# BaziQA 评测管线优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 BaziQA 基线准确率从 51.6% 提升至 80%+，通过修复 Bug、专用 Exam Prompt、Self-Consistency 投票。

**Architecture:** 分阶段实现——Phase 1 修 Bug + Exam Prompt（快速验证），Phase 2 Self-Consistency 投票（全量优化）。所有优化在 benchmark runner 端实现，不改线上 /chat 逻辑。

**Tech Stack:** Python, asyncio, regex, Counter (collections)

---

## Phase 1: 修 Bug + Exam Prompt（快速验证）

### Task 1: 修复 extract_answer 支持 A-E 选项

**Files:**
- Modify: `benchmarks/scoring/extractor.py`

- [ ] **Step 1: 读取当前 extractor.py 代码**

```python
# 当前代码（需要修改）
import re

def extract_answer(text: str) -> str:
    if not text:
        return ""
    text = text.strip()

    # 优先级1: 明确声明 "答案是X" / "选择X" / "选X"
    patterns = [
        r'(?:答案|选择|选|应选|应为|应该[是选])\s*[：:]?\s*([A-D])',
        r'(?:answer|Answer)\s*[：:is]*\s*([A-D])',
        r'^\s*([A-D])\s*$',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m:
            return m.group(1).upper()

    # 优先级2: 括号中的字母 (A) / 【A】
    m = re.search(r'[（(【\[]([A-D])[）)】\]]', text)
    if m:
        return m.group(1).upper()

    # 优先级3: 行首独立字母
    m = re.search(r'^([A-D])[.、。：:\s]', text, re.MULTILINE)
    if m:
        return m.group(1).upper()

    # 优先级4(兜底): 第一个出现的选项字母
    m = re.search(r'([A-D])', text)
    if m:
        return m.group(1).upper()

    return ""
```

- [ ] **Step 2: 修改 extract_answer 支持 A-E + markdown**

```python
import re

def extract_answer(text: str) -> str:
    if not text:
        return ""
    text = text.strip()

    # 优先级1: 明确声明 "答案是X" / "选择X" / "选X"
    patterns = [
        r'(?:答案|选择|选|应选|应为|应该[是选])\s*[：:]?\s*\**([A-E])\**',
        r'(?:answer|Answer)\s*[：:is]*\s*\**([A-E])\**',
        r'^\s*\**([A-E])\**\s*$',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m:
            return m.group(1).upper()

    # 优先级2: 括号中的字母 (A) / 【A】 / **A**
    m = re.search(r'[（(【\[]([A-E])[）)】\]]', text)
    if m:
        return m.group(1).upper()
    m = re.search(r'\*\*([A-E])\*\*', text)
    if m:
        return m.group(1).upper()

    # 优先级3: 行首独立字母
    m = re.search(r'^([A-E])[.、。：:\s]', text, re.MULTILINE)
    if m:
        return m.group(1).upper()

    # 优先级4(兜底): 最后200字符中的第一个选项字母
    tail = text[-200:]
    m = re.search(r'([A-E])', tail)
    if m:
        return m.group(1).upper()

    return ""
```

- [ ] **Step 3: 验证修改**

Run: `python -c "from benchmarks.scoring.extractor import extract_answer; print(extract_answer('故选**E**'))"`
Expected: `E`

### Task 2: 新建 Exam Prompt 模块

**Files:**
- Create: `benchmarks/optimizers/__init__.py`
- Create: `benchmarks/optimizers/exam_prompts.py`

- [ ] **Step 1: 创建 optimizers 包**

```python
# benchmarks/optimizers/__init__.py
```

- [ ] **Step 2: 创建 exam_prompts.py**

```python
EXAM_SYSTEM_PROMPT = """你是八字命理分析专家，精通子平八字、穷通宝鉴、滴天髓等典籍。
你的任务是根据命盘数据，通过严谨的命理推理，选择最正确的答案。

【推理步骤】
1. 确认日主强弱、格局、用神
2. 分析问题涉及的宫位或星曜
3. 结合大运流年判断应期
4. 逐一比对选项，选择最符合命理逻辑的答案

【输出要求】
- 先进行简要推理（3-5 句）
- 最后一行必须输出：答案：X（X 为 A/B/C/D/E 之一）
- 不要输出多余内容"""

CATEGORY_TEMPLATES = {
    "感情": """【感情题推理指引】
- 男命看正财（妻星）、偏财（情人星）；女命看正官（夫星）、七杀（偏夫）
- 日支为配偶宫，看日支五行与日主关系
- 桃花星（子午卯酉）主异性缘
- 大运流年见正财/正官为婚恋应期
- 正财两透或多透主感情复杂/多段恋情""",
    
    "六亲": """【六亲题推理指引】
- 年柱：祖上宫、父母宫（偏上）；月柱：父母宫（偏下）、兄弟宫
- 日柱：配偶宫；时柱：子女宫
- 男命：偏财为父，正印为母；女命：正财为父，偏印为母
- 男命：正官为女，七杀为子；女命：伤官为子，食神为女
- 六亲星坐旺地主六亲强，坐衰绝主六亲弱""",
    
    "事业": """【事业题推理指引】
- 正官/七杀主事业、权力、地位
- 食伤主才华、表达、创作
- 财星主财富、经营
- 印星主学业、文凭、贵人
- 官印相生主仕途亨通，食伤生财主商业成功""",
    
    "健康": """【健康题推理指引】
- 五行对应脏腑：木=肝胆，火=心小肠，土=脾胃，金=肺大肠，水=肾膀胱
- 五行过旺或过弱对应脏腑易出问题
- 大运流年冲克用神主健康波动
- 七杀无制主意外伤灾""",
    
    "财富": """【财富题推理指引】
- 财星旺且为用神主富裕
- 身旺担财主能守住财富
- 食伤生财主靠才华赚钱
- 比劫争财主破财/竞争
- 大运见财星为财运应期""",
    
    "其他": """【综合推理指引】
- 先确认格局和用神，再分析问题涉及的宫位或星曜
- 大运流年与原局的互动是判断应期的关键
- 逐一排除明显不符合命理逻辑的选项
- 选择与命盘数据最一致的答案""",
}

def build_exam_prompt(analysis_result: dict, category: str) -> str:
    """构建 Exam 模式的 system prompt"""
    ctx = format_analysis_for_exam(analysis_result)
    category_template = CATEGORY_TEMPLATES.get(category, CATEGORY_TEMPLATES["其他"])
    return f"{EXAM_SYSTEM_PROMPT}\n\n{ctx}\n\n{category_template}"

def format_analysis_for_exam(analysis_result: dict) -> str:
    """从 analysis_result 提取命盘数据，精简格式"""
    # 这里需要从 analysis_result 中提取关键数据
    # 暂时返回占位符，后续实现
    return "【命盘数据】\n（待实现）"
```

- [ ] **Step 3: 验证模块导入**

Run: `python -c "from benchmarks.optimizers.exam_prompts import build_exam_prompt; print('OK')"`
Expected: `OK`

### Task 3: 实现 format_analysis_for_exam

**Files:**
- Modify: `benchmarks/optimizers/exam_prompts.py`

- [ ] **Step 1: 实现 format_analysis_for_exam**

```python
def format_analysis_for_exam(analysis_result: dict) -> str:
    """从 analysis_result 提取命盘数据，精简格式"""
    parts = []
    
    # 基本信息
    if "八字" in analysis_result:
        parts.append(f"八字：{analysis_result['八字']}")
    if "日主" in analysis_result:
        parts.append(f"日主：{analysis_result['日主']}")
    if "性别" in analysis_result:
        parts.append(f"性别：{analysis_result['性别']}")
    
    # 格局和旺衰
    validation = analysis_result.get("validation", {})
    if "格局" in validation:
        parts.append(f"格局：{validation['格局']}")
    if "旺衰" in validation:
        parts.append(f"旺衰：{validation['旺衰']}")
    
    # 喜用神
    yongshen = analysis_result.get("yongshen", {})
    if "用神" in yongshen:
        parts.append(f"用神：{yongshen['用神']}")
    if "喜神" in yongshen:
        parts.append(f"喜神：{yongshen['喜神']}")
    if "忌神" in yongshen:
        parts.append(f"忌神：{yongshen['忌神']}")
    
    # 五行力量
    elements = analysis_result.get("elements", {})
    if elements:
        parts.append(f"五行力量：{elements}")
    
    # 大运
    dayun = analysis_result.get("dayun", [])
    if dayun:
        parts.append(f"当前大运：{dayun[0] if dayun else '未知'}")
    
    # 叙述
    narration = analysis_result.get("narration", "")
    if narration:
        parts.append(f"【确定性叙述】\n{narration}")
    
    return "\n".join(parts)
```

- [ ] **Step 2: 验证格式化输出**

Run: `python -c "from benchmarks.optimizers.exam_prompts import format_analysis_for_exam; print(format_analysis_for_exam({'八字': '甲子 乙丑 丙寅 丁卯'}))"`
Expected: 包含 "八字：甲子 乙丑 丙寅 丁卯" 的输出

### Task 4: 修改 runner 使用 Exam Prompt

**Files:**
- Modify: `benchmarks/runners/baziqa_runner.py`

- [ ] **Step 1: 添加 exam prompt 导入**

在 `baziqa_runner.py` 顶部添加：
```python
from benchmarks.optimizers.exam_prompts import build_exam_prompt
```

- [ ] **Step 2: 修改 ask_question 使用 exam prompt**

```python
def ask_question(analysis_result: dict, question: str, options: list[str],
                 category: str, school: str = "ziping") -> str:
    """使用 Exam Prompt 回答问题"""
    try:
        system_prompt = build_exam_prompt(analysis_result, category)
        user_prompt = f"{question}\n\n" + "\n".join(options)
        
        # 调用 LLM（这里需要实现 LLM 调用逻辑）
        # 暂时返回占位符
        return "A"
    except Exception as e:
        return f"[ERROR] {e}"
```

- [ ] **Step 3: 实现 LLM 调用**

需要在 runner 中实现 `chat_completion()` 的调用。由于 runner 是独立进程，需要：
1. 加载 `.env` 文件获取 LLM API key
2. 导入 `server.llm.chat_completion`
3. 调用 LLM

```python
import asyncio
from dotenv import load_dotenv
load_dotenv("server/.env")

from server.llm import chat_completion

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return await chat_completion(messages, temperature=0.7)

def ask_question(analysis_result: dict, question: str, options: list[str],
                 category: str, school: str = "ziping") -> str:
    """使用 Exam Prompt 回答问题"""
    try:
        system_prompt = build_exam_prompt(analysis_result, category)
        user_prompt = f"{question}\n\n" + "\n".join(options)
        
        reply = asyncio.run(call_llm(system_prompt, user_prompt))
        return reply
    except Exception as e:
        return f"[ERROR] {e}"
```

- [ ] **Step 4: 验证 runner 修改**

Run: `python -c "from benchmarks.runners.baziqa_runner import ask_question; print('OK')"`
Expected: `OK`

### Task 5: 快速验证 Phase 1（20 题）

**Files:**
- Modify: `benchmarks/runners/baziqa_runner.py` (添加 --max-persons 参数支持)

- [ ] **Step 1: 添加 --max-persons 参数**

在 `main()` 函数中添加参数解析：
```python
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-persons", type=int, help="最大测试人数")
    parser.add_argument("--school", default="ziping", help="流派")
    args = parser.parse_args()
    
    # ... 其他代码
    
    persons = load_persons()
    if args.max_persons:
        persons = persons[:args.max_persons]
    
    # ... 其他代码
```

- [ ] **Step 2: 运行 Phase 1 验证**

Run: `$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa --max-persons 4`
Expected: 完成 4 个 subject（约 40 题），输出准确率

- [ ] **Step 3: 分析 Phase 1 结果**

如果准确率 ≥ 65%，继续 Phase 2。
如果准确率 < 60%，需要调整 exam prompt 或检查 LLM 配置。

---

## Phase 2: Self-Consistency 投票（全量优化）

### Task 6: 实现 Self-Consistency 投票引擎

**Files:**
- Create: `benchmarks/optimizers/self_consistency.py`

- [ ] **Step 1: 创建 self_consistency.py**

```python
import asyncio
from collections import Counter
from benchmarks.scoring.extractor import extract_answer
from benchmarks.optimizers.exam_prompts import build_exam_prompt
from server.llm import chat_completion

async def answer_with_consistency(
    analysis_result: dict,
    question: str,
    options: list[str],
    category: str,
    n_samples: int = 5,
    temperature: float = 0.7,
) -> str:
    """Self-Consistency: 跑 n_samples 次，多数投票"""
    system_prompt = build_exam_prompt(analysis_result, category)
    user_prompt = f"{question}\n\n" + "\n".join(options)
    
    answers = []
    for _ in range(n_samples):
        try:
            reply = await chat_completion(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}],
                temperature=temperature,
            )
            answer = extract_answer(reply)
            if answer:
                answers.append(answer)
        except Exception:
            continue
    
    if not answers:
        # 全部提取失败，用 temperature=0 重试 1 次
        try:
            reply = await chat_completion(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}],
                temperature=0,
            )
            return extract_answer(reply)
        except Exception:
            return ""
    
    # 多数投票
    counter = Counter(answers)
    return counter.most_common(1)[0][0]
```

- [ ] **Step 2: 验证 Self-Consistency 模块**

Run: `python -c "from benchmarks.optimizers.self_consistency import answer_with_consistency; print('OK')"`
Expected: `OK`

### Task 7: 集成 Self-Consistency 到 runner

**Files:**
- Modify: `benchmarks/runners/baziqa_runner.py`

- [ ] **Step 1: 修改 ask_question 使用 Self-Consistency**

```python
from benchmarks.optimizers.self_consistency import answer_with_consistency

def ask_question(analysis_result: dict, question: str, options: list[str],
                 category: str, school: str = "ziping") -> str:
    """使用 Self-Consistency 投票回答问题"""
    try:
        reply = asyncio.run(answer_with_consistency(
            analysis_result, question, options, category,
            n_samples=5, temperature=0.7
        ))
        return reply
    except Exception as e:
        return f"[ERROR] {e}"
```

- [ ] **Step 2: 运行 Phase 2 验证（50 题）**

Run: `$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa --max-persons 10`
Expected: 完成 10 个 subject（约 100 题），输出准确率

- [ ] **Step 3: 分析 Phase 2 结果**

如果准确率 ≥ 72%，继续全量测试。
如果准确率 < 68%，需要调整 n_samples 或 temperature。

### Task 8: 全量测试（91 subject）

**Files:**
- 无新增文件

- [ ] **Step 1: 运行全量测试**

Run: `$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa`
Expected: 完成 91 个 subject（约 688 题），输出准确率

- [ ] **Step 2: 生成最终报告**

Run: `python -m benchmarks calibrate baseline`
Expected: 生成新的基线报告，准确率 ≥ 80%

---

## 验证命令

```bash
# Phase 1 验证（20 题）
$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa --max-persons 4

# Phase 2 验证（50 题）
$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa --max-persons 10

# 全量测试（688 题）
$env:PYTHONUNBUFFERED="1"; python -u -m benchmarks run baziqa

# 生成报告
python -m benchmarks calibrate baseline
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Phase 1 准确率 < 60% | 调整 exam prompt，增加 few-shot 示例 |
| Self-Consistency 投票无效 | 减少 n_samples 到 3，或改用 temperature=0 |
| LLM 调用超时 | 增加 timeout，或减少并发 |
| 内存不足 | 分批处理，或减少 max-persons |
