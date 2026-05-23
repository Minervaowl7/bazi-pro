# bazi-pro Code Wiki

> 项目：bazi-pro v4.4.1 — 可审计、可交互、可视化的八字命理分析引擎
> 文档生成时间：2026-05-22

---

## 目录

1. [项目概览](#1-项目概览)
2. [整体架构](#2-整体架构)
3. [模块职责与文件映射](#3-模块职责与文件映射)
4. [核心类与函数详解](#4-核心类与函数详解)
5. [数据流与执行流程](#5-数据流与执行流程)
6. [依赖关系](#6-依赖关系)
7. [项目运行方式](#7-项目运行方式)
8. [测试与质量保障](#8-测试与质量保障)
9. [参考文档与知识库](#9-参考文档与知识库)
10. [版本与演进](#10-版本与演进)

---

## 1. 项目概览

| 属性 | 说明 |
|------|------|
| **项目名称** | bazi-pro |
| **版本** | v4.4.1 |
| **定位** | AI Agent Skill（v3.3+ 执行流），专注八字命盘解读，不计算只解读 |
| **核心能力** | BM25+Hybrid 古籍检索、六层格局筛查、四层喜用神裁决、交互式仪表盘、证据链输出 |
| **语料规模** | 2964 条古籍条文，6 部经典，约 29.8 万字 |
| **Python 版本** | >= 3.10 |
| **许可证** | MIT |

### 1.1 设计哲学（非协商原则）

- **算析分离**：排盘计算由 Bazi MCP 完成，本仓库只负责解读
- **无伪造引用**：每条古籍引用必须来自 `retrieve_classical.py` 输出
- **计算边界**：简单统计 LLM 可做，复杂计算（乘法链、藏干比例、合化修正）必须由 MCP/脚本完成
- **线性执行流**：Step 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → [可选] 10，无"暂定→回补"循环
- **伦理优先**：健康、财务、婚姻等话题使用文化参考措辞，不做确定性预测

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         输入层 (Input)                               │
│  Bazi MCP JSON  ──►  字段校验与降级  ──►  统一字段识别               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      古籍检索层 (Evidence Retrieval)                 │
│  retrieve_classical.py  ──►  BM25 + jieba  ──►  双通道反事实检索     │
│  hybrid_search.py       ──►  BM25 + 向量 + 权威权重（可选降级）      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      解读引擎层 (Analysis Engine)                    │
│  SKILL.md  ──►  九步线性执行流                                       │
│    Step 1(数据校验) → Step 2(旺衰) → Step 3(格局·六层筛查)          │
│    → Step 4(喜用·四层裁决) → Step 5(五行力量) → Step 6(大运流年)    │
│    → Step 7(刑冲合害) → Step 8(分维度) → Step 9(历史校准)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      证据链层 (Evidence Pipeline)                    │
│  evidence.py  ──►  结构化证据 JSON（claim + confidence + basis）     │
│  trace.py     ──►  可回放分析 trace（stage + evidence 交叉引用）     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      输出层 (Output / Presentation)                  │
│  generate_report.py  ──►  Markdown / HTML / PDF 报告                │
│  dashboard.py        ──►  交互式仪表盘（SVG 雷达图 + 大运时间轴）    │
│  ui/report.py        ──►  咨询报告（封面 → Executive Summary）       │
│  ui/replay.py        ──►  裁决过程回放（三栏：主张·证据·反证）        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 三层代码组织

| 层级 | 目录 | 职责 |
|------|------|------|
| **脚本层** | `scripts/` | CLI 入口，向后兼容早期使用方式 |
| **包层** | `bazi_pro/` | 核心引擎包，含 `ui/` 子包 |
| **参考层** | `references/` | 古籍语料、伦理规范、调候表、迁移清单等 |

---

## 3. 模块职责与文件映射

### 3.1 核心引擎模块 (`bazi_pro/`)

| 文件 | 职责 | CLI 入口 |
|------|------|----------|
| `retrieve_classical.py` | BM25 + jieba 古籍检索；索引缓存；批量检索；JSON 性能元数据 | `bazi-retrieve` |
| `generate_report.py` | 报告生成器：Markdown/HTML/PDF；封面+目录+样式；emoji→PDF 降级 | `bazi-report` |
| `dashboard.py` | 交互式仪表盘：SVG 五行雷达图、评分色环、大运时间轴、暗色/亮色主题 | — |
| `evidence.py` | 证据链对象：`new_evidence()` / `build_analysis_evidence()`；结构化 JSON 输出 | `bazi-evidence` |
| `hybrid_search.py` | 融合检索骨架：BM25 + 向量(FAISS) + 权威权重 + 主题匹配；缺依赖自动降级 | — |
| `doctor.py` | 环境诊断：Python/jieba/语料库/缓存/Dashboard/Markdown/PDF/Hybrid 一键检查 | `bazi-doctor` |
| `trace.py` | 分析追踪：`TraceBuilder` 逐步构建 trace JSON；`validate_trace()` schema 校验 | `bazi-trace` |
| `view_model.py` | 共享数据层：`DashboardVM` / `PillarVM` / `VerdictVM` / `EvidenceVM` 等 dataclass | — |

### 3.2 UI 子包 (`bazi_pro/ui/`)

| 文件 | 职责 |
|------|------|
| `report.py` | 咨询报告渲染：封面 → Executive Summary → 裁决表 → 风险建议 → 正文 → 附录 |
| `replay.py` | 裁决回放渲染：三栏布局（推理步骤导航 / 步骤详情 / 主张与反证） |
| `report_composer.py` | Markdown → 结构化报告文档：技术章节自动归类到 Appendix；表格折叠 |
| `text_cleaner.py` | 统一输出编辑层：去 Markdown 残留、括号闭合、label/note 拆分 |
| `verdict_seal.py` | 命理裁决朱砂印章 SVG：中心裁决字 + 外圈五行纹样 + caption |

### 3.3 脚本兼容层 (`scripts/`)

`scripts/` 下各文件为 `bazi_pro/` 对应模块的轻量 wrapper，保持向后兼容：

```python
# scripts/retrieve_classical.py 示例
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bazi_pro.retrieve_classical import main
if __name__ == "__main__":
    main()
```

### 3.4 参考文档 (`references/`)

| 文件 | 内容 |
|------|------|
| `classical_corpus.md` | 2964 条古籍语料，行格式：`[ID] @topic @source ## content` |
| `tiaohou.md` | 调候用神参考表（10 天干 × 12 月令，基于《穷通宝鉴》） |
| `ETHICS.md` | 伦理措辞规则、禁止用语、特殊情境模板 |
| `bazi-mcp-direct-call.md` | MCP 不可用时直接调用 Node.js 排盘模块指南 |
| `migration-checklist.md` | 跨机器迁移检查清单 |
| `case-study-false-positive-yangren.md` | 羊刃假阳性陷阱案例研究 |
| `design_tokens.css` | 设计令牌（颜色、字体、间距） |
| `cross-platform-font-setup.md` | 跨平台字体配置（Linux/WSL emoji 降级等） |
| `report-style-example.md` | 报告样式示例 |

---

## 4. 核心类与函数详解

### 4.1 古籍检索 (`retrieve_classical.py`)

#### `BM25` 类

```python
class BM25:
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75)
    def score(self, query: list[str], doc: list[str]) -> float
    def get_top_n(self, query: list[str], n: int = 5) -> list[tuple[int, float]]
```

- 标准 Okapi BM25 实现
- `corpus` 为已分词的文档列表
- 支持 `pickle` 序列化用于缓存

#### `retrieve()` — 核心 API

```python
def retrieve(corpus_path: str, query_str: str, k: int = 8,
             force_rebuild: bool = False) -> dict
```

返回结构：

```json
{
  "mode": "bm25_cached",
  "cache": "hit",
  "latency_ms": 12,
  "corpus_size": 2964,
  "results": [
    {"score": 24.17, "id": "ZPZ_00031", "topic": "格局", "source": "子平真诠", "content": "..."}
  ]
}
```

#### `retrieve_batch()` — 批量检索

复用同一 BM25 索引，N 个 query 一次完成。

#### 缓存机制

- 缓存目录：`.cache/`
- 缓存键：语料文件路径 + mtime + size 的 MD5 前 12 位
- 冷启动构建索引约 1.8s，热查询毫秒级

---

### 4.2 融合检索 (`hybrid_search.py`)

#### `HybridSearcher` 类

```python
class HybridSearcher:
    def __init__(self, bm25, entries: list[dict],
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2")
    def build_vector_index(self, corpus_texts: list[str])
    def search(self, query_str: str, k: int = 8,
               bm25_weight: float = 0.55, vector_weight: float = 0.30) -> list[dict]
```

融合得分公式：

```
score = 0.55 × BM25_norm + 0.30 × cosine_sim
        + 0.10 × authority(source) + 0.05 × topic_match
```

- 可选依赖缺失时自动降级为纯 BM25（`hybrid_retrieve_or_fallback()`）
- 权威权重表 `CLASSICAL_AUTHORITY`：子平真诠/滴天髓=1.0，穷通宝鉴=0.95，...

---

### 4.3 证据链 (`evidence.py`)

#### `new_evidence()` — 单条证据工厂

```python
def new_evidence(
    claim: str,
    confidence: float,
    basis_mcp: list[str],
    basis_classics: list[str],
    basis_rules: list[str],
    counter_evidence: Optional[list[str]] = None,
    final_decision: str = ""
) -> dict
```

返回证据对象结构：

```json
{
  "claim": "...",
  "confidence": 0.85,
  "basis": {
    "mcp_fields": [...],
    "classics": [...],
    "rules": [...]
  },
  "counter_evidence": [...],
  "final_decision": "..."
}
```

#### `build_analysis_evidence()` — 完整证据链构建

输入旺衰、格局、喜用神、古籍引用、大运摘要等，输出包含 4-5 条证据的完整链条（E1 旺衰 → E2 格局 → E3 喜用神 → E4 大运 → E5 关键结构）。

---

### 4.4 分析追踪 (`trace.py`)

#### `TraceBuilder` 类

```python
class TraceBuilder:
    def __init__(self, run_id: Optional[str] = None)
    def set_input(self, day_master: str = "", pillars: list[str] = None, ...)
    def add_stage(self, stage_id: str, *, title: str = "", summary: str = "",
                  status: str = "done", confidence: float = None,
                  claims: list[str] = None, evidence_ids: list[str] = None,
                  decision: str = "", outputs: dict = None, results: list[dict] = None)
    def add_evidence(self, ev_id: str, *, claim: str = "", ...)
    def set_artifacts(self, report_html: str = "", report_md: str = "", ...)
    def build(self) -> dict
    def write(self, path: str)
```

#### `validate_trace()` — Schema 校验

校验规则：
- `schema_version` 必须为 `"trace.v1"`
- `stages` 数量 >= 3
- 每个 stage 必须含 `id/title/summary/status`
- `evidence_ids` 交叉引用必须存在
- `engine.corpus_size` >= 2900

---

### 4.5 仪表盘 (`dashboard.py`)

#### `generate_dashboard()` — 主入口

```python
def generate_dashboard(meta: dict, analysis_text: str,
                       report_title: str, report_date: str,
                       md_to_html_func) -> str
```

从分析文本提取数据，生成完整 HTML 仪表盘，包含：

| 组件 | 说明 |
|------|------|
| 四柱卡片 | 天干五行着色，hover 上浮效果 |
| 格局评分 | SVG 环形进度条，颜色分级（>=80 绿 / 60-79 浅绿 / 40-59 橙 / <40 红） |
| 五行雷达图 | SVG 五边形雷达图，数据点带颜色 |
| 五行占比条 | 横向进度条，木火土金水 |
| 证据链审查 | 可展开 `details` 面板，含置信度色标、古籍依据标签 |
| 刑冲合害图谱 | SVG 节点关系网（年/月/日/时四柱 + 关系边） |
| 大运时间轴 | 横向滚动卡片，吉凶色标 |
| 详细分析 | 可折叠区域，Markdown 转 HTML |

#### 数据提取 (`extract_dashboard_data()`)

通过正则从 Markdown 分析文本中提取：
- 四柱（`年|月|日|时` 表格行）
- 五行力量（ASCII 柱状图或百分比表格）
- 格局评分（`\d+/100`）
- 喜用神（正则匹配）
- 大运列表（表格行匹配）

---

### 4.6 报告生成器 (`generate_report.py`)

#### `generate_html_report()` — HTML 报告

- 中国传统美学排版（暖色调、宋体、金色点缀）
- 封面：标题 + 副标题 + 日期 + 命主基本信息表
- 目录：自动从 Markdown 标题生成，带编号和锚点跳转
- 正文：Markdown → HTML（表格、代码块、引用、列表、ASCII 艺术）
- 页脚：免责声明 + 生成时间戳

#### `generate_enhanced_markdown()` — Markdown 报告

- 增强版 Markdown，含元数据头和统一页脚
- 零转换、零失真，跨平台通用

#### PDF 生成 (`try_generate_pdf()`)

- 尝试顺序：weasyprint → pdfkit → 失败提示
- Emoji 降级：彩色 emoji → 文本符号（`_EMOJI_FALLBACK` 映射表）

---

### 4.7 环境诊断 (`doctor.py`)

检查项：

| 检查项 | 通过标准 |
|--------|----------|
| Python | >= 3.10 |
| jieba | 已安装 |
| Corpus | 语料库存在且条目 > 0 |
| BM25 cache | 缓存 warm 或 cold（首次运行构建） |
| Dashboard | 可导入 |
| Markdown | installed 或 stdlib fallback |
| PDF (weasyprint) | installed 或 disabled |
| Hybrid Search | ready 或 downgraded to BM25-only |
| Examples | 示例目录存在 |

---

### 4.8 ViewModel (`view_model.py`)

核心 dataclass：

| 类 | 职责 |
|----|------|
| `DashboardVM` | 仪表盘/报告/回放三种形态的共享数据源 |
| `PillarVM` | 一柱命盘数据（位置、天干、地支、五行、十神、藏干） |
| `VerdictVM` | 最终裁决（日主、格局、决策、用神/喜神/忌神、置信度） |
| `WuxingVM` | 五行力量分布（木火土金水 + 角色映射 + 解读文字） |
| `EvidenceVM` | 单条证据（stage_id、claim、decision、confidence、rules、classics） |
| `RelationVM` | 刑冲合害关系（类型、来源柱、目标柱、描述、影响、严重度） |
| `TraceStageVM` | 推理链一步（id、title、summary、status、confidence、rules、证据） |
| `DayunVM` | 大运（干支、年龄段、十神、评估） |

构建器：
- `build_vm_from_trace(trace: dict) -> DashboardVM` — 从 trace.json 构建
- `build_vm_from_analysis_text(text: str) -> DashboardVM` — 从 Markdown 分析文本构建（过渡方案）

---

### 4.9 UI 组件

#### `verdict_seal.py` — 裁决印章

```python
def render_seal_svg(vm: DashboardVM, size: int = 180) -> str
```

- 中心大字：根据裁决决策显示"正格"/"从格"/"化气"等
- 副字："不从"/"假从"等
- 外圈纹样：四柱天干五行对应颜色的弧线段
- 下方 caption：用神/喜神

#### `report_composer.py` — 报告编排

```python
def parse_markdown_to_document(md_text: str) -> ReportDocument
def render_document_body(doc: ReportDocument, md_to_html=None) -> str
```

- 自动识别技术章节（第〇步、双通道、BM25、六层筛查等）→ 归入 Appendix
- Reader-facing 章节保留在正文
- 表格密集章节自动加折叠按钮

#### `text_cleaner.py` — 文本清洗

```python
def clean_text(raw: str) -> str
def clean_pattern(raw_pattern: str) -> tuple[str, str]   # (short, detail)
def clean_yongshen(raw: str) -> tuple[str, str]          # (label, note)
def clean_xishen_jishen(raw: str) -> list[str]           # 五行标签列表
def build_clean_verdict(...) -> CleanVerdict
```

- 去 Markdown 加粗/斜体/代码标记
- 修括号闭合
- 过长括号内容截断（>10字 → 前8字+...）
- 格局名映射到短标签（如"建禄月劫，透官煞，..." → "建禄月劫 · 官杀混杂"）

---

## 5. 数据流与执行流程

### 5.1 标准分析流程（九步线性流）

```
用户输入（Bazi MCP JSON）
    │
    ▼
Step 0: 古籍条文检索
    ├─ 0.0 五行快速预检（粗略统计印比/克泄耗占比）
    ├─ 0.1 单通道检索（正常命盘）
    └─ 0.2 双通道检索（极偏/偏枯/灰区命盘）
    │
    ▼
Step 1: 数据校验摘要（基本信息表 + 四柱十神表 + 神煞分类表）
    │
    ▼
Step 2: 日主旺衰判断（得令 + 得地 + 得势 量化三要素）
    │
    ▼
Step 3: 格局判定（六层筛查：层0特殊格局 → 层1本气透干 → 层2中气透干 → 层3暗格/建禄月劫 → 层4混杂 → 层5成败 → 层6量化评分）
    │
    ▼
Step 4: 喜用判定（四层架构：格局用神 → 病药用神 → 扶抑用神 → 调候用神，格局优先裁决）
    │
    ▼
Step 5: 五行力量分析（基础力量计算 + 合化动态修正 + 空亡影响）
    │
    ▼
Step 6: 大运流年分析（大运总体趋势 + 病药突破例外 + 连续性忌神检测 + 重点年份提取）
    │
    ▼
Step 7: 刑冲合害与空亡综合分析
    │
    ▼
Step 8: 分维度解读（性格/事业/财运/感情/健康/近期，每维 ≥1 风险/劣势）
    │
    ▼
Step 9: 历史事件校准（3-5 个候选事件验证，根据反馈修正喜用神）
    │
    ▼
[可选] Step 10: 生成分析报告（Markdown / HTML / PDF / 仪表盘）
```

### 5.2 两轮对话协议（详细版专用）

```
Turn 1: 数据确认 + 历史校准
    ├─ Step 1 盘面摘要
    ├─ Step 2 旺衰判定
    ├─ 五行原始数据预览（不含合化修正）
    └─ 3 个历史验证问题
    → 停止，等待用户回复

Turn 2: 校准 + 全盘深度解读
    ├─ 比对反馈 → 校准用神
    ├─ Step 3 格局
    ├─ Step 4 喜用（含修正）
    ├─ Step 5 五行力量（含合化修正）
    ├─ Step 6 大运
    ├─ Step 7 刑冲合害
    ├─ Step 8 分维度
    └─ 免责声明
```

### 5.3 Evidence Pipeline 数据流

```
分析文本 (Markdown)
    │
    ▼
extract_dashboard_data()  ──►  DashboardVM
    │
    ├─► dashboard.py ──► 交互式 HTML 仪表盘
    ├─► ui/report.py ──► 咨询报告 HTML
    ├─► ui/replay.py ──► 裁决回放 HTML
    └─► evidence.py  ──► 结构化 evidence JSON
```

---

## 6. 依赖关系

### 6.1 依赖图谱

```
bazi-pro
├── jieba (>=0.42.1)          [核心依赖，必须]
│
├── markdown (>=3.5)            [可选，报告生成增强]
│   └── generate_report.py (HTML 输出)
│
├── weasyprint (>=60)           [可选，PDF 生成]
│   └── generate_report.py (--pdf)
│
├── sentence-transformers (>=2.2) [可选，Hybrid Search]
├── faiss-cpu (>=1.7)           [可选，向量索引]
├── numpy (>=1.24)              [可选，数值计算]
│   └── hybrid_search.py
│
└── 标准库: sys, os, re, json, math, time, hashlib, pickle,
            argparse, textwrap, datetime, html, pathlib, typing,
            dataclasses, collections, subprocess
```

### 6.2 模块导入关系

```
generate_report.py
    └── dashboard.py
        └── view_model.py
            └── ui/text_cleaner.py (可选)

evidence.py
    └── trace.py (validate_trace / demo_trace)

doctor.py
    └── retrieve_classical.py (_cache_path, _resolve_corpus)
    └── dashboard.py (generate_dashboard)

ui/report.py
    └── view_model.py
    └── ui/verdict_seal.py

ui/replay.py
    └── view_model.py

view_model.py
    └── ui/text_cleaner.py (可选)
```

### 6.3 脚本与包模块映射

| 脚本 (`scripts/`) | 包模块 (`bazi_pro/`) | 说明 |
|-------------------|----------------------|------|
| `retrieve_classical.py` | `retrieve_classical.py` | 轻量 wrapper |
| `generate_report.py` | `generate_report.py` | 轻量 wrapper |
| `dashboard.py` | `dashboard.py` | 轻量 wrapper |
| `evidence.py` | `evidence.py` | 轻量 wrapper |
| `hybrid_search.py` | `hybrid_search.py` | 轻量 wrapper |
| `doctor.py` | `doctor.py` | 轻量 wrapper |
| `trace.py` | `trace.py` | 轻量 wrapper |

---

## 7. 项目运行方式

### 7.1 安装

```bash
git clone git@github.com:Minervaowl7/bazi-pro.git
cd bazi-pro
pip install -r requirements.txt        # 核心：jieba
# pip install -e .                     # 安装为包（含 console scripts）
```

### 7.2 核心命令

```bash
# 古籍检索
python scripts/retrieve_classical.py "食神 制杀 身弱" -k 3 --json
python scripts/retrieve_classical.py --stats
python scripts/retrieve_classical.py --cache-info

# 批量检索
python scripts/retrieve_classical.py --batch "食神" "七杀" "调候" -k 2 --json

# 报告生成
python scripts/generate_report.py --input examples/sample_analysis.md --output report.md
python scripts/generate_report.py --input examples/sample_analysis.md --output report.html --format html
python scripts/generate_report.py --input examples/sample_analysis.md --theme dashboard --format html --output dashboard.html

# 环境诊断
python scripts/doctor.py

# 证据对象
python scripts/evidence.py

# Trace 演示与校验
python -m bazi_pro.trace demo > /tmp/trace.json
python -m bazi_pro.trace validate /tmp/trace.json

# Hybrid Search 状态检查
python scripts/hybrid_search.py
```

### 7.3 Console Scripts（pip install -e . 后）

```bash
bazi-retrieve "食神 制杀 身弱" -k 3 --json
bazi-report --input analysis.md --output report.html
bazi-doctor
bazi-evidence
bazi-trace demo
```

### 7.4 作为 Python 包使用

```python
from bazi_pro.retrieve_classical import retrieve, retrieve_batch, load_corpus
from bazi_pro.evidence import build_analysis_evidence, new_evidence
from bazi_pro.dashboard import generate_dashboard
from bazi_pro.view_model import DashboardVM, build_vm_from_trace

# 检索
result = retrieve("references/classical_corpus.md", "伤官见官 财星通关", k=5)

# 构建证据链
evidence = build_analysis_evidence(
    day_master="丙火", gender="女", bazi="...",
    deling_score=-2, dedi_score=2.3, deshi_score=2.9,
    wangshuai="身弱", pattern_name="暗食神格", pattern_score=65,
    yongshen="土", xishen="木、火", jishen="水",
    classical_refs=[...], key_features=[...], dayun_summary=[...]
)
```

---

## 8. 测试与质量保障

### 8.1 CI 流程 (`.github/workflows/ci.yml`)

| 步骤 | 说明 |
|------|------|
| Version consistency | `__version__` / README / pyproject.toml 版本一致性 |
| Corpus stats | `retrieve_classical.py --stats` |
| Basic retrieve | 单条检索 |
| Batch retrieve | 批量检索 |
| Doctor | 环境诊断 |
| Evidence | 证据对象生成与校验 |
| Hybrid status | Hybrid Search 状态 |
| Report markdown | Markdown 报告生成 |
| Dashboard | 仪表盘生成（含 evidence-card / relation-graph 检查） |
| Trace validation | trace demo + validate |
| Golden cases | 边界回归测试（4 例） |
| Package import | 全部模块可导入 |
| Install package | `pip install -e .` |
| Console scripts | `bazi-retrieve` / `bazi-doctor` / `bazi-evidence` |
| Wheel build | 构建 wheel 并安装验证 |

### 8.2 测试文件 (`tests/`)

| 文件 | 说明 |
|------|------|
| `test_retrieve.py` | Smoke tests：检索、批量、统计、缓存、doctor、evidence、hybrid、report、dashboard |
| `test_html_quality.py` | HTML 输出质量检查 |
| `test_trace.py` | Trace schema 校验测试 |
| `run_golden.py` | Golden Cases 边界回归测试 |
| `golden_cases/*.json` | 83 例边界案例：从杀 vs 身弱、羊刃 vs 从强、伤官见官、建禄月劫 等 |

### 8.3 Golden Cases（边界回归测试）

| 案例 | 测试重点 |
|------|----------|
| `congsha_vs_shenruo.json` | 从杀格 vs 身弱格边界 |
| `yangren_vs_congqiang.json` | 羊刃格 vs 从强格边界（典型假阳性陷阱） |
| `shangguan_jianguan.json` | 伤官见官 + 财星通关 |
| `jianyue_luyue_jiejian.json` | 建禄月劫 + 比劫拦截 |

---

## 9. 参考文档与知识库

### 9.1 执行规范

| 文档 | 内容 |
|------|------|
| `SKILL.md` | 核心运行时契约：九步执行流、两轮对话协议、计算外包原则、输出规范、免责声明、红线警示表 |
| `CLAUDE.md` | 本仓库的 Claude Code 工作指南（项目角色、关键文件、设计原则、编辑规范） |
| `README.md` | 用户面向的引擎架构说明、30 秒体验、版本历史 |

### 9.2 伦理与安全

| 文档 | 内容 |
|------|------|
| `references/ETHICS.md` | 伦理措辞规则：禁止确定性预测、禁止恐惧性语言、健康/财务/婚姻等话题的文化参考措辞模板 |

### 9.3 命理知识库

| 文档 | 内容 |
|------|------|
| `references/classical_corpus.md` | 6 部经典 2964 条原文（子平真诠、滴天髓、渊海子平、神峰通考、三命通会、穷通宝鉴） |
| `references/tiaohou.md` | 十天干 × 十二月令调候用神表 |
| `references/case-study-false-positive-yangren.md` | 羊刃假阳性案例研究 |

### 9.4 工程参考

| 文档 | 内容 |
|------|------|
| `references/migration-checklist.md` | 跨机器迁移：路径、依赖、smoke tests |
| `references/bazi-mcp-direct-call.md` | MCP 不可用时直接调用 Node.js 排盘 |
| `references/cross-platform-font-setup.md` | Linux/WSL 字体与 emoji 降级 |
| `references/design_tokens.css` | 颜色、字体、间距设计令牌 |
| `references/report-style-example.md` | 报告样式示例 |

---

## 10. 版本与演进

| 版本 | 关键特性 |
|------|----------|
| **v4.4** | 报告编排器（report_composer.py）、文本清洗层（text_cleaner.py）、裁决印章（verdict_seal.py）、咨询报告（report.py）、回放视图（replay.py） |
| **v4.3** | Golden Cases (4例) + CI + Web Demo 首页 + Evidence Pipeline + 包结构重构 |
| **v4.1** | bazi doctor · pyproject 包结构修复 · README 引擎化 · 检索性能元数据 |
| **v4.0** | Evidence Object · BM25 缓存 · 批量检索 · Hybrid Search 骨架 · 仪表盘 v2.0 |
| **v3.5** | 层3比劫拦截（禁止"暗劫财格"）· 强制自动生成报告 · 交互式仪表盘 |
| **v3.4** | 报告生成器跨平台字体 · 调候双通道 · 病药突破大运上限 |
| **v3.3** | 算析分离·线性执行流 · 两轮对话协议 · 计算外包原则 · 燥湿寒暖偏枯预检 |
| **v3.2** | 负面清单强制规则 · 评分基准锚防通胀 · 连续性忌神大运专项分析 |
| **v3.1** | 第〇步双通道检索+反事实裁决 · 从强格/假从强格纳入层0 |
| **v2.3** | 第〇步古籍检索（BM25+jieba，2964条6经典） |

---

## 附录：文件清单

```
bazi-pro/
├── .github/workflows/ci.yml
├── bazi_pro/
│   ├── __init__.py
│   ├── retrieve_classical.py      # BM25 古籍检索
│   ├── generate_report.py         # 报告生成器
│   ├── dashboard.py               # 交互式仪表盘
│   ├── evidence.py                # 证据链对象
│   ├── hybrid_search.py           # 融合检索
│   ├── doctor.py                  # 环境诊断
│   ├── trace.py                   # 分析追踪
│   ├── view_model.py              # 共享数据层
│   └── ui/
│       ├── __init__.py
│       ├── report.py              # 咨询报告渲染
│       ├── replay.py              # 裁决回放渲染
│       ├── report_composer.py     # 报告编排器
│       ├── text_cleaner.py        # 文本清洗
│       ├── verdict_seal.py        # 裁决印章 SVG
│       ├── templates/__init__.py
│       └── static/
│           ├── __init__.py
│           └── tokens.css
├── scripts/                       # CLI 兼容层
│   ├── retrieve_classical.py
│   ├── generate_report.py
│   ├── dashboard.py
│   ├── evidence.py
│   ├── hybrid_search.py
│   ├── doctor.py
│   ├── trace.py
│   └── __init__.py
├── tests/
│   ├── test_retrieve.py
│   ├── test_html_quality.py
│   ├── test_trace.py
│   ├── run_golden.py
│   └── golden_cases/
│       ├── congsha_vs_shenruo.json
│       ├── jianyue_luyue_jiejian.json
│       ├── shangguan_jianguan.json
│       └── yangren_vs_congqiang.json
├── references/
│   ├── classical_corpus.md        # 2964 条古籍语料
│   ├── tiaohou.md                 # 调候用神表
│   ├── ETHICS.md                  # 伦理规范
│   ├── bazi-mcp-direct-call.md    # MCP 绕过指南
│   ├── migration-checklist.md     # 迁移清单
│   ├── case-study-false-positive-yangren.md
│   ├── design_tokens.css
│   ├── cross-platform-font-setup.md
│   ├── report-style-example.md
│   ├── v4.3-hard-reset.md
│   ├── v4.3-master-brief.md
│   └── v4.3-visual-system-rewrite.md
├── examples/
│   ├── sample_analysis.md
│   ├── sample_bazi_mcp.json
│   ├── sample_dashboard.html
│   ├── sample_report.md
│   └── sample_trace.json
├── dist/
│   └── index.html                 # Web Demo 首页
├── pyproject.toml
├── requirements.txt
├── README.md
├── SKILL.md                       # 核心运行时契约
├── CLAUDE.md                      # Claude Code 工作指南
├── LICENSE
├── MANIFEST.in
└── .gitignore
```

---

*本文档由项目代码分析自动生成，涵盖 bazi-pro v4.4.1 的完整架构、模块、类函数、依赖与运行方式。*
