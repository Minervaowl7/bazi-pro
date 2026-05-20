# bazi-pro · 专业八字命理解读 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.4-brightgreen)](SKILL.md)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](scripts/retrieve_classical.py)

**bazi-pro** 是一个供 AI Agent 使用的八字命理解读 Skill，配合 [Bazi MCP](https://github.com/nicepkg/bazi-mcp) 排盘数据，提供从古籍条文检索到喜用神、格局、大运流年全链路的专业命理解读。

> 🎯 **定位**：Bazi MCP 负责排盘计算，bazi-pro 负责解读环节。Agent 拿到 MCP 返回的 JSON 排盘数据后，按本 Skill 的十步流程输出专业命理解读报告。

---

## ✨ 核心能力

| 模块 | 能力 |
|------|------|
| **第〇步：古籍条文检索** | BM25 + jieba 分词，从 2964 条古籍原文（6 部经典）中实时匹配最相关条文；支持双通道（顺向+反事实）检索，克服确认偏误 |
| **第一步：数据校验摘要** | 基本信息表 + 四柱十神表 + 神煞分类表 |
| **第二步：日主旺衰判断** | 月令四分 + 根气等级 + 生扶/克泄耗权重打分 |
| **第三步：格局判定** | 六层筛查：特殊格局 → 月令透干 → 暗格 → 混杂 → 成败 → 量化评分 |
| **第四步：喜用神判断** | 四层架构（格局用神 → 病药验证 → 扶抑修正 → 调候调节）+ 量化裁决（0-100 分） |
| **第五步：五行力量分析** | 基础计分 + 合化动态修正 + 中气/余气 + 空亡打折 + ASCII 力量图 |
| **第六步：大运流年** | 大运总表 + 喜忌引动 + 大运上限原则 + 流年分析 |
| **第七步：刑冲合害** | 天干五合 + 地支六合三合三会六冲六害三刑 + 合化成功率判定 |
| **第八步：六维度分述** | 性格底色 / 事业发展 / 财运分析 / 感情姻缘 / 健康养生 / 近期运势 |
| **第十步：报告生成** | 将解读输出保存为精美 HTML/MD/PDF 报告（封面+目录+样式），可选 |

### 古籍检索覆盖 6 部经典

《渊海子平》《神峰通考》《三命通会》《子平真诠》《滴天髓》《穷通宝鉴》 — 共 **2964 条原文，约 29.8 万中文字**。

---

## 📁 文件结构

```
bazi-pro/
├── SKILL.md                          # 主 Skill 定义（AI Agent 执行规范）
├── scripts/
│   ├── retrieve_classical.py         # BM25 + jieba 古籍检索脚本
│   └── generate_report.py            # 分析报告生成器（HTML/Markdown/PDF）
├── references/
│   ├── classical_corpus.md           # 2964 条古籍原文语料库
│   ├── tiaohou.md                    # 十天干调候用神速查表（基于《穷通宝鉴》）
│   ├── ETHICS.md                     # 伦理准则（措辞规范、特殊情境处理、免责声明）
│   ├── bazi-mcp-direct-call.md       # Bazi MCP 直接调用指南
│   ├── case-study-false-positive-yangren.md  # 羊刃误判案例研究
│   └── migration-checklist.md         # 跨机器迁移检查清单
├── LICENSE                           # MIT License
└── README.md
```

---

## 🚀 快速开始

### 前置依赖

```bash
pip install jieba
```

### 古籍检索（独立使用）

```bash
python3 scripts/retrieve_classical.py "<查询词>" -k 5
```

示例：
```bash
python3 scripts/retrieve_classical.py "从象 从强 假从 壬水 金水" -k 5

# 输出：
# [DTM_00082] (15.65) @十神
#     十四、假从 真从之象有几人，假从亦可发其身...
#     ——《滴天髓》
```

### Agent 完整解读

1. 通过 Bazi MCP 获取命盘 JSON 数据
2. 将 JSON 输入交给加载了本 Skill 的 AI Agent
3. Agent 按流程自动输出完整解读报告

### 报告生成

```bash
# 生成 HTML 报告（零依赖，推荐）
python scripts/generate_report.py --input analysis_output.md --output report.html

# 通过管道输入
cat analysis_output.md | python scripts/generate_report.py > report.html

# 生成 Markdown 报告
python scripts/generate_report.py --input analysis_output.md --format md --output report.md

# 同时生成 PDF（需先安装 weasyprint 或 pdfkit）
python scripts/generate_report.py --input analysis_output.md --output report.html --pdf
```

报告特性：
- 精美传统中式排版（象牙底色 + 朱红点缀）
- 封面页 + 自动目录 + 样式化表格 + ASCII 图保留
- 响应式设计，手机/桌面均可阅读
- 一键打印为 PDF（浏览器打印功能）
- 打印优化 CSS（A4 纸张，智能分页）

---

## 🔬 设计亮点

### 双通道检索（防确认偏误）

极偏命盘（印比/克泄耗 ≥75%）强制运行两组独立检索：
- **通道 A**（顺向）：基于月令初判方向
- **通道 B**（反事实）：构造对立方向（如从格方向）

两通道结果对比裁决，避免「月令第一印象 → 格局锁定 → 检索被带偏」的确认偏误链。

### 四层喜用神裁决

```
格局用神（主导层） → 病药验证 → 扶抑修正 → 调候调节
      ↓                    ↓            ↓           ↓
  《子平真诠》        《五言独步》   《滴天髓》   《穷通宝鉴》
```

四层各自打分（每层 0-25），综合 0-100。四层一致的结论置信度为 High。

### 大运上限原则

> **原局是硬件规格，大运是运行时环境——运行时不能提升硬件上限。**

大运不能改变命局本质层次，只能在原局基础上波动。此原则防止「大运好 = 格局变好」的常见误判。

---

## 📝 版本历史

| 版本 | 主要改进 |
|------|---------|
| **v3.4** | 新增报告生成功能（HTML/Markdown/PDF），scripts/generate_report.py，SKILL.md 第十步可选报告输出 |
| **v3.3** | 算析分离·线性执行流（废除暂定/回补）；两轮对话协议；计算边界明确化（LLM可做简单统计，复杂计算外包MCP）；燥湿寒暖偏枯预检；病药突破大运上限；动态负面清单比例 |
| **v3.2** | 负面清单强制规则；评分基准锚防通胀；连续性忌神大运专项分析；回补完整性校验 |
| **v3.1.2** | 修复 §0.0 阈值不一致（增设 60-74% 灰区）；§0.2 措辞统一；Step4/5 数据依赖闭环；Step6 大运缺失优雅降级 |
| **v3.1.1** | 标准版输出增强（十神表+神煞表+六层筛查+ASCII 图）、每步≥1 古籍引用 |
| **v3.1** | 第〇步双通道检索+反事实裁决；从强格/假从强格纳入层 0；层 0 筛查先全局后局部 |
| **v2.3** | 第〇步古籍检索（BM25+jieba，2964 条 6 经典） |
| **v2.2** | 三层用神架构；大运上限原则；反泛化红线 |
| **v2.1** | 十神根气虚实检查；病药法虚实预检 |

---

## ⚠️ 免责声明

本 Skill 基于传统命理学理论（参酌《穷通宝鉴》《子平真诠》《三命通会》《滴天髓》《神峰通考》等经典），**仅供传统文化学习与参考，不构成任何决策依据**。命理学属于传统文化范畴，涉及健康和财务的判断请以专业诊断为准。人生在于自身的努力和选择，命理仅为认知自我的辅助工具。

---

## 📄 License

MIT © Minervaowl
