# bazi-pro v5.0

[![CI](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml)

**确定性命理计算核心 + 零幻觉叙述器 + 交互式 Web 应用**

2964 条古籍条文 · 6 部经典 · BM25+Hybrid 检索 · 六层格局筛查 · 喜用神推导 · 确定性叙述器 · Next.js 暗色主题前端 · FastAPI SSE 后端 · 插件机制

---

## 安装

```bash
# 最小安装（核心分析 + 古籍检索）
pip install -e .

# 完整安装（含向量检索、报告、PDF、服务端、TUI）
pip install -e ".[all]"

# 按需安装
pip install -e ".[server]"    # FastAPI 服务端
pip install -e ".[report]"    # Markdown/HTML 报告
pip install -e ".[pdf]"       # PDF 生成
pip install -e ".[hybrid]"    # 向量融合检索
pip install -e ".[tui]"       # Rich 终端界面
```

## 30秒体验

```bash
git clone git@github.com:Minervaowl7/bazi-pro.git
cd bazi-pro
pip install -e ".[server]"

# 启动后端 (端口 8710)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8710

# 启动前端 (另一个终端)
cd frontend && pnpm install && pnpm dev

# 打开浏览器访问 http://localhost:3000
```

```bash
# 或者使用 CLI 工具
# 检索古籍（核心功能，无需 extra）
python scripts/retrieve_classical.py "食神 制杀 身弱" -k 3 --json

# 生成技术报告
python scripts/generate_report.py --input examples/sample_analysis.md --output report.md

# 生成消费级报告（面向普通用户，六维叙事 + 术语解释）
python scripts/generate_report.py --input examples/sample_analysis.md --mode consumer --format html -o consumer.html

# 交互式仪表盘
python scripts/generate_report.py --input examples/sample_analysis.md --mode dashboard --format html -o dashboard.html

# 环境诊断
python scripts/doctor.py
```

```bash
# FastAPI 服务端（需要 [server]）
bazi-server

# Rich 终端界面（需要 [tui]）
bazi-tui

# 向量融合检索（需要 [hybrid]）
bazi-hybrid
```

---

## 引擎架构

```
用户输入 (Web 表单 / MCP JSON / CLI)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  确定性计算核心 (bazi_pro/core/ · 13 模块)       │
│  full_analysis() → dict                         │
│  十神 · 藏干 · 五行力量 · 旺衰 · 格局 · 用神     │
│  刑冲合害 · 格局之病 · 调候用神                   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  古籍检索层                                      │
│  retrieve_classical.py (BM25 + jieba + 缓存)     │
│  hybrid_search.py (FAISS + 权威权重)             │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  确定性叙述器 (bazi_pro/narrator.py)             │
│  narrate_analysis() → 9 维度专业中文文本          │
│  零 LLM · 零幻觉 · 每句可追溯到计算数据          │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  输出层                                          │
│  Web 应用 (Next.js + FastAPI SSE + SQLite)       │
│  3 种报告模式 (技术/仪表盘/消费级)                │
│  ui/ 子包 (SVG命盘 · 命运河流 · 推理图谱)         │
│  server/ (FastAPI) · tui/ (Rich 终端)            │
└─────────────────────────────────────────────────┘
```

核心原则：**算析分离** — `bazi_pro/core/` 做所有确定性命理计算，LLM 只负责解读，不参与计算。

---

## Web 应用

bazi-pro 提供完整的交互式 Web 应用（暗色主题，DeepOracle 风格）：

**前端** (`frontend/`): Next.js 14 + TypeScript + Tailwind CSS + Zustand + ECharts
- 命盘输入表单（八字 + 日主自动推导 + 性别）
- SSE 实时分析进度条
- 四柱网格 + 五行雷达图
- 确定性叙述面板（旺衰/格局/用神/调候/五行/刑冲/性格/事业）
- 大运时间轴
- 历史记录侧边栏

**后端** (`server/`): FastAPI + SSE + SQLite
- `POST /api/v2/analyze` — 提交分析，返回 analysis_id + SSE stream URL
- `GET /api/v2/analysis/{id}/stream` — SSE 实时进度推送（含事件缓冲回放）
- `GET /api/v2/analysis/{id}` — 完整结果 + 确定性叙述文本
- `GET /api/v2/history` — 分页历史记录

**叙述器** (`bazi_pro/narrator.py`): 从计算结果直接生成命理师风格中文文本
- 9 个维度：总览/旺衰/格局/用神/调候/五行/刑冲/性格/事业
- 零 LLM 依赖，每句话可追溯到确定性计算数据
- 风格：先下结论再给论据，用干支语言，敢说"不确定"

---

## 能力状态

### 稳定能力

| 能力 | 代码入口 | 说明 |
|------|---------|------|
| 十神推导 | `bazi_pro.core.constants.derive_shishen` | 10 种十神完整推导 |
| 藏干展开 | `bazi_pro.core.hidden_stems.get_canggan` | 含气级别 (本/中/余) |
| 五行力量 | `bazi_pro.core.elements.calc_element_forces` | 原始 + 合化修正双版本 |
| 旺衰判定 | `bazi_pro.core.strength.judge_wangshuai` | 得令/得地/得势三维判定 |
| 格局筛查 | `bazi_pro.core.patterns.screen_pattern` | 六层算法 (化气→专旺→从格→L1→L2→L3) |
| 喜用神推导 | `bazi_pro.core.yongshen.derive_yongshen` | 格局感知，含喜/忌/闲神 |
| 刑冲合害 | `bazi_pro.core.relations.detect_relations` | 三合/六合/三刑/冲/害/暗合/半合 |
| 格局之病 | `bazi_pro.core.disease.detect_disease` | 5 类病症检测 + 药方建议 |
| 调候用神 | `bazi_pro.core.tiaohou.lookup_tiaohou` | 穷通宝鉴 120 条查表 |
| 古籍检索 | `bazi_pro.retrieve_classical.retrieve` | BM25 + 反证通道 |
| 消费级报告 | `bazi_pro.ui.consumer_report` | 六维叙事 + 术语解释 + 暗色模式 |
| 98 Golden Cases | `tests/run_golden.py` | 98/98 通过 |

> **格局筛查说明**：六层算法覆盖化气格、专旺格、从格（从强/从财/从官杀/从儿）、建禄月劫格、正格月令透干、暗格。调候用神已编码为确定性查表（穷通宝鉴 120 条）。
>
> **Golden Cases 说明**：覆盖十神推导、旺衰判定、格局筛查、喜用神推导、刑冲合害等确定性规则的边界情况。不覆盖命理争议点。

### 实验能力

| 能力 | 代码入口 | 说明 |
|------|---------|------|
| 命盘对比 | `bazi_pro.compare_engine` | 置信区间 ±15%，不返回伪精确分数 |
| 流年沙盒 | `bazi_pro.liunian_sandbox` | 依赖 AnalysisEngine 结果 |
| 向量融合检索 | `bazi_pro.hybrid_search` | 需要 sentence-transformers + FAISS |
| 大运流年 | `bazi_pro.view_model` (dayun 提取) | 从分析文本提取，部分边界情况待完善 |

---

## 报告模式

| 模式 | CLI | 受众 | 说明 |
|------|-----|------|------|
| `report` | `--mode report` | 命理师/开发者 | 技术报告，按分析步骤排列，含完整表格和评分 |
| `dashboard` | `--mode dashboard` | 命理师/开发者 | 交互式仪表盘，SVG 图表 + 证据链 + 推理图谱 |
| `consumer` | `--mode consumer` | 普通用户 | 消费级报告，结论先行 + 术语解释 + 六维叙事 |

Consumer 模式特性：术语 tooltip（hover 显示通俗解释）、70 词术语小词典、六维度叙事扩展（性格/事业/财运/感情/健康/近运）、技术附录折叠、移动端适配、暗色模式。

---

## Web API 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BAZI_API_KEY` | (空) | 设置后启用 API 鉴权。REST 使用 `X-API-Key` header；WebSocket 使用 `x-api-key` header |
| `BAZI_CORS_ORIGINS` | `localhost:3000` | 逗号分隔的允许 Origin 列表。默认允许前端开发地址 |
| `BAZI_MAX_PAYLOAD_BYTES` | `10240` | 请求体最大字节数（含 chunked body） |
| `BAZI_TASK_TTL_SECONDS` | `7200` | 分析任务缓存 TTL（秒） |
| `BAZI_MAX_CONCURRENT_TASKS` | `1000` | 最大并发分析任务数 |
| `BAZI_RATE_LIMIT_REQUESTS` | `30` | 每个 IP+API key 在窗口期内最大请求数 |
| `BAZI_RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit 窗口期（秒） |
| `BAZI_HOST` | `0.0.0.0` | 服务监听地址 |
| `BAZI_PORT` | `8710` | 服务监听端口 |
| `BAZI_LOG_LEVEL` | `info` | 日志级别 |
| `BAZI_CACHE_DIR` | (平台缓存目录) | BM25 索引缓存目录，默认 `~/.cache/bazi-pro` (Linux) |
| `BAZI_DB_PATH` | `bazi_pro.db` | SQLite 数据库文件路径 |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8710` | 前端连接后端的地址（前端 .env.local） |
| `REDIS_URL` | (空) | 设置后使用 Redis 作为缓存/任务存储/限流后端 |

API 错误响应统一格式：

```json
{"error": {"code": "UNAUTHORIZED", "message": "API key 无效或缺失"}}
```

错误码：`UNAUTHORIZED` / `NOT_FOUND` / `PAYLOAD_TOO_LARGE` / `RATE_LIMITED` / `INTERNAL_ERROR` / `SERVER_BUSY`。422 Pydantic 校验错误保留 FastAPI 默认格式。

---

## CI / 测试

- **Python 版本矩阵**：3.10 / 3.11 / 3.12
- **全量 pytest**：`python -m pytest -q`
- **Ruff lint**：`ruff check server/ bazi_pro/ tests/`
- **Build 验证**：`python -m build`
- **Twine 检查**：`twine check dist/*`
- **Wheel 安装冒烟测试**：从非源码目录安装并运行 CLI
- **Console scripts 检查**：所有 entry point 可 import 且 callable

---

## 核心模块

| 模块 | 功能 | 亮点 |
|------|------|------|
| `bazi_pro/retrieve_classical.py` | BM25+古籍检索 | pickle 缓存 · `--batch` 批量 · JSON 元数据 |
| `bazi_pro/narrator.py` | 确定性叙述器 | 9 维度中文文本 · 零 LLM · 命理师风格 |
| `bazi_pro/hybrid_search.py` | 融合检索 | BM25+向量+权威权重 · 匹配词高亮 · CLI 入口 |
| `bazi_pro/generate_report.py` | 报告生成 | Markdown/HTML/PDF · `--theme dashboard` v5.0 仪表盘 |
| `bazi_pro/ui/` (子包) | 可视化组件 | 动态SVG命盘 · 命运河流时间轴 · 推理图谱 · 裁决印章 |
| `bazi_pro/view_model.py` | 共享数据层 | DashboardVM 统一三种输出形态 |
| `server/` | Web 服务 | FastAPI REST + SSE + WebSocket + SQLite 持久化 |
| `bazi_pro/tui/` | 交互终端 | Rich 彩色表格 + 进度条 + Tab 补全 REPL |
| `bazi_pro/plugin_api.py` | 插件机制 | on_retrieve / on_evidence / on_render 钩子 |
| `bazi_pro/archive.py` | 档案系统 | SQLite 存储 + 用户反馈校准 |
| `bazi_pro/doctor.py` | 环境诊断 | 16 项检查一键运行 |

---

## 版本历史

| 版本 | 内容 |
|------|------|
| **v5.0** | 确定性计算核心 (core/ 13模块)：十神推导、藏干展开、五行力量、旺衰判定、六层格局筛查、喜用神推导、刑冲合害、格局之病、调候用神 · 98 Golden Cases · 消费级报告（六维叙事+术语解释） · Pydantic API Schema · counter_evidence 通道 · 插件机制 · CLI TUI · AnalysisEngine SDK · 档案校准系统 |
| **v4.8** | 命盘对比引擎 · 古籍双栏展示 · 流年推演沙盒 · 个人命理档案 |
| **v4.7** | Hybrid Search 落地(INT8量化+FAISS+预热) · ViewModel 统一化 |
| **v4.6** | FastAPI + WebSocket 服务层 · Redis 缓存 |
| **v4.5** | 动态 SVG 命盘 · 命运河流时间轴 · 推理图谱 DAG · 印章动画升级 |
| **v4.3** | Golden Cases (4例) + CI + Web Demo 首页 + Evidence Pipeline + 包结构重构 |
| **v4.1** | bazi doctor · pyproject 包结构修复 · README 引擎化 · 检索性能元数据 |
| **v4.0** | Evidence Object · BM25缓存 · 批量检索 · Hybrid Search骨架 · examples |
| **v3.5** | 层3比劫拦截 (禁止"暗劫财格"→建禄月劫经典框架) · 强制自动生成报告 · 交互式仪表盘 |

---

## 依赖

最小安装仅需 `jieba`。可选依赖通过 `pip install -e ".[extra]"` 安装，详见上方安装章节。

---

## 许可

MIT License — 仅供传统文化学习与参考，不构成任何决策依据。

⚠️ **免责声明**：bazi-pro 的分析结果包含三类来源：(1) 确定性规则推导（十神、旺衰、六层格局筛查、喜用神、刑冲合害、格局之病、调候用神等），(2) 古籍检索（BM25 检索 6 部经典条文），(3) LLM 辅助解释（分维度叙事解读）。其中 LLM 输出为概率性生成，不代表确定性事实。请勿将任何分析结果用于人生重大决策。
