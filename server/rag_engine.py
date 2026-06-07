"""
server/rag_engine.py
问题感知古籍检索引擎 (Question-Aware RAG Engine)

根据用户问题分类，动态构造检索查询，调用 bazi_pro.retrieve_classical
进行 BM25 古籍检索，并格式化为 LLM prompt 可用的引用块。
"""

from __future__ import annotations

import logging
import os
from typing import Any

from bazi_pro.retrieve_classical import retrieve

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. 问题分类体系
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "marriage": [
        "婚姻", "结婚", "离婚", "配偶", "夫妻", "感情", "桃花", "正缘", "孽缘",
        "嫁", "娶", "婚恋", "情", "对象", "另一半", "男朋友", "女朋友", "老公", "老婆",
    ],
    "career": [
        "事业", "工作", "职业", "升职", "跳槽", "创业", "官运", "仕途", "领导",
        "老板", "职场", "官", "权力", "职位", "岗位", "行业", "生意", "项目",
    ],
    "health": [
        "健康", "病", "身体", "疾", "寿", "体质", "手术", "医院", "养生",
        "脏腑", "虚弱", "调理", "痛", "伤", "精神", "睡眠", "饮食",
    ],
    "wealth": [
        "财", "钱", "富", "收入", "投资", "理财", "资产", "负债", "盈利",
        "亏损", "薪资", "奖金", "股票", "基金", "房", "车", "经济", "现金流",
    ],
    "study": [
        "学业", "学习", "考试", "升学", "文凭", "学历", "学校", "考", "成绩",
        "科举", "文昌", "智慧", "聪明", "证书", "资格", "考研", "留学", "进修",
    ],
    "interpersonal": [
        "人际", "关系", "交友", "贵人", "小人", "同事", "朋友", "亲戚",
        "兄弟", "姐妹", "合作", "合伙", "社交", "人脉", "圈子", "冲突", "矛盾",
    ],
    "general": [
        "运势", "命", "八字", "运程", "流年", "大运", "整体", "综合", "怎样",
        "如何", "好不好", "建议", "指点", "看看", "分析", "解读", "预测", "未来",
    ],
}

# 反向映射：category -> 中文标签
CATEGORY_LABELS: dict[str, str] = {
    "marriage": "婚姻感情",
    "career": "事业官运",
    "health": "健康寿元",
    "wealth": "财富财运",
    "study": "学业考试",
    "interpersonal": "人际关系",
    "general": "综合运势",
}

# ---------------------------------------------------------------------------
# 2. 各类别检索查询模板
# ---------------------------------------------------------------------------

# 模板占位符说明：
#   {question}   — 用户原始问题
#   {category}   — 类别中文标签
#   {pattern}    — 格局名称（如 analysis_context["pattern"]["name"]）
#   {day_master} — 日主天干（如 analysis_context["day_master"]）
#   {yongshen}   — 用神（如 analysis_context["yongshen"]["yongshen"]）
#   {wangshuai}  — 旺衰判定（如 analysis_context["wangshuai"]["verdict"]）

RETRIEVAL_TEMPLATES: dict[str, list[str]] = {
    "marriage": [
        "{day_master}日柱 {pattern} 婚姻配偶 夫妻宫",
        "{wangshuai} {yongshen} 桃花 正缘 感情",
        "男命财星 女命官星 婚姻 配偶",
        "刑冲合害 夫妻宫 婚姻 感情",
        "{question} 婚姻 配偶 感情",
    ],
    "career": [
        "{day_master}日柱 {pattern} 事业 官运 仕途",
        "{wangshuai} {yongshen} 官杀 印星 事业",
        "格局 用神 事业 职业 行业",
        "大运 流年 升职 创业 工作",
        "{question} 事业 职业 官运",
    ],
    "health": [
        "{day_master}日柱 {pattern} 健康 疾病 脏腑",
        "{wangshuai} 五行 偏弱 健康 体质",
        "刑冲 克害 健康 伤病 寿元",
        "调候 用神 健康 养生 脏腑",
        "{question} 健康 身体 疾病",
    ],
    "wealth": [
        "{day_master}日柱 {pattern} 财运 财富 财星",
        "{wangshuai} {yongshen} 财星 财运 富",
        "格局 用神 财 富 贫",
        "大运 流年 财 投资 收入",
        "{question} 财运 财富 金钱",
    ],
    "study": [
        "{day_master}日柱 {pattern} 学业 文昌 智慧",
        "{wangshuai} 印星 食伤 学业 考试",
        "文昌 学堂 功名 科举 考试",
        "大运 流年 升学 考试 成绩",
        "{question} 学业 考试 学习",
    ],
    "interpersonal": [
        "{day_master}日柱 {pattern} 人际 贵人 小人",
        "{wangshuai} {yongshen} 比劫 食伤 人际",
        "天乙贵人 文昌 桃花 人际 关系",
        "刑冲 合害 人际 冲突 合作",
        "{question} 人际 关系 朋友",
    ],
    "general": [
        "{day_master}日柱 {pattern} 运势 命 运程",
        "{wangshuai} {yongshen} 格局 大运 流年",
        "调候 用神 喜忌 整体 运势",
        "格局 旺衰 大运 流年 吉凶",
        "{question} 八字 运势 命运",
    ],
}

# ---------------------------------------------------------------------------
# 3. 报告章节 -> 检索类别映射
# ---------------------------------------------------------------------------

CHAPTER_TO_CATEGORY: dict[str, str] = {
    "wangshuai": "general",
    "pattern": "general",
    "yongshen": "general",
    "tiaohou": "general",
    "wuxing": "health",
    "relations": "interpersonal",
    "personality": "general",
    "career": "career",
    "wealth": "wealth",
    "marriage": "marriage",
    "health": "health",
    "study": "study",
    "dayun": "general",
    "liunian": "general",
    "summary": "general",
}

# ---------------------------------------------------------------------------
# 4. 问题分类
# ---------------------------------------------------------------------------


def _classify_question(question: str) -> str:
    """根据关键词匹配对用户问题进行分类。

    匹配规则：
    - 遍历每个类别的关键词列表，统计命中次数
    - 返回命中次数最多的类别；若全部未命中，返回 'general'
    """
    if not question or not isinstance(question, str):
        return "general"

    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question)
        scores[category] = score

    best = max(scores, key=lambda c: scores[c])
    if scores[best] == 0:
        return "general"
    return best


# ---------------------------------------------------------------------------
# 5. 检索查询构造
# ---------------------------------------------------------------------------


def _extract_context_value(analysis_context: dict, key_path: str, default: str = "") -> str:
    """按点号分隔的路径从嵌套字典中安全取值。"""
    if not analysis_context or not isinstance(analysis_context, dict):
        return default
    keys = key_path.split(".")
    val: Any = analysis_context
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    if val is None:
        return default
    return str(val)


def _build_retrieval_query(question: str, category: str, analysis_context: dict) -> str:
    """基于问题类别和分析上下文，构造精确检索查询字符串。

    逻辑：
    1. 从 analysis_context 提取 day_master、pattern、wangshuai、yongshen
    2. 选取对应类别的前两条模板进行格式化，合并为更丰富的查询
    3. 若格式化失败，回退到 "{question} {category_label}"
    """
    category = category if category in RETRIEVAL_TEMPLATES else "general"
    templates = RETRIEVAL_TEMPLATES[category]

    day_master = _extract_context_value(analysis_context, "day_master", "")
    pattern = _extract_context_value(analysis_context, "pattern.pattern", "")
    wangshuai = _extract_context_value(analysis_context, "wangshuai.verdict", "")
    yongshen = _extract_context_value(analysis_context, "yongshen.yongshen", "")
    category_label = CATEGORY_LABELS.get(category, "综合运势")

    fmt_kwargs = dict(
        question=question,
        category=category_label,
        day_master=day_master,
        pattern=pattern,
        wangshuai=wangshuai,
        yongshen=yongshen,
    )

    parts = []
    for tmpl in templates[:2]:
        try:
            parts.append(tmpl.format(**fmt_kwargs))
        except (KeyError, ValueError):
            continue

    if not parts:
        parts.append(f"{question} {category_label}")

    query = " ".join(parts)
    query = " ".join(query.split())
    return query


# ---------------------------------------------------------------------------
# 6. 核心检索接口
# ---------------------------------------------------------------------------


def _resolve_corpus_path() -> str:
    """安全解析语料库路径，不依赖私有函数。"""
    try:
        from bazi_pro.retrieve_classical import _resolve_corpus
        return _resolve_corpus()
    except ImportError:
        pass
    # 降级：手动查找
    try:
        from importlib.resources import files
        data_dir = files("bazi_pro.data")
        corpus = data_dir.joinpath("classical_corpus.md")
        if corpus.is_file():
            return str(corpus)
    except Exception:
        pass
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.join(script_dir, "..", "bazi_pro", "data", "classical_corpus.md"),
        os.path.join(script_dir, "..", "references", "classical_corpus.md"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return os.path.join(script_dir, "..", "bazi_pro", "data", "classical_corpus.md")


def retrieve_for_chat(question: str, analysis_context: dict, k: int = 5) -> dict:
    """为聊天场景检索古籍依据。

    流程：
    1. 分类用户问题
    2. 构造检索查询
    3. 调用 bazi_pro.retrieve_classical.retrieve()
    4. 返回结构化结果（含 category、query、results、counter_evidence）

    错误处理：若检索失败，返回空结果，不抛异常。
    """
    category = _classify_question(question)
    query = _build_retrieval_query(question, category, analysis_context)
    corpus_path = _resolve_corpus_path()

    try:
        raw = retrieve(corpus_path, query, k=k)
    except Exception as exc:
        logger.warning("retrieve_for_chat failed: %s", exc)
        return {
            "category": category,
            "query": query,
            "results": [],
            "counter_evidence": [],
            "error": str(exc),
        }

    return {
        "category": category,
        "query": query,
        "results": raw.get("results", []),
        "counter_evidence": raw.get("counter_evidence", []),
        "latency_ms": raw.get("latency_ms", 0),
        "cache": raw.get("cache", "unknown"),
        "corpus_size": raw.get("corpus_size", 0),
    }


def retrieve_for_report(chapter_key: str, analysis_context: dict, k: int = 5) -> dict:
    """为报告生成场景检索古籍依据。

    流程：
    1. 将 chapter_key 映射到检索类别
    2. 构造检索查询（chapter_key 作为问题占位符）
    3. 调用 retrieve()
    4. 返回结构化结果

    错误处理：若检索失败，返回空结果，不抛异常。
    """
    category = CHAPTER_TO_CATEGORY.get(chapter_key, "general")
    # 报告章节检索：直接构造 query，不走 _build_retrieval_query（避免 pseudo_question 被模板二次拼接）
    day_master = _extract_context_value(analysis_context, "day_master", "")
    pattern = _extract_context_value(analysis_context, "pattern.pattern", "")
    category_label = CATEGORY_LABELS.get(category, "综合运势")
    query = f"{day_master}日柱 {pattern} {category_label}" if day_master else f"{pattern} {category_label}"
    query = " ".join(query.split())  # 清理多余空格
    corpus_path = _resolve_corpus_path()

    try:
        raw = retrieve(corpus_path, query, k=k)
    except Exception as exc:
        logger.warning("retrieve_for_report failed: %s", exc)
        return {
            "chapter_key": chapter_key,
            "category": category,
            "query": query,
            "results": [],
            "counter_evidence": [],
            "error": str(exc),
        }

    return {
        "chapter_key": chapter_key,
        "category": category,
        "query": query,
        "results": raw.get("results", []),
        "counter_evidence": raw.get("counter_evidence", []),
        "latency_ms": raw.get("latency_ms", 0),
        "cache": raw.get("cache", "unknown"),
        "corpus_size": raw.get("corpus_size", 0),
        "corpus_path": corpus_path,
    }


# ---------------------------------------------------------------------------
# 7. 结果格式化
# ---------------------------------------------------------------------------


def _format_retrieval_for_prompt(results: dict, max_entries: int = 5) -> str:
    """将检索结果格式化为 prompt 友好的引用块。

    输入：retrieve_for_chat / retrieve_for_report 返回的 dict
    输出：可直接拼入 system prompt 的字符串，包含古籍引用和反证。
    """
    if not results or not isinstance(results, dict):
        return "（无古籍检索结果）"

    entries = results.get("results", [])
    if not entries:
        return "（无古籍检索结果）"

    lines: list[str] = []
    lines.append("【古籍依据】")

    count = 0
    for entry in entries[:max_entries]:
        count += 1
        source = entry.get("source", "未知")
        topic = entry.get("topic", "")
        content = entry.get("content", "")
        score = entry.get("score", 0.0)
        eid = entry.get("id", "")
        lines.append(
            f"[{count}] 《{source}》@{topic} (id={eid}, score={score:.4f})\n    {content}"
        )

    counter = results.get("counter_evidence", [])
    if counter:
        lines.append("")
        lines.append("【反证/对立观点】")
        for c_entry in counter[:3]:
            c_source = c_entry.get("source", "未知")
            c_topic = c_entry.get("topic", "")
            c_content = c_entry.get("content", "")
            c_score = c_entry.get("score", 0.0)
            lines.append(
                f"- 《{c_source}》@{c_topic} (score={c_score:.4f})\n  {c_content}"
            )

    return "\n".join(lines)
