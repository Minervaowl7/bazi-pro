# bazi-pro v5.0

[![CI](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/Minervaowl7/bazi-pro/actions/workflows/ci.yml)

**可审计、可交互、可视化的八字命理分析引擎（Beta）**

📜 2964 条古籍条文 · 6 部经典 · BM25+Hybrid 检索 · 四层喜用神裁决 · 六层格局筛查 · 动态 SVG 命盘 · FastAPI 服务 · 插件机制

---

## 30秒体验

```bash
git clone git@github.com:Minervaowl7/bazi-pro.git
cd bazi-pro
pip install -r requirements.txt

# 检索古籍
python scripts/retrieve_classical.py "食神 制杀 身弱" -k 3 --json

# 生成报告（Markdown）
python scripts/generate_report.py --input examples/sample_analysis.md --output report.md

# 交互式仪表盘
python scripts/generate_report.py --input examples/sample_analysis.md --theme dashboard --format html --output dashboard.html

# 环境诊断
python scripts/doctor.py
```

---

## 引擎架构

```
命盘 MCP JSON
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
│  解读引擎层 (SKILL.md 10步执行流)                │
│  六层格局筛查 → 四层喜用神裁决 → 九步分析        │
│  evidence.py · trace.py · view_model.py          │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  输出与可视化层                                   │
│  generate_report.py (MD/HTML/PDF)                │
│  ui/ 子包 (SVG命盘 · 命运河流 · 推理图谱)         │
│  server/ (FastAPI) · tui/ (Rich 终端)            │
└─────────────────────────────────────────────────┘
```

⚠️ 本项目处于 Beta 阶段，确定性计算核心已实现但仍在持续完善中。compare_engine 和 liunian_sandbox 标记为 EXPERIMENTAL。

---

## 核心模块

| 模块 | 功能 | 亮点 |
|------|------|------|
| `bazi_pro/retrieve_classical.py` | BM25+古籍检索 | pickle 缓存 · `--batch` 批量 · JSON 元数据 |
| `bazi_pro/hybrid_search.py` | 融合检索 | BM25+向量+权威权重 · 匹配词高亮 · CLI 入口 |
| `bazi_pro/generate_report.py` | 报告生成 | Markdown/HTML/PDF · `--theme dashboard` v5.0 仪表盘 |
| `bazi_pro/ui/` (子包) | 可视化组件 | 动态SVG命盘 · 命运河流时间轴 · 推理图谱 · 裁决印章 |
| `bazi_pro/view_model.py` | 共享数据层 | DashboardVM 统一三种输出形态 |
| `server/` | Web 服务 | FastAPI REST + WebSocket 进度推送 + Redis/LRU 缓存 |
| `bazi_pro/tui/` | 交互终端 | Rich 彩色表格 + 进度条 + Tab 补全 REPL |
| `bazi_pro/plugin_api.py` | 插件机制 | on_retrieve / on_evidence / on_render 钩子 |
| `bazi_pro/archive.py` | 档案系统 | SQLite 存储 + 用户反馈校准 |
| `bazi_pro/doctor.py` | 环境诊断 | 9 项检查一键运行 |

---

## 版本历史

| 版本 | 内容 |
|------|------|
| **v5.0** | 确定性计算核心 (core/) · 72 Golden Cases · Pydantic API Schema · CORS/安全加固 · counter_evidence 通道 |
| **v5.0** | 插件机制 · CLI TUI · AnalysisEngine SDK · 流年沙盒 · 命盘对比 · 档案校准系统 |
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

```bash
pip install jieba                       # 核心（必须）

# 可选
pip install markdown                    # Markdown→HTML 增强
pip install weasyprint                  # PDF 生成
pip install sentence-transformers faiss-cpu numpy  # Hybrid Search
```

---

## 许可

MIT License — 仅供传统文化学习与参考，不构成决策依据。
