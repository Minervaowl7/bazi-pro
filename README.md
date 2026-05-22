# bazi-pro v4.2

**可审计、可交互、可视化的八字命理分析引擎**

📜 2964 条古籍条文 · 6 部经典 · BM25+Hybrid 检索 · 四层喜用神裁决 · 六层格局筛查 · 交互式仪表盘

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
│  retrieve_classical.py                          │
│  BM25 (cache) + Hybrid Search (vector)          │
│  双通道反事实检索 → 16 条古籍证据               │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  bazi-pro SKILL.md (解读引擎)                   │
│  六层格局筛查 → 四层喜用神裁决 → 九步分析        │
│  evidence.py → 结构化证据链 JSON                 │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  generate_report.py + dashboard.py              │
│  Markdown / HTML / PDF / 交互式仪表盘            │
│  五行雷达图 · 大运时间轴 · 暗色/亮色主题         │
└─────────────────────────────────────────────────┘
```

---

## 核心模块

| 模块 | 功能 | 亮点 |
|------|------|------|
| `scripts/retrieve_classical.py` | BM25+古籍检索 | pickle 缓存 (3.6x) · `--batch` 批量 · JSON 性能元数据 |
| `scripts/generate_report.py` | 报告生成 | Markdown/HTML/PDF · `--theme dashboard` 仪表盘 |
| `scripts/dashboard.py` | 交互式仪表盘 | SVG 雷达图 · 评分色环 · 大运时间轴 · 五行着色 |
| `scripts/evidence.py` | 证据链对象 | claim + confidence + basis.classics + counter |
| `scripts/hybrid_search.py` | 融合检索 | BM25+向量+权威权重，缺依赖自动降级 |
| `scripts/doctor.py` | 环境诊断 | `python scripts/doctor.py` 一键检查 |

---

## 版本历史

| 版本 | 内容 |
|------|------|
| **v4.2** | Golden Cases (4例) + CI + Web Demo 首页 + Evidence Pipeline + 包结构重构 |
| **v4.1** | bazi doctor · pyproject 包结构修复 · README 引擎化 · 检索性能元数据 |
| **v4.0** | Evidence Object · BM25缓存 · 批量检索 · Hybrid Search骨架 · examples |
| **v3.5** | 层3比劫拦截 (禁止"暗劫财格"→建禄月劫经典框架) · 强制自动生成报告 · 交互式仪表盘 |
| **v3.4** | 报告生成器跨平台字体 · 调候双通道 · 病药突破大运上限 |

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
