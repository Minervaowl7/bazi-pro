# bazi-pro Code Wiki

> 项目：bazi-pro v5.0.0 — 可审计、可交互、可视化的八字命理分析引擎
> 文档生成时间：2026-05-27

---

## 目录

1. [项目概览](#1-项目概览)
2. [整体架构](#2-整体架构)
3. [模块职责与文件映射](#3-模块职责与文件映射)
4. [核心计算引擎详解](#4-核心计算引擎详解)
5. [叙述器与检索系统](#5-叙述器与检索系统)
6. [Web 后端架构](#6-web-后端架构)
7. [前端应用架构](#7-前端应用架构)
8. [ViewModel 与 UI 渲染](#8-viewmodel-与-ui-渲染)
9. [插件系统](#9-插件系统)
10. [数据流与执行流程](#10-数据流与执行流程)
11. [依赖关系](#11-依赖关系)
12. [项目运行方式](#12-项目运行方式)
13. [测试与质量保障](#13-测试与质量保障)
14. [环境变量与配置](#14-环境变量与配置)
15. [关键约束与设计原则](#15-关键约束与设计原则)
16. [附录：完整文件清单](#16-附录完整文件清单)

---

## 1. 项目概览

| 属性 | 说明 |
|------|------|
| **项目名称** | bazi-pro |
| **版本** | v5.0.0 |
| **定位** | 确定性八字命理计算引擎 + LLM 解读框架 + Web 应用 |
| **核心原则** | **算析分离** — `bazi_pro/core/` 做所有确定性命理计算，LLM 只负责解读，不参与计算 |
| **核心能力** | BM25+Hybrid 古籍检索、六层格局筛查、四层喜用神裁决、格局之病检测、调候用神查表、确定性叙述器、交互式仪表盘、证据链输出 |
| **语料规模** | 2964 条古籍条文，6 部经典，约 29.8 万字 |
| **Python 版本** | >= 3.10 |
| **许可证** | MIT |

### 1.1 设计哲学

- **算析分离**：`bazi_pro/core/` 做所有确定性计算（十神、藏干、五行力量、旺衰、格局、喜用神、刑冲合害），LLM 只负责解读
- **无伪造引用**：每条古籍引用必须来自 `retrieve_classical.py` 输出
- **无 LLM 占位符**：模式名称、旺衰裁决和用神值绝不含"待LLM分析"等占位符
- **线性执行流**：Step 0 → 1 → 2 → ... → 9 → [可选] 10，无回填循环
- **伦理优先**：健康、财务、婚姻等话题使用文化参考措辞，不做确定性预测

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         输入层 (Input)                               │
│  Bazi MCP JSON  ──►  字段校验与降级  ──►  统一字段识别               │
│  (validation.py)                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│               确定性计算核心 (bazi_pro/core/)                        │
│  full_analysis() → dict                                              │
│  ├─ constants.py  — 天干地支映射、十神推导                           │
│  ├─ stems.py      — 天干五合、五行生克映射                           │
│  ├─ branches.py   — 地支藏干、十二长生、刑冲合害关系表               │
│  ├─ hidden_stems.py — 藏干展开                                      │
│  ├─ ten_gods.py   — 十神关系、旺衰方向辅助                           │
│  ├─ strength.py   — 得令/得地/得势 + 旺衰综合判定                    │
│  ├─ elements.py   — 五行力量计算（含合化动态修正）                   │
│  ├─ patterns.py   — 六层格局筛查                                    │
│  ├─ yongshen.py   — 四层喜用神推导                                  │
│  ├─ relations.py  — 刑冲合害检测 + 十神关系检测                      │
│  ├─ disease.py    — 格局之病检测（5类）                              │
│  └─ tiaohou.py    — 调候用神查表（穷通宝鉴 120 条）                  │
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
│                      叙述器 (narrator.py)                            │
│  narrate_analysis() → 9 维度中文文本（旺衰/格局/用神/调候/五行/       │
│  刑冲/性格/事业/引用），零 LLM 依赖，每句话锚定在确定性数据上        │
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
│  ui/consumer_report.py ──► 消费级报告（六维叙事 + 术语解释）         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Web 服务层                                      │
│  FastAPI Server (server/)  ──►  REST + SSE + WebSocket + SQLite     │
│  Next.js Frontend (frontend/) ──►  暗色主题 Web 应用               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 四层代码组织

| 层级 | 目录 | 职责 |
|------|------|------|
| **核心层** | `bazi_pro/core/` | 确定性命理计算引擎，13 个模块，纯数据变换 |
| **包层** | `bazi_pro/` | 检索、叙述、报告、证据链、ViewModel、插件 API |
| **服务层** | `server/` | FastAPI 后端，REST + SSE + WebSocket |
| **前端层** | `frontend/` | Next.js 14 App Router + TypeScript + Tailwind CSS |

---

## 3. 模块职责与文件映射

### 3.1 确定性计算核心 (`bazi_pro/core/`)

| 文件 | 职责 | 核心导出 |
|------|------|----------|
| `__init__.py` | 主入口 + 全部 re-export | `full_analysis()` |
| `constants.py` | 权威常量映射 | `GAN_WUXING`, `ZHI_WUXING`, `WUXING_TO_GAN`, `GAN_SHISHEN_MAP`, `derive_shishen()` |
| `stems.py` | 天干五合、五行生克映射 | `GAN_HE`, `WUXING_SHENG`, `WUXING_KE`, `SHENG_MAP`, `KE_MAP`, `WO_KE_MAP`, `WO_SHENG_MAP` |
| `branches.py` | 地支藏干、十二长生、刑冲合害关系表 | `ZHI_CANGGAN`, `CANGGAN_WEIGHT`, `SHIER_CHANGSHENG`, `DELING_SCORE`, `ZHI_HE/CHONG/HAI/XING/SANHE/SANXING/BANHE/HUIFANG`, `JIANLU_MAP`, `YANGREN_MAP` |
| `hidden_stems.py` | 藏干展开 | `get_canggan()` |
| `ten_gods.py` | 十神关系、旺衰方向辅助 | `SHISHEN_WUXING_REL`, `_count_shishen_categories()`, `_get_yongshen_direction()` |
| `strength.py` | 得令/得地/得势 + 旺衰综合判定 | `calc_deling()`, `calc_dedi()`, `calc_deshi()`, `judge_wangshuai()` |
| `elements.py` | 五行力量计算（含合化动态修正） | `calc_element_forces()` |
| `patterns.py` | 六层格局筛查 | `screen_pattern()`, `PATTERN_YONGSHEN`, `_screen_layer0/1/2/3()`, `_finalize_pattern()` |
| `yongshen.py` | 四层喜用神推导 | `derive_yongshen()`, `_pattern_yongshen_wx()` |
| `relations.py` | 刑冲合害检测 + 十神关系检测 | `detect_relations()`, `detect_shishen_relations()` |
| `disease.py` | 格局之病检测（5类） | `detect_disease()` |
| `tiaohou.py` | 调候用神查表（穷通宝鉴 120 条） | `lookup_tiaohou()`, `TIAOHOU_TABLE` |

### 3.2 包层模块 (`bazi_pro/`)

| 文件 | 职责 | CLI 入口 |
|------|------|----------|
| `__init__.py` | SDK 入口，`AnalysisEngine` 类 | — |
| `retrieve_classical.py` | BM25 + jieba 古籍检索 | `bazi-retrieve` |
| `hybrid_search.py` | 融合检索骨架（BM25 + 向量 + 权威权重） | `bazi-hybrid` |
| `narrator.py` | 确定性叙述器（9 维度中文文本生成） | — |
| `generate_report.py` | 报告生成器（Markdown/HTML/PDF） | `bazi-report` |
| `dashboard.py` | 交互式仪表盘（SVG 五行雷达图等） | — |
| `evidence.py` | 证据链对象 | `bazi-evidence` |
| `trace.py` | 分析追踪（TraceBuilder） | `bazi-trace` |
| `view_model.py` | 共享数据层（DashboardVM 等 dataclass） | — |
| `validation.py` | 输入校验 | — |
| `doctor.py` | 环境诊断 | `bazi-doctor` |
| `plugin_api.py` | 插件抽象基类 + 注册机制 | — |
| `core_rules.py` | 向后兼容代理（触发 DeprecationWarning） | — |
| `compare_engine.py` | 命盘对比引擎 | — |
| `calibration.py` | 历史校准 | — |
| `liunian_sandbox.py` | 流年沙盘 | — |
| `archive.py` | 归档工具 | — |

### 3.3 UI 子包 (`bazi_pro/ui/`)

| 文件 | 职责 |
|------|------|
| `report.py` | 咨询报告渲染：封面 → Executive Summary → 裁决表 → 风险建议 → 正文 → 附录 |
| `replay.py` | 裁决回放渲染：三栏布局（推理步骤导航 / 步骤详情 / 主张与反证） |
| `consumer_report.py` | 消费级报告：六维叙事 + 术语解释 |
| `report_composer.py` | Markdown → 结构化报告文档：技术章节自动归类到 Appendix |
| `text_cleaner.py` | 统一输出编辑层：去 Markdown 残留、括号闭合、label/note 拆分 |
| `verdict_seal.py` | 命理裁决朱砂印章 SVG |
| `pillar_chart.py` | 四柱命盘 SVG 图表 |
| `reasoning_graph.py` | 推理图谱可视化 |
| `timeline_river.py` | 命运河流时间轴 |
| `classics_viewer.py` | 古典文献查看器 |
| `compare_view.py` | 对比视图 |
| `glossary.py` | 术语表 |
| `sandbox_ui.py` | 沙盘 UI |

### 3.4 Web 后端 (`server/`)

| 文件 | 职责 |
|------|------|
| `app.py` | FastAPI 应用主入口，路由定义，中间件配置 |
| `analysis.py` | 异步分析编排，调用 core 模块 |
| `db.py` | SQLite 存储层（aiosqlite），分析记录 + 聊天历史持久化 |
| `schemas.py` | Pydantic 请求/响应模型定义 |
| `cache.py` | 缓存层（Redis 优先，降级为内存 LRU） |
| `ratelimiter.py` | 限流器（Redis 优先，降级为内存滑动窗口） |
| `taskstore.py` | 任务存储（Redis 优先，降级为内存 dict） |
| `ws.py` | WebSocket 连接管理器 |

### 3.5 前端 (`frontend/`)

| 文件/目录 | 职责 |
|-----------|------|
| `src/app/page.tsx` | 首页（出生信息表单） |
| `src/app/analyze/[id]/page.tsx` | 分析结果页 |
| `src/app/layout.tsx` | 根布局 |
| `src/components/BirthForm.tsx` | 出生信息表单组件 |
| `src/components/BaziChartCard.tsx` | 八字命盘卡片 |
| `src/components/AnalysisProgress.tsx` | 分析进度组件 |
| `src/components/DayunTimeline.tsx` | 大运时间轴 |
| `src/components/SchoolPanel.tsx` | 学派面板 |
| `src/components/HistorySidebar.tsx` | 历史记录侧边栏 |
| `src/lib/api.ts` | API 通信层 |
| `src/stores/analysisStore.ts` | Zustand 状态管理 |

### 3.6 插件 (`plugins/`)

| 目录 | 职责 |
|------|------|
| `loader.py` | 插件发现与加载（目录扫描 + entry_points） |
| `examples/english/` | 英文翻译插件示例 |
| `examples/fengshui/` | 风水分析插件示例 |
| `examples/tarot/` | 塔罗关联插件示例 |

### 3.7 脚本兼容层 (`scripts/`)

`scripts/` 下各文件为 `bazi_pro/` 对应模块的轻量 wrapper，保持向后兼容。所有脚本使用 `sys.exit(main())` 传播退出码。

| 脚本 | 包模块 | 说明 |
|------|--------|------|
| `retrieve_classical.py` | `bazi_pro.retrieve_classical` | 古籍检索 CLI |
| `generate_report.py` | `bazi_pro.generate_report` | 报告生成 CLI |
| `dashboard.py` | `bazi_pro.dashboard` | 仪表盘 CLI |
| `evidence.py` | `bazi_pro.evidence` | 证据链 CLI |
| `hybrid_search.py` | `bazi_pro.hybrid_search` | 融合检索 CLI |
| `doctor.py` | `bazi_pro.doctor` | 环境诊断 CLI |
| `audit_all.py` | — | 全量审计 |
| `audit_data_tables.py` | — | 数据表审计 |
| `audit_golden_cases.py` | — | Golden Case 审计 |
| `audit_logic_chain.py` | — | 逻辑链审计 |
| `check_version_consistency.py` | — | 版本一致性检查 |
| `validate_pattern_rules.py` | — | 格局规则验证 |

---

## 4. 核心计算引擎详解

### 4.1 `full_analysis()` — 核心主入口

**位置**: [bazi_pro/core/__init__.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/__init__.py#L57)

**签名**:
```python
def full_analysis(mcp_json: dict) -> dict
```

**执行流程**:
1. 输入校验 → `validate_bazi_input()`
2. 得令计算 → `calc_deling(day_master, month_zhi)`
3. 得地计算 → `calc_dedi(day_master, bazi_parts)`
4. 得势计算 → `calc_deshi(day_master, bazi_parts)`
5. 旺衰判定 → `judge_wangshuai(deling_score, dedi_score, deshi_score)`
6. 五行力量 → `calc_element_forces(bazi_parts, month_zhi)`
7. 刑冲合害 → `detect_relations(bazi_parts)` + `detect_shishen_relations(day_master, bazi_parts)` → 合并去重
8. 格局筛查 → `screen_pattern(day_master, bazi_parts, wangshuai, element_forces)`
9. 喜用神推导 → `derive_yongshen(day_master, bazi_parts, pattern, wangshuai, element_forces)`
10. 格局之病 → `detect_disease(day_master, bazi_parts, element_forces)`
11. 调候查表 → `lookup_tiaohou(day_master, month_zhi)`
12. 病源补充忌神 → 将疾病源的五行加入忌神列表
13. 构建四柱详情 → 含天干、地支、五行、十神、藏干

**返回结构**:
```python
{
    'status': 'completed',
    'day_master': str,
    'deling': {'status': str, 'score': int},
    'dedi': {'score': float, 'details': list, 'level': str},
    'deshi': {'score': float, 'details': list, 'level': str},
    'wangshuai': {
        'verdict': str,           # 极旺/身旺/偏旺/中和偏旺/中和/中和偏弱/身弱/极弱
        'deling_score': int,
        'dedi_score': float,
        'deshi_score': float,
        'is_weak': bool,
        'is_strong': bool,
        'is_extreme_weak': bool,
        'is_extreme_strong': bool,
    },
    'element_forces': {
        'raw': dict,              # 原始五行力量
        'percent': dict,          # 原始百分比
        'percent_adjusted': dict, # 合化修正后百分比
        'total': float,
        'hehua': dict,            # 合化详情
    },
    'relations': list[dict],      # 刑冲合害 + 十神关系
    'pattern': {
        'pattern': str,           # 格局名称
        'layer': int,             # 命中层级 (0-3)
        'type': str,              # 格局类型
        'confidence': float,      # 置信度
        'reason': str,            # 判定依据
        'yongshen_direction': str,# 用神方向
        'candidates': list,
        'trace': dict,            # 各层筛查轨迹
    },
    'yongshen': {
        'yongshen': str,          # 用神五行
        'yongshen_gan': str,      # 用神天干
        'xishen': list[str],      # 喜神五行
        'xishen_gan': list[str],
        'jishen': list[str],      # 忌神五行
        'jishen_gan': list[str],
        'confidence': float,
        'pattern_basis': str,
        'trace': dict,
    },
    'disease': {
        'has_disease': bool,
        'items': list[dict],      # 病项列表
        'medicine_advice': str,   # 药方建议
    },
    'tiaohou': {
        'has_tiaohou': bool,
        'tiaohou_gan': list[str], # 调候用神天干
        'tiaohou_wx': list[str],  # 调候用神五行
        'note': str,
    },
    'pillars': list[dict],        # 四柱详情
}
```

### 4.2 旺衰判定 (`strength.py`)

**位置**: [bazi_pro/core/strength.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/strength.py)

#### `calc_deling(day_master, month_zhi) → (status, score)`

- 查 `SHIER_CHANGSHENG[日主][月支]` 得十二长生状态
- 查 `DELING_SCORE[状态]` 得分数（帝旺/临官=+3, 长生=+2, 死=-2, 绝=-3 等）

#### `calc_dedi(day_master, bazi_parts) → {score, details, level}`

- 遍历四柱地支藏干，统计与日主同五行的藏干权重
- 本气=1.0, 中气=0.6, 余气=0.3
- 得地等级：≥3=得地, ≥1.5=偏得地, <1.5=不得地

#### `calc_deshi(day_master, bazi_parts) → {score, details, level}`

- 天干：比肩/劫财/正印/偏印，距离日柱≤1得2分，否则1分
- 藏干：本气比劫/印星得1分
- 得势等级：≥4=得势, ≥2=偏得势, <2=不得势

#### `judge_wangshuai(deling_score, dedi_score, deshi_score) → dict`

- **极旺**：得令≥3 且 得地≥3 且 得势≥6
- **极弱**：得令≤-2 且 得地<1.5 且 得势≤1
- **身旺**：得令≥2 且 得地≥3 且 得势≥4
- **身弱**：得令≤0 且 得地<1.5 且 得势<2
- **中和**：其他组合
- **关键约束**：极旺/极弱必须在身旺/身弱之前检查，防止遮蔽

### 4.3 五行力量计算 (`elements.py`)

**位置**: [bazi_pro/core/elements.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/elements.py)

#### `calc_element_forces(bazi_parts, month_zhi) → dict`

**基础力量计算**:
- 天干：有根（本气/中气藏干同五行）=1.2，无根=0.5
- 藏干：按 `CANGGAN_WEIGHT` 加权（本气=1.0, 中气=0.6, 余气=0.3）
- 月支本气权重 ×1.5

**合化动态修正**:
- 天干合化：原五行力量转50%入化神
- 地支三合局：原五行力量转50%入化神
- 半合局：转化率20%
- 会方：加成30%

**返回两组百分比**:
- `percent`：原始百分比（格局筛查使用）
- `percent_adjusted`：合化修正后百分比（化气格使用）

### 4.4 六层格局筛查 (`patterns.py`)

**位置**: [bazi_pro/core/patterns.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/patterns.py)

#### `screen_pattern(day_master, bazi_parts, wangshuai, element_forces) → dict`

筛查顺序（逐层短路）：

| 层级 | 函数 | 格局类型 | 说明 |
|------|------|----------|------|
| L0 | `_screen_layer0()` | 化气格、专旺格、从强格、假从强格、从财格、从官杀格、从儿格、从势格、两行成象格 | 特殊格局 |
| L1 | `_screen_layer1()` | 月令本气透干格 | 正格第一层 |
| L2 | `_screen_layer2()` | 月令中气透干格 | 正格第二层 |
| L3 | `_screen_layer3()` | 暗格、建禄月劫格、羊刃格 | 正格第三层 |

**L0 特殊格局判定逻辑**:
- 化气格：日主参与天干合化，化神修正后占比≥60%
- 专旺格：日主五行占比≥80%（曲直/炎上/稼穑/从革/润下）
- 从强格：印比≥80%，日主极旺且地支无本气根
- 从财/从官杀/从儿/从势：日主极弱，克泄耗成势，无比劫印星

**建禄月劫格特殊处理**:
- 月令本气为比劫时，走 `_build_jianlu_yuejie()` 构建
- 输出格式为"建禄格，透X"而非"比肩格"
- 用神由"透X"决定，不是盲取 `PATTERN_YONGSHEN` 表

### 4.5 喜用神推导 (`yongshen.py`)

**位置**: [bazi_pro/core/yongshen.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/yongshen.py)

#### `derive_yongshen(day_master, bazi_parts, pattern_result, wangshuai, element_forces) → dict`

**四层裁决架构**:
1. **格局用神**：从 `PATTERN_YONGSHEN` 表和格局名称推导
2. **旺衰扶抑**：身弱取印星，身强取克泄
3. **忌神推导**：从格忌逆势五行，扶抑格忌克泄/印比
4. **喜神推导**：从格局用神表第二候选或通用逻辑

**从格用神方向**:
- 从强/专旺 → 印比
- 从财 → 食伤生财
- 从官杀 → 财生官
- 从儿 → 食伤生财

### 4.6 格局之病检测 (`disease.py`)

**位置**: [bazi_pro/core/disease.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/disease.py)

#### `detect_disease(day_master, bazi_parts, element_forces) → dict`

检测 5 类格局之病：

| 病名 | 检测条件 | 药方 |
|------|----------|------|
| 枭神夺食 | 偏印有根 + 食神有根 | 财星制枭 |
| 食神制杀逢枭 | 同上 + 七杀有根 | 财星制枭 |
| 伤官见官 | 伤官有根 + 正官有根，无财星通关，无印星制化 | 印星化伤官 |
| 比劫争财 | 比劫旺(≥2透干或有本气根) + 财星无强根 | 官杀制比劫 |
| 官杀混杂 | 正官有根 + 七杀有根，无食伤制化，无印星化杀 | 食伤制杀 |

每项病含：`severity`(active/potential)、`disease_god`、`affected_god`、`medicine`、`reason`

### 4.7 刑冲合害检测 (`relations.py`)

**位置**: [bazi_pro/core/relations.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/relations.py)

#### `detect_relations(bazi_parts) → list[dict]`

检测干支层面的物理关系：
- 天干合（5 组）
- 地支冲（6 组）
- 地支合（6 组）
- 地支害（6 组）
- 地支刑（11 组，含自刑）
- 三合局（4 组）
- 半合局（8 组，三合局成立时排除子集）
- 会方（4 组）
- 三刑（2 组：寅巳申、丑未戌）

#### `detect_shishen_relations(day_master, bazi_parts) → list[dict]`

检测十神层面的逻辑关系：
- 枭神夺食
- 伤官见官（需无财星通关、无印星制化）
- 财破印（需无官杀通关）
- 食神制杀
- 官杀混杂（需无食伤制化、无印星化杀）

### 4.8 调候用神 (`tiaohou.py`)

**位置**: [bazi_pro/core/tiaohou.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/core/tiaohou.py)

#### `lookup_tiaohou(day_master, month_zhi) → dict`

- 基于 `TIAOHOU_TABLE`（10 天干 × 12 月支 = 120 条）
- 数据来源：《穷通宝鉴》原文逐月提取
- 返回主调候天干 + 辅调候天干
- 调候是辅助参考，不凌驾于格局用神之上

---

## 5. 叙述器与检索系统

### 5.1 确定性叙述器 (`narrator.py`)

**位置**: [bazi_pro/narrator.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/narrator.py)

#### `narrate_analysis(result) → dict`

从完整分析结果生成 9 维度专业中文文本，零 LLM 依赖：

| 维度 | 函数 | 内容 |
|------|------|------|
| `overview` | `_narrate_overview()` | 命局总览（2-3句） |
| `strength` | `_narrate_strength()` | 旺衰分析（得令/得地/得势 + 综合判定） |
| `pattern` | `_narrate_pattern()` | 格局判定（层级 + 置信度 + 依据） |
| `yongshen` | `_narrate_yongshen()` | 喜用神（推导方法 + 用神/喜神/忌神 + 实用建议） |
| `tiaohou` | `_narrate_tiaohou()` | 调候分析（穷通宝鉴 + 命局有无调候干） |
| `elements` | `_narrate_elements()` | 五行分析（力量分布 + 偏旺/极弱提示） |
| `relations` | `_narrate_relations()` | 刑冲合害（逐条描述 + 影响） |
| `personality` | `_narrate_personality()` | 性格推断（五行本性 + 旺衰影响 + 格局倾向） |
| `career` | `_narrate_career()` | 事业方向（用神行业 + 格局适合岗位） |
| `citations` | `_extract_citations()` | 引用的古籍条文（前5条） |

### 5.2 古籍检索 (`retrieve_classical.py`)

#### `BM25` 类

标准 Okapi BM25 实现，参数 k1=1.5, b=0.75。支持 pickle 序列化缓存。

#### `retrieve(corpus_path, query_str, k=8, force_rebuild=False) → dict`

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

**缓存机制**:
- 缓存目录：`.cache/`
- 缓存键：语料文件路径 + mtime + size 的 MD5 前 12 位
- 冷启动构建索引约 1.8s，热查询毫秒级

### 5.3 融合检索 (`hybrid_search.py`)

#### `HybridSearcher` 类

融合得分公式：
```
score = 0.55 × BM25_norm + 0.30 × cosine_sim
        + 0.10 × authority(source) + 0.05 × topic_match
```

- 可选依赖缺失时自动降级为纯 BM25
- 权威权重表 `CLASSICAL_AUTHORITY`：子平真诠/滴天髓=1.0，穷通宝鉴=0.95

---

## 6. Web 后端架构

### 6.1 FastAPI 应用 (`server/app.py`)

**位置**: [server/app.py](file:///c:/Users/李云龙/Desktop/bazi-pro/server/app.py)

#### 中间件栈（执行顺序）

1. `_SecurityHeadersMiddleware` — 安全响应头（X-Content-Type-Options, X-Frame-Options, CSP 等）
2. `_RequestSizeLimitMiddleware` — 请求体大小限制（默认 10KB）
3. `_RateLimitMiddleware` — 限流（默认 30次/60秒）
4. `TrustedHostMiddleware` — 可选，受信主机检查
5. `CORSMiddleware` — CORS（默认允许 localhost:3000）

#### API 路由

**V1 路由（WebSocket 推送）**:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 提交分析任务，返回 run_id |
| GET | `/api/status/{run_id}` | 查询分析进度 |
| GET | `/api/result/{run_id}` | 获取分析结果 |
| WS | `/ws/{run_id}` | WebSocket 实时进度推送 |
| GET | `/api/health` | 健康检查 |

**V2 路由（SSE 流式 + SQLite 持久化）**:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v2/analyze` | 提交分析，返回 analysis_id + stream_url |
| GET | `/api/v2/analysis/{id}/stream` | SSE 流式进度推送（含缓冲回放） |
| GET | `/api/v2/analysis/{id}` | 获取完整结果 + 叙述器文本 |
| GET | `/api/v2/history` | 历史记录列表（分页） |

**V2 数据流**:
```
POST /api/v2/analyze
  → insert_analysis() → SQLite
  → asyncio.create_task(_background_analyze_v2)
  → 返回 202 + stream_url

_background_analyze_v2
  → SSE broadcast progress events
  → run_analysis() → 核心计算
  → update_analysis_result() → SQLite
  → SSE broadcast done

GET /api/v2/analysis/{id}
  → get_analysis() → SQLite
  → narrate_analysis() → 叙述器
  → 返回 result + narration
```

### 6.2 异步分析编排 (`server/analysis.py`)

**位置**: [server/analysis.py](file:///c:/Users/李云龙/Desktop/bazi-pro/server/analysis.py)

#### `run_analysis(mcp_json, run_id, detail_level) → dict`

异步包装同步核心模块，通过 `asyncio.to_thread()` 执行检索，其余步骤同步调用。

步骤：数据校验 → 古籍检索 → 旺衰判断 → 格局判定 → 十神推导 → 喜用神 → 五行力量 → 刑冲合害

缓存键：`bazi:v5:{sha256(八字+日主+性别+阳历+农历+大运+detail_level)[:24]}`

### 6.3 SQLite 存储层 (`server/db.py`)

**位置**: [server/db.py](file:///c:/Users/李云龙/Desktop/bazi-pro/server/db.py)

**表结构**:

```sql
-- 分析记录
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,           -- ana_{uuid[:12]}
    status TEXT DEFAULT 'processing',
    detail_level TEXT DEFAULT 'standard',
    birth_json TEXT,               -- 输入 JSON
    full_result TEXT,              -- 完整结果 JSON
    created_at TEXT,
    completed_at TEXT,
    duration_ms INTEGER,
    day_master TEXT,
    pattern TEXT,
    yongshen TEXT
);

-- 聊天历史
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id TEXT REFERENCES analyses(id) ON DELETE CASCADE,
    role TEXT,
    content TEXT,
    citations TEXT,
    created_at TEXT
);
```

PRAGMA: `journal_mode=WAL`, `foreign_keys=ON`

### 6.4 请求校验模型 (`server/schemas.py`)

**位置**: [server/schemas.py](file:///c:/Users/李云龙/Desktop/bazi-pro/server/schemas.py)

核心模型：
- `BaziAnalysisRequest` — V1 分析请求（性别、八字、日主、detail_level、大运）
- `BirthAnalyzeRequest` — V2 分析请求（含经纬度字段）
- `BaziPillars` — 四柱校验（天干+地支合法性）
- `DayunItem` — 大运项校验
- 各种响应模型：`WangshuaiResult`, `PatternResult`, `YongshenResult` 等

### 6.5 缓存与限流

**缓存** (`server/cache.py`):
- Redis 优先，降级为内存 LRU（LRUDict，maxsize=128，支持 TTL）
- 环境变量 `REDIS_URL` 控制

**限流** (`server/ratelimiter.py`):
- Redis 优先（ZSET 滑动窗口），降级为内存滑动窗口
- 默认 30 次/60秒
- 环境变量 `BAZI_RATE_LIMIT_REQUESTS`, `BAZI_RATE_LIMIT_WINDOW_SECONDS`

---

## 7. 前端应用架构

### 7.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.2.6 | App Router 框架 |
| React | 19.2.4 | UI 渲染 |
| TypeScript | ^5 | 类型安全 |
| Tailwind CSS | ^4 | 样式 |
| Zustand | ^5.0.13 | 状态管理 |
| ECharts | ^6.1.0 | 图表可视化 |

### 7.2 页面结构

```
src/app/
├── layout.tsx           # 根布局（暗色主题）
├── page.tsx             # 首页（BirthForm）
├── globals.css          # 全局样式
└── analyze/[id]/
    └── page.tsx         # 分析结果页
```

### 7.3 组件结构

| 组件 | 职责 |
|------|------|
| `BirthForm` | 出生信息输入表单（性别、八字、日主等） |
| `BaziChartCard` | 八字命盘卡片展示 |
| `AnalysisProgress` | SSE 分析进度条 |
| `DayunTimeline` | 大运时间轴可视化 |
| `SchoolPanel` | 学派分析面板 |
| `HistorySidebar` | 历史记录侧边栏 |

### 7.4 状态管理

`analysisStore.ts` (Zustand) 管理分析状态：当前分析 ID、结果数据、加载状态等。

### 7.5 API 通信

`api.ts` 封装与后端的通信：
- `NEXT_PUBLIC_API_URL` 环境变量配置后端地址（默认 `http://127.0.0.1:8710`）
- SSE 连接用于实时进度
- REST 调用用于提交分析和获取结果

---

## 8. ViewModel 与 UI 渲染

### 8.1 ViewModel 数据层 (`view_model.py`)

**位置**: [bazi_pro/view_model.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/view_model.py)

核心 dataclass：

| 类 | 职责 | 关键字段 |
|----|------|----------|
| `DashboardVM` | 主数据容器 | pillars, verdict, wuxing, evidence, relations, trace_stages, dayun |
| `PillarVM` | 一柱命盘 | position, gan, zhi, wuxing_gan, wuxing_zhi, shishen, canggan |
| `VerdictVM` | 最终裁决 | day_master, pattern, decision, yongshen, xishen, jishen, confidence |
| `WuxingVM` | 五行力量 | wood, fire, earth, metal, water, roles, interpretations |
| `EvidenceVM` | 单条证据 | stage_id, claim, decision, confidence, rules, classics |
| `RelationVM` | 刑冲合害 | relation_type, from_pillar, to_pillar, description, severity |
| `TraceStageVM` | 推理链一步 | stage_id, title, summary, status, confidence, rules |
| `DayunVM` | 大运 | gan_zhi, age_range, shishen, assessment |

**构建器**:
- `build_vm_from_result_json(json_path)` — 标准路径（v5.0），从 result.json 构建
- `build_vm_from_trace(trace)` — 从 trace.json 构建
- `build_vm_from_analysis_text(text)` — 过渡方案，从 Markdown 文本正则提取

### 8.2 UI 渲染器

所有 UI 组件只接受 `DashboardVM` dataclass，不做正则提取。

| 渲染器 | 输入 | 输出 |
|--------|------|------|
| `dashboard.py` | DashboardVM | 交互式 HTML 仪表盘 |
| `ui/report.py` | DashboardVM | 咨询报告 HTML |
| `ui/replay.py` | DashboardVM | 裁决回放 HTML |
| `ui/consumer_report.py` | DashboardVM | 消费级报告 HTML |
| `ui/verdict_seal.py` | DashboardVM | 裁决印章 SVG |

---

## 9. 插件系统

### 9.1 插件 API (`plugin_api.py`)

**位置**: [bazi_pro/plugin_api.py](file:///c:/Users/李云龙/Desktop/bazi-pro/bazi_pro/plugin_api.py)

#### `BaziPlugin` 抽象基类

```python
class BaziPlugin(ABC):
    name: str = ''
    version: str = '1.0.0'
    description: str = ''
    permissions: list[str] = []

    @abstractmethod
    def on_retrieve(self, query: str, results: list[dict]) -> list[dict]: ...

    @abstractmethod
    def on_evidence(self, evidence: dict) -> dict: ...

    @abstractmethod
    def on_render(self, html: str, vm) -> str: ...
```

**Hook 分类**:
- 只读 Hook：`on_retrieve`, `on_evidence` — 插件返回不同对象时使用原始数据
- 可写 Hook：`on_render` — 允许修改输出，记录修改日志

**注册机制**: `register_plugin()`, `get_plugin()`, `list_plugins()`, `invoke_hook()`

### 9.2 插件加载器 (`plugins/loader.py`)

**位置**: [plugins/loader.py](file:///c:/Users/李云龙/Desktop/bazi-pro/plugins/loader.py)

- 目录扫描：`plugins/` 下每个子目录需含 `plugin.json` + `main.py`
- 路径逃逸检测：验证符号链接不超出插件目录
- 白名单机制：`PLUGIN_WHITELIST` 非空时只加载白名单内插件
- entry_points 发现：也支持 `bazi_pro.plugins` 入口点

---

## 10. 数据流与执行流程

### 10.1 标准分析流程

```
用户输入 (Bazi MCP JSON)
    │
    ▼
Step 0: 输入校验 (validation.py)
    │
    ▼
Step 1: 得令/得地/得势 → 旺衰判定 (strength.py)
    │
    ▼
Step 2: 五行力量计算 + 合化修正 (elements.py)
    │
    ▼
Step 3: 六层格局筛查 (patterns.py)
    ├─ L0: 化气格/专旺格/从格
    ├─ L1: 月令本气透干
    ├─ L2: 月令中气透干
    └─ L3: 暗格/建禄月劫/羊刃
    │
    ▼
Step 4: 四层喜用神推导 (yongshen.py)
    ├─ 格局用神
    ├─ 病药用神
    ├─ 扶抑用神
    └─ 调候用神
    │
    ▼
Step 5: 格局之病检测 (disease.py)
    ├─ 枭神夺食
    ├─ 伤官见官
    ├─ 比劫争财
    └─ 官杀混杂
    │
    ▼
Step 6: 刑冲合害检测 (relations.py)
    ├─ 干支物理关系
    └─ 十神逻辑关系
    │
    ▼
Step 7: 调候用神查表 (tiaohou.py)
    │
    ▼
Step 8: 病源补充忌神
    │
    ▼
Step 9: 构建四柱详情 + 返回完整结果
```

### 10.2 Web 数据流

```
POST /api/v2/analyze
    │
    ▼
insert_analysis() → SQLite (status=processing)
    │
    ▼
asyncio.create_task(_background_analyze_v2)
    ├─ SSE: progress events
    ├─ run_analysis() → core 计算
    ├─ update_analysis_result() → SQLite
    └─ SSE: done event

GET /api/v2/analysis/{id}
    │
    ▼
get_analysis() → SQLite
    │
    ▼
narrate_analysis() → 9维度叙述文本
    │
    ▼
返回 { result, narration }
```

### 10.3 SDK 数据流

```python
from bazi_pro import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze(mcp_json)
# 内部: full_analysis() → retrieve() → 结构化输出

report = engine.generate_report(result, format='html')
# 内部: generate_html_report() / generate_enhanced_markdown() / generate_dashboard()
```

---

## 11. 依赖关系

### 11.1 Python 依赖

```
bazi-pro
├── jieba (>=0.42.1)                    [核心依赖，必须]
│
├── [可选: hybrid]
│   ├── sentence-transformers (>=2.2)   [向量检索]
│   ├── faiss-cpu (>=1.7)               [向量索引]
│   └── numpy (>=1.24)                  [数值计算]
│
├── [可选: report]
│   └── markdown (>=3.5)                [Markdown → HTML]
│
├── [可选: pdf]
│   └── weasyprint (>=60)               [PDF 生成]
│
├── [可选: server]
│   ├── fastapi (>=0.110)               [Web 框架]
│   ├── uvicorn[standard] (>=0.20)      [ASGI 服务器]
│   ├── pydantic (>=2,<3)               [数据校验]
│   ├── aiosqlite (>=0.19)              [异步 SQLite]
│   ├── redis (>=4.5)                   [缓存/限流/任务存储（可选）]
│   ├── websockets (>=11.0)             [WebSocket]
│   └── jinja2 (>=3.1)                 [模板引擎]
│
├── [可选: tui]
│   └── rich (>=13.0)                   [终端 UI]
│
└── [all] = hybrid + report + pdf + server + tui
```

### 11.2 前端依赖

```
frontend
├── next (16.2.6)                       [App Router 框架]
├── react (19.2.4) / react-dom          [UI 渲染]
├── zustand (^5.0.13)                   [状态管理]
├── echarts (^6.1.0)                    [图表]
├── echarts-for-react (^3.0.6)          [React ECharts 封装]
├── tailwindcss (^4)                    [CSS 框架]
└── typescript (^5)                     [类型系统]
```

### 11.3 模块导入关系

```
bazi_pro/__init__.py (AnalysisEngine)
    ├── bazi_pro.core.full_analysis
    │   ├── bazi_pro.core.constants (GAN_WUXING, derive_shishen)
    │   ├── bazi_pro.core.strength (calc_deling, calc_dedi, calc_deshi, judge_wangshuai)
    │   ├── bazi_pro.core.elements (calc_element_forces)
    │   ├── bazi_pro.core.relations (detect_relations, detect_shishen_relations)
    │   ├── bazi_pro.core.patterns (screen_pattern)
    │   ├── bazi_pro.core.yongshen (derive_yongshen)
    │   ├── bazi_pro.core.disease (detect_disease)
    │   ├── bazi_pro.core.tiaohou (lookup_tiaohou)
    │   └── bazi_pro.validation (validate_bazi_input)
    ├── bazi_pro.retrieve_classical (retrieve, retrieve_batch, load_corpus)
    └── bazi_pro.evidence (build_analysis_evidence, new_evidence)

bazi_pro/narrator.py
    ├── bazi_pro.core.constants (GAN_WUXING, ZHI_WUXING)
    └── bazi_pro.core.tiaohou (lookup_tiaohou)

server/app.py
    ├── server.analysis (run_analysis)
    ├── server.db (insert_analysis, get_analysis, ...)
    ├── server.cache (get_cache)
    ├── server.ratelimiter (create_rate_limiter)
    ├── server.schemas (BaziAnalysisRequest)
    ├── server.taskstore (create_task_store)
    ├── server.ws (manager)
    └── bazi_pro.narrator (narrate_analysis) [V2 路由]

bazi_pro/view_model.py
    └── bazi_pro.ui.text_cleaner (可选)

bazi_pro/core_rules.py [废弃 shim]
    └── bazi_pro.core.* (re-export + DeprecationWarning)
```

---

## 12. 项目运行方式

### 12.1 安装

```bash
# 克隆
git clone git@github.com:Minervaowl7/bazi-pro.git
cd bazi-pro

# 最小安装（核心 + 检索）
pip install -e .

# 完整安装（含 hybrid、report、pdf、server、tui）
pip install -e ".[all]"
```

### 12.2 核心命令

```bash
# 古籍检索
python scripts/retrieve_classical.py "食神 制杀 身弱" -k 3 --json
python scripts/retrieve_classical.py --stats
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
python -m bazi_pro.trace demo > trace.json
python -m bazi_pro.trace validate trace.json

# Hybrid Search 状态检查
python scripts/hybrid_search.py
```

### 12.3 Console Scripts（pip install -e . 后）

```bash
bazi-retrieve "食神 制杀 身弱" -k 3 --json
bazi-report --input analysis.md --output report.html
bazi-doctor
bazi-evidence
bazi-trace demo
bazi-server          # 启动后端
bazi-tui             # TUI 界面
bazi-hybrid          # Hybrid Search
```

### 12.4 启动 Web 服务

```bash
# 后端（端口 8710）
python -m uvicorn server.app:app --host 127.0.0.1 --port 8710
# 或
bazi-server

# 前端（端口 3000）
cd frontend
pnpm install
pnpm dev
```

### 12.5 作为 Python 包使用

```python
from bazi_pro import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze({
    "性别": "女",
    "八字": "壬午 乙巳 丁亥 癸卯",
    "日主": "丁",
})
print(result['pattern'])
print(result['yongshen'])

report = engine.generate_report(result, format='html')
```

### 12.6 验证命令

```bash
# 主测试
python -m pytest tests/test_core.py tests/test_full_analysis.py -v

# Golden Cases 边界回归测试
python tests/run_golden.py

# 环境诊断
python -m bazi_pro.doctor

# 编译检查
python -m compileall bazi_pro scripts tests -q

# Lint
ruff check bazi_pro/ tests/ scripts/

# 版本一致性
python scripts/check_version_consistency.py
```

---

## 13. 测试与质量保障

### 13.1 测试文件 (`tests/`)

| 文件 | 说明 |
|------|------|
| `test_core.py` | 核心计算单元测试 |
| `test_full_analysis.py` | 完整分析流程测试 |
| `test_analysis_golden.py` | Golden Case 自动化测试 |
| `test_consumer_report.py` | 消费级报告测试 |
| `test_evidence_cases.py` | 证据链案例测试 |
| `test_trace.py` | Trace schema 校验测试 |
| `test_retrieve.py` | 检索功能测试 |
| `test_retrieve_cache_dir.py` | 检索缓存目录测试 |
| `test_server.py` | 服务器集成测试 |
| `test_server_entrypoint.py` | 服务器入口测试 |
| `test_server_validation.py` | 服务器校验测试 |
| `test_ratelimiter.py` | 限流器测试 |
| `test_validation.py` | 输入校验测试 |
| `test_vm_extraction.py` | ViewModel 提取测试 |
| `test_dayun_extraction.py` | 大运提取测试 |
| `test_html_quality.py` | HTML 输出质量测试 |
| `test_hardening_p0.py` | P0 加固测试 |
| `test_console_scripts.py` | Console Scripts 测试 |
| `test_auth_frontend_contract.py` | 前端认证契约测试 |
| `run_golden.py` | Golden Cases 运行器 |
| `validate_output_schema.py` | 输出 schema 校验 |

### 13.2 Golden Cases

`tests/golden_cases/` 包含 98 个边界回归测试用例，覆盖：

| 类别 | 示例 |
|------|------|
| 从格边界 | `congsha_vs_shenruo`, `yangren_vs_congqiang`, `congqiang_vs_yangren` |
| 正格 | `zhenguan_ge`, `qishage`, `shangguan_peiyin`, `shishen_zhisha` |
| 建禄月劫 | `jianlu_yuejie`, `jianlu_benqi`, `jianlu_wuyong` |
| 极端情况 | `jiwang`, `jiruo`, `extreme_cold`, `extreme_hot`, `all_same_wuxing` |
| 刑冲合害 | `dizhi_chong`, `dizhi_he`, `dizhi_xing`, `dizhi_hai`, `sanhe_ju` |
| 调候 | `han_nuan_tiaohou`, `classical_caiwang_shenruo` |
| 藏干 | `canggan_quanzhong`, `pianyin_benqi`, `pianyin_zhongqi` |

### 13.3 CI 流程 (`.github/workflows/ci.yml`)

| 步骤 | 说明 |
|------|------|
| Version consistency | 版本一致性检查 |
| Corpus stats | 语料统计 |
| Basic/Batch retrieve | 检索功能 |
| Doctor | 环境诊断 |
| Evidence | 证据对象 |
| Hybrid status | Hybrid Search 状态 |
| Report/Dashboard | 报告/仪表盘生成 |
| Trace validation | Trace 校验 |
| Golden cases | 边界回归测试 |
| Package import | 模块导入检查 |
| Install + Console scripts | 安装与 CLI 测试 |
| Wheel build | 构建 wheel |

---

## 14. 环境变量与配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `BAZI_API_KEY` | 空 | API 鉴权密钥（空则不鉴权） |
| `BAZI_CORS_ORIGINS` | `http://localhost:3000,...` | CORS 允许源 |
| `BAZI_ALLOWED_HOSTS` | 空 | 受信主机列表 |
| `BAZI_HOST` | `0.0.0.0` | 服务器监听地址 |
| `BAZI_PORT` | `8710` | 服务器端口 |
| `BAZI_LOG_LEVEL` | `info` | 日志级别 |
| `BAZI_WORKERS` | `1` | Uvicorn 工作进程数 |
| `BAZI_MAX_PAYLOAD_BYTES` | `10240` | 请求体最大字节数 |
| `BAZI_RATE_LIMIT_REQUESTS` | `30` | 限流：窗口内最大请求数 |
| `BAZI_RATE_LIMIT_WINDOW_SECONDS` | `60` | 限流：窗口秒数 |
| `BAZI_TASK_TTL_SECONDS` | `7200` | 任务 TTL |
| `BAZI_MAX_CONCURRENT_TASKS` | `1000` | 最大并发任务数 |
| `BAZI_DB_PATH` | `bazi_pro.db` | SQLite 数据库路径 |
| `BAZI_ENABLE_DOCS` | 空 | 启用 Swagger/ReDoc 文档 |
| `REDIS_URL` | 空 | Redis 连接 URL |
| `DEBUG` | 空 | 调试模式 |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8710` | 前端 API 地址 |

---

## 15. 关键约束与设计原则

### 15.1 不可违反的规则

1. **`bazi_pro/core/` 模块只从 `bazi_pro.core.*` 导入**，禁止从 `bazi_pro` 直接导入（防循环依赖）
2. **每个新规则至少一个测试**：新增 `bazi_pro/core/` 函数必须加测试
3. **公共 API 变更需兼容性测试**：修改 `AnalysisEngine.analyze()` 或 `full_analysis()` 返回键需更新 `EXPECTED_TOP_LEVEL_KEYS`
4. **Golden Cases 数量不可减少**：当前 98 例，只能增加或修正
5. **脚本必须传播退出码**：`scripts/*.py` 使用 `sys.exit(main())`
6. **Doctor 遇 FAIL 必须退出码 1**
7. **禁止 LLM 占位符**：模式名、旺衰裁决、用神值不得含"待LLM分析"
8. **极旺/极弱优先检查**：`judge_wangshuai()` 中"极旺"/"极弱"在"身旺"/"身弱"之前
9. **检索错误必须可见**：`AnalysisEngine.retrieve()` 错误出现在 `result["retrieval"]["warnings"]`
10. **CI 必须运行完整验证链**

### 15.2 关键 Gotchas

- **`core_rules.py` 是废弃 shim**：内部代码应从 `bazi_pro.core` 导入
- **建禄月劫格**：层1/2/3 都走 `_build_jianlu_yuejie()`，输出"建禄格，透X"而非"比肩格"
- **`percent` vs `percent_adjusted`**：格局筛查用 `percent`（原始），化气格用 `percent_adjusted`（合化修正）
- **从格用神方向**：从强/专旺→印星，从财→财星，从官杀→官杀，从儿→食伤
- **建禄月劫格用神**：由格局名中"透X"决定，不是盲取 `PATTERN_YONGSHEN` 表
- **Windows 兼容**：子进程测试使用 `sys.executable`，文件读写指定 `encoding="utf-8"`
- **Server 模块可选**：`server/` 依赖不装也不影响核心功能
- **前端包管理**：使用 `pnpm`（非 npm/yarn）

---

## 16. 附录：完整文件清单

```
bazi-pro/
├── .github/workflows/ci.yml
├── bazi_pro/
│   ├── __init__.py                      # SDK 入口 (AnalysisEngine)
│   ├── core/
│   │   ├── __init__.py                  # full_analysis() 主入口
│   │   ├── constants.py                 # 天干地支映射、十神推导
│   │   ├── stems.py                     # 天干五合、五行生克
│   │   ├── branches.py                  # 地支藏干、十二长生、刑冲合害表
│   │   ├── hidden_stems.py              # 藏干展开
│   │   ├── ten_gods.py                  # 十神关系辅助
│   │   ├── strength.py                  # 旺衰判定
│   │   ├── elements.py                  # 五行力量计算
│   │   ├── patterns.py                  # 六层格局筛查
│   │   ├── yongshen.py                  # 喜用神推导
│   │   ├── relations.py                 # 刑冲合害检测
│   │   ├── disease.py                   # 格局之病检测
│   │   └── tiaohou.py                   # 调候用神查表
│   ├── data/
│   │   ├── __init__.py
│   │   └── classical_corpus.md          # 2964 条古籍语料
│   ├── tui/
│   │   ├── __init__.py
│   │   └── app.py                       # TUI 界面
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── report.py                    # 咨询报告
│   │   ├── replay.py                    # 裁决回放
│   │   ├── consumer_report.py           # 消费级报告
│   │   ├── report_composer.py           # 报告编排器
│   │   ├── text_cleaner.py              # 文本清洗
│   │   ├── verdict_seal.py              # 裁决印章 SVG
│   │   ├── pillar_chart.py              # 四柱命盘 SVG
│   │   ├── reasoning_graph.py           # 推理图谱
│   │   ├── timeline_river.py            # 命运河流时间轴
│   │   ├── classics_viewer.py           # 古典文献查看器
│   │   ├── compare_view.py              # 对比视图
│   │   ├── glossary.py                  # 术语表
│   │   ├── sandbox_ui.py               # 沙盘 UI
│   │   ├── static/tokens.css            # 设计令牌
│   │   └── templates/__init__.py
│   ├── retrieve_classical.py            # BM25 古籍检索
│   ├── hybrid_search.py                 # 融合检索
│   ├── narrator.py                      # 确定性叙述器
│   ├── generate_report.py               # 报告生成器
│   ├── dashboard.py                     # 交互式仪表盘
│   ├── evidence.py                      # 证据链对象
│   ├── trace.py                         # 分析追踪
│   ├── view_model.py                    # ViewModel 数据层
│   ├── validation.py                    # 输入校验
│   ├── doctor.py                        # 环境诊断
│   ├── plugin_api.py                    # 插件 API
│   ├── core_rules.py                    # 废弃 shim
│   ├── compare_engine.py                # 对比引擎
│   ├── calibration.py                   # 历史校准
│   ├── liunian_sandbox.py               # 流年沙盘
│   └── archive.py                       # 归档工具
├── server/
│   ├── __init__.py
│   ├── app.py                           # FastAPI 应用
│   ├── analysis.py                      # 异步分析编排
│   ├── db.py                            # SQLite 存储层
│   ├── schemas.py                       # Pydantic 模型
│   ├── cache.py                         # 缓存层
│   ├── ratelimiter.py                   # 限流器
│   ├── taskstore.py                     # 任务存储
│   └── ws.py                            # WebSocket 管理
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                 # 首页
│   │   │   ├── layout.tsx               # 根布局
│   │   │   ├── globals.css              # 全局样式
│   │   │   └── analyze/[id]/page.tsx    # 分析结果页
│   │   ├── components/
│   │   │   ├── BirthForm.tsx
│   │   │   ├── BaziChartCard.tsx
│   │   │   ├── AnalysisProgress.tsx
│   │   │   ├── DayunTimeline.tsx
│   │   │   ├── SchoolPanel.tsx
│   │   │   └── HistorySidebar.tsx
│   │   ├── lib/api.ts                   # API 通信
│   │   └── stores/analysisStore.ts      # Zustand 状态
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── eslint.config.mjs
├── plugins/
│   ├── __init__.py
│   ├── loader.py                        # 插件加载器
│   └── examples/
│       ├── english/                     # 英文翻译插件
│       ├── fengshui/                    # 风水分析插件
│       └── tarot/                       # 塔罗关联插件
├── scripts/
│   ├── __init__.py
│   ├── retrieve_classical.py
│   ├── generate_report.py
│   ├── dashboard.py
│   ├── evidence.py
│   ├── hybrid_search.py
│   ├── doctor.py
│   ├── audit_all.py
│   ├── audit_data_tables.py
│   ├── audit_golden_cases.py
│   ├── audit_logic_chain.py
│   ├── check_version_consistency.py
│   └── validate_pattern_rules.py
├── tests/
│   ├── test_core.py
│   ├── test_full_analysis.py
│   ├── test_analysis_golden.py
│   ├── test_consumer_report.py
│   ├── test_evidence_cases.py
│   ├── test_trace.py
│   ├── test_retrieve.py
│   ├── test_server.py
│   ├── test_validation.py
│   ├── test_ratelimiter.py
│   ├── run_golden.py
│   ├── golden_cases/                    # 98 个边界回归用例
│   └── evidence_cases/                  # 10 个证据链案例
├── references/
│   ├── classical_corpus.md              # 2964 条古籍语料
│   ├── tiaohou.md                       # 调候用神参考表
│   ├── ETHICS.md                        # 伦理规范
│   ├── bazi-mcp-direct-call.md          # MCP 绕过指南
│   ├── migration-checklist.md           # 迁移清单
│   ├── case-study-false-positive-yangren.md
│   ├── design_tokens.css                # 设计令牌
│   └── ...
├── examples/
│   ├── sample_bazi_mcp.json
│   ├── sample_analysis.md
│   ├── sample_report.md
│   ├── sample_dashboard.html
│   └── sample_trace.json
├── pyproject.toml
├── requirements.txt
├── SKILL.md                             # 核心运行时契约
├── CLAUDE.md                            # Claude Code 工作指南
├── AGENTS.md                            # Agent Guardrails
├── README.md
├── LICENSE
└── MANIFEST.in
```

---

*本文档由项目代码分析生成，涵盖 bazi-pro v5.0.0 的完整架构、模块、类函数、依赖与运行方式。*
