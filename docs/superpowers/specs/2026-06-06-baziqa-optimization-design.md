# BaziQA 评测管线优化设计

## 目标

将 BaziQA 基线准确率从 **51.6%** 提升至 **80%+**，通过三阶段优化：修复基础 Bug、专用 Exam Prompt、Self-Consistency 投票。

## 当前基线

| 指标 | 数值 |
|------|------|
| 总题数 | 688 |
| 正确数 | 355 |
| 准确率 | 51.6% |
| 错误数 | 333（其中 35 题提取为空） |

### 分类准确率

| 分类 | 题数 | 准确率 | 瓶颈分析 |
|------|------|--------|----------|
| 健康 | 96 | 60.4% | 相对最强，五行缺失→疾病映射较明确 |
| 财富 | 52 | 59.6% | 财星分析逻辑清晰 |
| 事业 | 129 | 58.9% | 官杀/食伤分析覆盖较好 |
| 其他 | 251 | 49.8% | 混合分类，LLM 推理路径不明确 |
| 感情 | 107 | 41.1% | 最弱之一，配偶宫/配偶星推理链缺失 |
| 六亲 | 53 | 39.6% | 最弱，六亲宫位映射复杂 |

## 根因分析

### 问题 1：extract_answer 不支持 E 选项（影响 ~5%）
`benchmarks/scoring/extractor.py` 硬编码 `[A-D]`，数据集有 5 选项题（A-E）。正确答案为 E 时提取失败。

### 问题 2：35 题提取为空（影响 ~5%）
- 6 题被 LLM 安全过滤器拦截
- 29 题 LLM 回复长篇分析但无明确选项字母

### 问题 3：System Prompt 与任务严重不匹配（最大瓶颈，影响 ~15%）
当前 `build_chat_system_prompt()` 为开放式聊天设计，"老夫"角色设定 + 古籍引用格式 + 4 步节奏模板占 4000-6000 tokens，挤压推理空间。

### 问题 4：RAG 检索不完整（影响 ~3%）
`_build_retrieval_query()` 只用 templates[0]，其余 4 条模板被丢弃。

### 问题 5：缺少分类专用推理链（影响 ~5%）
LLM 没有被引导按问题分类做结构化推理（感情题→配偶宫分析、六亲题→六亲宫位分析）。

## 优化方案

### 总体架构

```
当前:  问题 → 命盘数据 + 角色扮演 prompt → LLM → extract_answer → 评分

优化后:
  问题 → 命盘数据（确定性分析） → Exam Prompt + 分类推理模板
       → LLM × 5 次（Self-Consistency）
       → 多数投票 → extract_answer → 评分
```

关键原则：**不改线上 /chat 逻辑**，所有优化在 benchmark runner 端实现。

### Stage 0：基础层修复

#### 0.1 extract_answer 增强
文件：`benchmarks/scoring/extractor.py`

修改内容：
- 所有 `[A-D]` 正则扩展为 `[A-E]`
- 新增 markdown 加粗模式：`\*\*([A-E])\*\*`
- 新增"故选"模式：`故\s*选\s*\**([A-E])\*\*`
- 缩小兜底匹配范围：只匹配最后 200 字符中的选项字母

#### 0.2 安全拒绝重试
文件：`benchmarks/runners/baziqa_runner.py`

在 `ask_question()` 中检测 `"request was rejected"` 或空答案时，用中性措辞重试 1 次。

#### 0.3 Dynamic RAG 增强
文件：`server/rag_engine.py`

修改 `_build_retrieval_query()`：
- 对所有 5 条模板执行检索
- 合并结果，按 score 降序去重，取 top-8
- 根据问题分类自动扩展关键词

### Stage 1：专用 Exam Prompt

#### 1.1 Exam System Prompt
新建 `benchmarks/optimizers/exam_prompts.py`

核心 system prompt（去掉所有角色扮演，聚焦推理）：

```
你是八字命理分析专家，精通子平八字、穷通宝鉴、滴天髓等典籍。
你的任务是根据命盘数据，通过严谨的命理推理，选择最正确的答案。

【推理步骤】
1. 确认日主强弱、格局、用神
2. 分析问题涉及的宫位或星曜
3. 结合大运流年判断应期
4. 逐一比对选项，选择最符合命理逻辑的答案

【输出要求】
- 先进行简要推理（3-5 句）
- 最后一行必须输出：答案：X（X 为 A/B/C/D/E 之一）
- 不要输出多余内容
```

#### 1.2 分类推理模板
为 6 个分类各定义一个专用推理模板，注入 system prompt：

**感情题**：
```
【感情题推理指引】
- 男命看正财（妻星）、偏财（情人星）；女命看正官（夫星）、七杀（偏夫）
- 日支为配偶宫，看日支五行与日主关系
- 桃花星（子午卯酉）主异性缘
- 大运流年见正财/正官为婚恋应期
- 正财两透或多透主感情复杂/多段恋情
```

**六亲题**：
```
【六亲题推理指引】
- 年柱：祖上宫、父母宫（偏上）；月柱：父母宫（偏下）、兄弟宫
- 日柱：配偶宫；时柱：子女宫
- 男命：偏财为父，正印为母；女命：正财为父，偏印为母
- 男命：正官为女，七杀为子；女命：伤官为子，食神为女
- 六亲星坐旺地主六亲强，坐衰绝主六亲弱
```

**事业题**：
```
【事业题推理指引】
- 正官/七杀主事业、权力、地位
- 食伤主才华、表达、创作
- 财星主财富、经营
- 印星主学业、文凭、贵人
- 官印相生主仕途亨通，食伤生财主商业成功
```

**健康题**：
```
【健康题推理指引】
- 五行对应脏腑：木=肝胆，火=心小肠，土=脾胃，金=肺大肠，水=肾膀胱
- 五行过旺或过弱对应脏腑易出问题
- 大运流年冲克用神主健康波动
- 七杀无制主意外伤灾
```

**财富题**：
```
【财富题推理指引】
- 财星旺且为用神主富裕
- 身旺担财主能守住财富
- 食伤生财主靠才华赚钱
- 比劫争财主破财/竞争
- 大运见财星为财运应期
```

**其他题**（兜底模板，覆盖不在上述 5 类中的问题）：
```
【综合推理指引】
- 先确认格局和用神，再分析问题涉及的宫位或星曜
- 大运流年与原局的互动是判断应期的关键
- 逐一排除明显不符合命理逻辑的选项
- 选择与命盘数据最一致的答案
```

### Stage 2：Self-Consistency 投票

新建 `benchmarks/optimizers/self_consistency.py`

#### 2.1 投票机制

```python
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
        reply = await chat_completion(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        answer = extract_answer(reply)
        if answer:
            answers.append(answer)

    if not answers:
        # 全部提取失败，用 temperature=0 重试 1 次
        reply = await chat_completion(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0,
        )
        return extract_answer(reply)

    # 多数投票
    counter = Counter(answers)
    return counter.most_common(1)[0][0]
```

#### 2.2 命盘数据注入

从 `run_analysis()` 的 result dict 中提取结构化数据，注入 exam prompt：

```python
def build_exam_prompt(analysis_result: dict, category: str) -> str:
    ctx = format_analysis_for_exam(analysis_result)
    category_template = CATEGORY_TEMPLATES.get(category, "")
    return f"{EXAM_SYSTEM_PROMPT}\n\n{ctx}\n\n{category_template}"
```

`format_analysis_for_exam()` 从 analysis_result 提取：
- 四柱详情（干支、藏干、十神）
- 旺衰判定（得令/得地/得势/综合）
- 格局信息（名称、层次、置信度）
- 喜用神（用神/喜神/忌神）
- 调候用神
- 五行力量百分比
- 刑冲合害
- 神煞
- 大运列表（含当前大运）
- 确定性叙述（narrator 输出）

比当前的 `_format_analysis_context()` 更精简，去掉冗余的格式化开销。

### Stage 3：Runner 集成

修改 `benchmarks/runners/baziqa_runner.py`：

Runner 的 `ask_question()` 需要接收 `options` 和 `category` 参数。
当前 runner 只传 `analysis_id` + `question` + `school`，需要扩展为传入完整的题目信息。

`category` 来源：BaziQA 数据集中每个 question 所属的 person 的 `categories` 字典的 key。
Runner 在加载数据时，从 `person["categories"]` 中根据 question_id 所属的 category 维度确定分类。

Self-Consistency 的 `chat_completion()` 是 async 函数，runner 的 `ask_question()` 是 sync 函数。
使用 `asyncio.run()` 桥接，或在 runner 主循环中改用 `asyncio` 驱动。

```python
def ask_question(analysis_result: dict, question: str, options: list[str],
                 category: str) -> str:
    """Self-Consistency 投票回答（sync 入口）"""
    import asyncio
    return asyncio.run(answer_with_consistency(
        analysis_result, question, options, category,
        n_samples=5, temperature=0.7
    ))
```

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `benchmarks/scoring/extractor.py` | 修改 | 扩展 A-D → A-E，新增 markdown 模式 |
| `benchmarks/runners/baziqa_runner.py` | 修改 | 集成 Self-Consistency，安全拒绝重试 |
| `benchmarks/optimizers/__init__.py` | 新建 | 优化器包 |
| `benchmarks/optimizers/exam_prompts.py` | 新建 | Exam system prompt + 6 个分类推理模板 |
| `benchmarks/optimizers/self_consistency.py` | 新建 | Self-Consistency 投票引擎 |
| `server/rag_engine.py` | 修改 | `_build_retrieval_query()` 使用全部模板 |

## 不变的文件

以下文件**不做任何修改**：
- `server/app.py` — 线上 /chat 端点保持不变
- `server/llm.py` — `build_chat_system_prompt()` 保持不变
- `server/analysis.py` — 分析流水线保持不变
- `bazi_pro/core/` — 确定性计算引擎保持不变

## 成本估算

| 指标 | 基线 | 优化后 |
|------|------|--------|
| 每题 LLM 调用 | 1 次 | 5-6 次（Self-Consistency） |
| 总 LLM 调用 | 688 次 | ~3800 次 |
| 评测时间 | ~5h | ~25h |
| 目标准确率 | 51.6% | 80%+ |

## 验证方法

1. 先在 10 个 subject 子集上快速验证（~50 题），确认 prompt 改进有效
2. 对比基线：exam prompt（无投票） vs exam prompt + 5 次投票
3. 全量跑 91 个 subject，生成新基线报告
4. 错题分析：对比优化前后的错题分布变化

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Self-Consistency 投票仍低于 80% | 增加 few-shot 示例（从数据集中选 3 道典型题注入 prompt） |
| LLM 安全拒绝增加（敏感人物） | 重试机制 + 中性措辞替换 |
| 评测时间过长（25h+） | 可用 `--max-persons` 限制 subject 数量做快速迭代 |
| Exam Prompt 太简洁导致推理不足 | A/B 测试不同 prompt 长度，找最优平衡点 |
