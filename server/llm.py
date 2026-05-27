"""
LLM 服务模块 — 支持 OpenAI 兼容 API (OpenAI, DeepSeek, 通义千问, Ollama 等)
"""
import json
import logging
import os

import httpx

logger = logging.getLogger("bazi-pro.llm")

_LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
_LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
_LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "300"))


def is_llm_configured() -> bool:
    return bool(_LLM_API_KEY)


async def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=_LLM_TIMEOUT) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def chat_completion_stream(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
    if not _LLM_API_KEY:
        raise RuntimeError("LLM API key 未配置。请设置 LLM_API_KEY 环境变量。")

    url = f"{_LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=_LLM_TIMEOUT) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


def build_analysis_system_prompt(analysis_result: dict, narration: dict) -> str:
    validation = analysis_result.get("validation", {})
    strength = analysis_result.get("strength", {})
    pattern_info = analysis_result.get("pattern", {})
    yongshen_info = analysis_result.get("yongshen", {})
    elements = analysis_result.get("elements", {})
    relations = analysis_result.get("relations", [])
    tiaohou = analysis_result.get("tiaohou", {})
    shishen = analysis_result.get("shishen", {})

    day_master = validation.get("day_master", "")
    bazi = validation.get("bazi", "")
    gender = validation.get("gender", "")

    ws = strength.get("wangshuai", {})
    pattern = pattern_info.get("pattern", "")
    yongshen = yongshen_info.get("yongshen", "")
    xishen = yongshen_info.get("xishen", [])
    jishen = yongshen_info.get("jishen", [])

    pillars_info = ""
    for p in shishen.get("pillars", []):
        pos = p.get("position", "")
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        ss_gan = p.get("shishen_gan", "")
        ss_zhi = p.get("shishen_zhi", "")
        canggan = p.get("canggan", [])
        cg_str = " ".join(f"{c['gan']}({c.get('shishen','')})" for c in canggan)
        pillars_info += f"  {pos}: {gan}{zhi} 天干十神={ss_gan} 地支十神={ss_zhi} 藏干={cg_str}\n"

    relations_str = ""
    for r in relations:
        relations_str += f"  {r.get('type','')}: {r.get('description','')}\n"

    percent = elements.get("percent", {})
    elements_str = " ".join(f"{k}:{v:.1f}%" for k, v in sorted(percent.items(), key=lambda x: -x[1]))

    return f"""你是一位精通中国传统命理学的资深命理师，擅长子平八字、穷通宝鉴、滴天髓等多种流派。

## 命盘数据
- 八字: {bazi}
- 日主: {day_master}（{gender}命）
- 生肖: {validation.get('生肖', '')}

## 四柱详情
{pillars_info}

## 旺衰判定
- 得令: {strength.get('deling', {}).get('status', '')} (分数: {strength.get('deling', {}).get('score', 0)})
- 得地分数: {strength.get('dedi', {}).get('score', 0)}
- 得势分数: {strength.get('deshi', {}).get('score', 0)}
- 综合判定: {ws.get('verdict', '')}

## 格局
- 格局: {pattern} (第{pattern_info.get('layer', '?')}层, 置信度: {pattern_info.get('confidence', 0):.0%})
- 判定理由: {pattern_info.get('reason', '')}

## 喜用神
- 用神: {yongshen}
- 喜神: {'、'.join(xishen)}
- 忌神: {'、'.join(jishen)}

## 调候
- 调候用神: {'、'.join(tiaohou.get('tiaohou_gan', []))} ({'、'.join(tiaohou.get('tiaohou_wx', []))})

## 五行力量
{elements_str}

## 刑冲合害
{relations_str if relations_str else '无'}

## 确定性叙述
{json.dumps(narration, ensure_ascii=False, indent=2)}

---

你的任务是基于以上确定性计算数据，为命主提供深度、专业、有温度的命理解读。要求：
1. 所有论断必须基于上述数据，不得编造不存在的干支或十神关系
2. 引用古籍时需注明出处（如《滴天髓》《子平真诠》《穷通宝鉴》）
3. 分析要有深度，不能泛泛而谈，要结合具体干支关系
4. 语言风格：专业但易懂，像一位资深命理师在面对面解读
5. 涵盖：命局特征、性格分析、事业方向、感情婚姻、健康提示、流年建议
"""


def build_chat_system_prompt(analysis_result: dict, narration: dict) -> str:
    base = build_analysis_system_prompt(analysis_result, narration)
    return base + """

现在命主想要向你提问。请基于命盘数据回答，保持专业、有温度的风格。
如果问题超出命理范围，礼貌地引导回命理话题。
回答要具体、有针对性，引用命盘中的具体干支关系来支撑论断。
"""


def build_report_system_prompt(analysis_result: dict, narration: dict, dayun_data: list | None = None) -> str:
    validation = analysis_result.get("validation", {})
    strength = analysis_result.get("strength", {})
    pattern_info = analysis_result.get("pattern", {})
    yongshen_info = analysis_result.get("yongshen", {})
    elements = analysis_result.get("elements", {})
    relations = analysis_result.get("relations", [])
    tiaohou = analysis_result.get("tiaohou", {})
    shishen = analysis_result.get("shishen", {})
    disease = analysis_result.get("disease", {})

    day_master = validation.get("day_master", "")
    bazi = validation.get("bazi", "")
    gender = validation.get("gender", "")

    ws = strength.get("wangshuai", {})
    pattern = pattern_info.get("pattern", "")
    yongshen = yongshen_info.get("yongshen", "")
    xishen = yongshen_info.get("xishen", [])
    jishen = yongshen_info.get("jishen", [])

    pillars_info = ""
    for p in shishen.get("pillars", []):
        pos = p.get("position", "")
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        ss_gan = p.get("shishen_gan", "")
        ss_zhi = p.get("shishen_zhi", "")
        canggan = p.get("canggan", [])
        cg_str = " ".join(f"{c['gan']}({c.get('shishen','')})" for c in canggan)
        pillars_info += f"  {pos}: {gan}{zhi} 天干十神={ss_gan} 地支十神={ss_zhi} 藏干={cg_str}\n"

    relations_str = ""
    for r in relations:
        relations_str += f"  {r.get('type','')}: {r.get('description','')}\n"

    percent = elements.get("percent", {})
    elements_str = " ".join(f"{k}:{v:.1f}%" for k, v in sorted(percent.items(), key=lambda x: -x[1]))

    disease_str = ""
    if disease.get("has_disease"):
        for item in disease.get("items", []):
            disease_str += f"  {item.get('name','')}: {item.get('description','')}\n"

    dayun_str = ""
    if dayun_data:
        for dy in dayun_data:
            if isinstance(dy, dict):
                dayun_str += f"  {dy.get('age_range','')}: {dy.get('gan_zhi','')} {dy.get('description','')}\n"
            elif isinstance(dy, str):
                dayun_str += f"  {dy}\n"

    return f"""你是一位精通中国传统命理学的资深命理师，擅长子平八字、穷通宝鉴、滴天髓等多种流派。现在你需要为命主生成一份七维度综合分析报告。

## 命盘数据
- 八字: {bazi}
- 日主: {day_master}（{gender}命）
- 生肖: {validation.get('生肖', '')}

## 四柱详情
{pillars_info if pillars_info.strip() else '无'}

## 旺衰判定
- 得令: {strength.get('deling', {}).get('status', '')} (分数: {strength.get('deling', {}).get('score', 0)})
- 得地分数: {strength.get('dedi', {}).get('score', 0)}
- 得势分数: {strength.get('deshi', {}).get('score', 0)}
- 综合判定: {ws.get('verdict', '')}

## 格局
- 格局: {pattern} (第{pattern_info.get('layer', '?')}层, 置信度: {pattern_info.get('confidence', 0):.0%})
- 判定理由: {pattern_info.get('reason', '')}

## 喜用神
- 用神: {yongshen}
- 喜神: {'、'.join(xishen)}
- 忌神: {'、'.join(jishen)}

## 调候
- 调候用神: {'、'.join(tiaohou.get('tiaohou_gan', []))} ({'、'.join(tiaohou.get('tiaohou_wx', []))})

## 五行力量
{elements_str if elements_str.strip() else '无'}

## 刑冲合害
{relations_str if relations_str.strip() else '无'}

## 格局之病
{disease_str if disease_str.strip() else '无'}

## 大运列表
{dayun_str if dayun_str.strip() else '未提供大运数据'}

## 确定性叙述
{json.dumps(narration, ensure_ascii=False, indent=2)}

---

你的任务是基于以上确定性计算数据，生成一份七维度综合分析报告。你必须严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "overview": "命盘总论 - 格局+用神+旺衰综合论述，300-500字",
  "personality": "性格深度分析 - 十神组合+格局性格，300-500字",
  "career": "事业财运 - 行业方向+大运事业走势，300-500字",
  "marriage": "感情婚姻 - 日支分析+大运感情走势，300-500字",
  "health": "健康提醒 - 五行偏枯+大运健康风险，200-300字",
  "dayun_analysis": "大运流年详批 - 每步大运+关键流年，500-800字",
  "lucky": "开运建议 - 方位/颜色/数字/行业，200-300字"
}}
```

要求：
1. 所有论断必须基于上述数据，不得编造不存在的干支或十神关系
2. 引用古籍时需注明出处（如《滴天髓》《子平真诠》《穷通宝鉴》）
3. 分析要有深度，不能泛泛而谈，要结合具体干支关系
4. 语言风格：专业但易懂，像一位资深命理师在面对面解读
5. 每个维度的字数必须严格控制在指定范围内
6. 只输出 JSON，不要输出任何其他文字
7. 如果大运数据未提供，在 dayun_analysis 中说明"大运数据未提供，无法详批"，并基于原局做趋势分析
"""
