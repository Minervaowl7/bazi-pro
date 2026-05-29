# bazi-pro v5.2

[![CI](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml)

**确定性命理计算核心 + 古籍对齐引擎 + 多流派分析路径（典籍对齐版）+ 零幻觉叙述器 + 交互式 Web 应用**

2964 条古籍条文 · 6 部经典 · BM25+Hybrid 检索 · 六层格局筛查（古籍对齐）· 破格检测 · 三流派分析（子平/盲派/新派）· 喜用神推导 · 确定性叙述器 · Next.js 暗色主题前端 · FastAPI SSE 后端 · 插件机制

**v5.2 亮点**：盲派和新派分析方法论全面对照典籍修正——盲派新增墓用/复合做功、贼神捕神检测、五党成势分析、功神废神判定；新派完善反断论（同宗对规则）、百神论（动态六亲替代）、空亡出空机制、格局分类（扶抑/从强/从弱）。507 Golden Cases 全部通过。

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

# 启动后端 (端口 8711)
python -m uvicorn server.app:app --host 127.0.0.1 --port 8711

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
│  刑冲合害 · 格局之病 · 调候用神 · 破格检测        │
└─────────────────────────────────────────────────┘
    │
    ├──→ ┌─────────────────────────────────────┐
    │     │  多流派分析 (bazi_pro/core/schools/) │
    │     │  ZipingAnalyzer · MangpaiAnalyzer   │
    │     │  XinpaiAnalyzer · school_analyze()  │
    │     └─────────────────────────────────────┘
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

## 古籍对齐引擎 (v5.1)

格局判定严格对齐子平真诠、渊海子平、滴天髓、神峰通考等经典原文：

### 专旺格（曲直/炎上/稼穑/从革/润下）

| 规则 | 古籍依据 | 实现 |
|------|---------|------|
| 必须有地支方局/三合局 | 子平真诠"取甲乙全亥卯未、寅卯辰" | `_check_formation()` |
| 必须月令当令 | 渊海子平"又生春月之类" | `_check_month_season()` |
| 无方局/三合局降级为从强格 | 子平真诠格局定义 | `_screen_layer0()` 降级逻辑 |
| 官杀逆势破格 | 渊海子平"最怕引至时为死绝之乡" | `_check_zhuanwang_break()` |

### 化气格（甲己化土/乙庚化金/丙辛化水/丁壬化木/戊癸化火）

| 规则 | 古籍依据 | 实现 |
|------|---------|------|
| 必须月令当令 | 子平真诠"要化出之物，得时乘令" | `HUA_SEASON_MAP` + 真化/假化区分 |
| 必须地支根局 | 子平真诠"四支局全" | `_check_formation()` |
| 争合破格 | 渊海子平"己字中露出二甲字，谓之争合" | `_check_hua_break()` |
| 妒合破格 | 渊海子平"有一个乙字露出，谓之妒合" | `_check_hua_break()` |
| 克化神破格 | 子平真诠 | `_check_hua_break()` |

### 从格（从财/从官杀/从儿/从强）

| 规则 | 古籍依据 | 实现 |
|------|---------|------|
| 从财须会财 | 渊海子平"弃命从财，须要会财" | `_check_formation()` 财局检测 |
| 从杀须会杀 | 渊海子平"弃命从杀，须要会杀" | `_check_formation()` 杀局检测 |
| 命逢根气破格 | 渊海子平"命逢根气，命殒无猜" | `_check_dm_root_in_branches()` |
| 从儿须财星承接 | 滴天髓"只要吾儿又得儿" | 财星≥1 检查 |

### 建禄/羊刃/正格破格检测

| 格局 | 破格类型 | 古籍依据 |
|------|---------|---------|
| 建禄格 | 孤官无辅 | 子平真诠 |
| 羊刃格 | 透刃合煞 | 子平真诠"阳刃露煞，透刃无成" |
| 建禄格 | 会杀为凶 | 神峰通考 |
| 正官格 | 伤官见官 | 子平真诠+神峰通考 |
| 财格 | 比劫争财 | 子平真诠 |
| 印格 | 财星破印 | 子平真诠 |
| 食神格 | 枭神夺食 | 子平真诠 |
| 伤官格 | 伤官见官（金水伤官除外） | 子平真诠+神峰通考 |

---

## 多流派分析路径 (v5.2 典籍对齐版)

三流派并行分析，统一 `SchoolAnalyzer` 基类接口。**v5.2 重大更新**：盲派和新派分析方法论全面对照典籍修正（详见版本历史）。

### 传统子平法 (`ZipingAnalyzer`)

源自《子平真诠》《渊海子平》，以月令取格为核心：
- 格局用神法（六层筛查 + 格局用神优先 + 扶抑用神次之）
- 破格感知用神调整（伤官见官→取印制伤，财星破印→取官通关）
- 大运吉凶判定（生克用神关系）

### 盲派 (`MangpaiAnalyzer`) ✨ v5.2 典籍对齐

源自段建业盲派体系（《盲派初级命理学》《命理珍宝瑰宝50期》），以体用、宾主、做功为核心：

**核心概念**：
- **宾主分析**：年月为宾（外环境），日时为主（内环境）
- **体用分析**（v5.2 修正）：体=比劫/印/食（我的工具），用=财/官/伤（我的目标）
- **做功分析**（6种）：制用（克制）、化用（化泄）、生用（相生）、合用（相合）、**墓用（v5.2 新增）**、**复合（v5.2 新增）**
- **贼神捕神**（v5.2 新增）：体力量 > 用力量×1.5 时判定
- **五党成势**（v5.2 新增）：木火势/金水势/水木势/火燥土势/金湿土势
- **功神/废神**（v5.2 新增）：做功成功的十神为功神，失败或被制的为废神
- 功力评估：高功/中功/低功/无功
- 应期预测：大运/流年引动时机（含"出现为应""反客为主"法则）

### 新派 (`XinpaiAnalyzer`) ✨ v5.2 典籍对齐

源自李涵辰新法（《八字预测真踪》），以用忌神为核心：

**核心概念**：
- **用忌神判定**（v5.2 改进）：综合月令+四柱帮扶/克泄力量对比，可判定扶抑格/从强格/从弱格
- **百神论**（v5.2 修正）：动态查找缺失六亲十神→月干优先替代、时干次之（删除硬编码位置映射）
- **空亡论**（v5.2 完善）：六甲旬空亡查表 + **出空机制**（冲出空/合出空检测）
- **反断论**（v5.2 修正）：
  - 删除错误的"月令同五行→互换"和"空亡→互换"条件
  - 正确规则：同五行两天干→时干反断 + 月时同宗（丙戊/丁己/庚壬/辛癸）→反断
- **格局分类**（v5.2 新增）：扶抑格/从强格/从弱格（返回 `geju_type` 字段）
- 大运吉凶判定（v5.2 改进）：综合十神+空亡/出空+反断判定

### API 接口

```python
from bazi_pro.core.schools import school_analyze

# 单流派分析
result = school_analyze(mcp_json, school='ziping')    # 传统子平法
result = school_analyze(mcp_json, school='mangpai')   # 盲派
result = school_analyze(mcp_json, school='xinpai')    # 新派

# 全流派对比
results = school_analyze(mcp_json, school='all')
```

```bash
# REST API
POST /api/v2/analyze?school=ziping          # 指定流派分析
POST /api/v2/analyze/compare                # 三流派对比分析
```

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
- **流派选择下拉框**（传统子平/盲派/新派/全流派对比）
- **全流派对比面板**（三列并排：子平/盲派/新派）
- **方局信息 + 破格条件**显示

**后端** (`server/`): FastAPI + SSE + SQLite
- `POST /api/v2/analyze` — 提交分析，支持 `school` 参数（默认 ziping）
- `POST /api/v2/analyze/compare` — 三流派对比分析
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
| 破格检测 | `bazi_pro.core.patterns` | 专旺/化气/从格/建禄/羊刃/正格破格 |
| 喜用神推导 | `bazi_pro.core.yongshen.derive_yongshen` | 格局感知，含喜/忌/闲神 |
| 刑冲合害 | `bazi_pro.core.relations.detect_relations` | 三合/六合/三刑/冲/害/暗合/半合 |
| 格局之病 | `bazi_pro.core.disease.detect_disease` | 5 类病症检测 + 药方建议 |
| 调候用神 | `bazi_pro.core.tiaohou.lookup_tiaohou` | 穷通宝鉴 120 条查表 |
| 古籍检索 | `bazi_pro.retrieve_classical.retrieve` | BM25 + 反证通道 |
| 消费级报告 | `bazi_pro.ui.consumer_report` | 六维叙事 + 术语解释 + 暗色模式 |
| 子平法分析 | `bazi_pro.core.schools.ziping` | 格局用神法 + 破格感知用神调整 |
| 盲派分析 | `bazi_pro.core.schools.mangpai` | 宾主/6种做功/体用/功力/应期/贼神捕神/五党成势/墓用复合（典籍对齐） |
| 新派分析 | `bazi_pro.core.schools.xinpai` | 百神论/空亡论(含出空)/反断论(同宗对)/格局分类(扶抑从强从弱)（典籍对齐） |
| 507 Golden Cases | `tests/run_golden.py` | 507/507 通过 |

> **格局筛查说明**：六层算法覆盖化气格、专旺格、从格（从强/从财/从官杀/从儿）、建禄月劫格、正格月令透干、暗格。所有格局判定严格对齐古籍原文，含方局/月令/破格检测。调候用神已编码为确定性查表（穷通宝鉴 120 条）。
>
> **Golden Cases 说明**：覆盖十神推导、旺衰判定、格局筛查、喜用神推导、刑冲合害、古籍对齐等确定性规则的边界情况。不覆盖命理争议点。

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
| `BAZI_PORT` | `8711` | 服务监听端口 |
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
| `bazi_pro/core/patterns.py` | 六层格局筛查 + 破格检测 | 方局/月令/争合妒合/命逢根气/伤官见官 |
| `bazi_pro/core/schools/` | 多流派分析路径 | 子平/盲派/新派 + 统一注册接口 |
| `bazi_pro/retrieve_classical.py` | BM25+古籍检索 | pickle 缓存 · `--batch` 批量 · JSON 元数据 |
| `bazi_pro/narrator.py` | 确定性叙述器 | 9 维度中文文本 · 零 LLM · 命理师风格 |
| `bazi_pro/hybrid_search.py` | 融合检索 | BM25+向量+权威权重 · 匹配词高亮 · CLI 入口 |
| `bazi_pro/generate_report.py` | 报告生成 | Markdown/HTML/PDF · `--theme dashboard` v5.0 仪表盘 |
| `bazi_pro/ui/` (子包) | 可视化组件 | 动态SVG命盘 · 命运河流时间轴 · 推理图谱 · 裁决印章 |
| `bazi_pro/view_model.py` | 共享数据层 | DashboardVM 统一三种输出形态 |
| `server/` | Web 服务 | FastAPI REST + SSE + WebSocket + SQLite 持久化 + 流派选择 |
| `bazi_pro/tui/` | 交互终端 | Rich 彩色表格 + 进度条 + Tab 补全 REPL |
| `bazi_pro/plugin_api.py` | 插件机制 | on_retrieve / on_evidence / on_render 钩子 |
| `bazi_pro/archive.py` | 档案系统 | SQLite 存储 + 用户反馈校准 |
| `bazi_pro/doctor.py` | 环境诊断 | 16 项检查一键运行 |

---

## 版本历史

| 版本 | 内容 |
|------|------|
| **v5.2** | **典籍对齐版**：盲派 7 项方法论修正（体用定义修正/墓用复合做功/宾主细致化/贼神捕神检测/功神废神判定/五党成势/应期法则完善）· 新派 6 项方法论修正（反断论同宗对规则/百神论动态查找/身旺身弱综合判定/格局分类扶抑从强从弱/空亡出空机制/大运吉凶综合判定）· 对照典籍：段建业《盲派初级命理学》《命理珍宝瑰宝50期》、李涵辰《八字预测真踪》· Golden Cases 从 103 扩展至 507 |
| **v5.1** | 古籍对齐引擎：专旺格（方局+月令+破格）、化气格（月令+根局+争合妒合）、从格（会财会杀+根气+从儿格）、建禄/羊刃/正格破格检测 · 多流派分析路径：传统子平法（格局用神+破格感知）、盲派（宾主/做功/体用/功力/应期）、新派（百神论/空亡论/反断论） · 流派选择API + 前端对比面板 · 103 Golden Cases |
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
