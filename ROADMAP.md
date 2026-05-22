# bazi-pro COOL 升级路线图

> 目标：将 bazi-pro 从「生成 HTML 的工具」升级为 **有灵魂的可视化引擎**
> 版本目标：v5.0

---

## 总览

| 阶段 | 主题 | 状态 | 优先级 |
|------|------|:----:|:------:|
| Phase A | 视觉与交互升级 | 🔴 未开始 | P0 |
| Phase B | 技术架构升级 | 🔴 未开始 | P1 |
| Phase C | 功能创新 | 🔴 未开始 | P2 |
| Phase D | 开发者生态 | 🔴 未开始 | P3 |

---

## Phase A：视觉与交互升级

### A-1 动态 SVG 命盘（活命盘）

- [ ] 天干地支使用书法字体渲染（Ma Shan Zheng / Zhi Mang Xing）
- [ ] 地支间刑冲合害关系用动态弧线连接，hover 高亮 + 弹出解读
- [ ] 五行力量用粒子动画表现（木生火 → 绿色粒子流向红色区域）
- [ ] 日主用脉冲光圈标识，突出核心
- [ ] 命盘支持暗色/亮色主题切换
- [ ] 导出命盘为独立 SVG/PNG
- **涉及文件**：`bazi_pro/dashboard.py`, `bazi_pro/ui/verdict_seal.py`
- **新增文件**：`bazi_pro/ui/pillar_chart.py`

### A-2 大运时间轴 → 命运河流

- [ ] 横向卡片改为曲线时间轴（SVG path）
- [ ] 每步大运吉凶用波峰/波谷表达
- [ ] 当前年份光标标注，随时间自动流动
- [ ] hover 某步大运时背景色温渐变（吉→暖色 / 凶→冷色）
- [ ] 支持键盘左右键沿时间轴导航
- **涉及文件**：`bazi_pro/dashboard.py`
- **新增文件**：`bazi_pro/ui/timeline_river.py`

### A-3 证据链面板 → 推理图谱（DAG）

- [ ] 折叠列表改为节点-边图（D3.js 或纯 SVG）
- [ ] 每个证据为节点，basis 为入边，counter_evidence 为红色虚线反证边
- [ ] 置信度热力图（旺衰→格局→喜用 颜色渐变表达衰减）
- [ ] 点击节点展开完整推理链
- [ ] 支持 zoom/pan 交互
- **涉及文件**：`bazi_pro/dashboard.py`, `bazi_pro/evidence.py`
- **新增文件**：`bazi_pro/ui/reasoning_graph.py`

### A-4 裁决印章动画升级

- [ ] 盖章动画效果（墨迹扩散 + 纸张压痕 CSS animation）
- [ ] 外圈五行弧线段微动画（缓慢旋转）
- [ ] 导出印章为独立 PNG（用户可分享到社交媒体）
- **涉及文件**：`bazi_pro/ui/verdict_seal.py`

---

## Phase B：技术架构升级

### B-1 Web 服务层（FastAPI + WebSocket）

- [ ] FastAPI 应用骨架，接收 MCP JSON 上传
- [ ] WebSocket 推送分析进度（Step 0→1→2... 逐步推送）
- [ ] Redis 缓存 BM25 索引和热门查询结果
- [ ] 前端 HTMX/Alpine.js 轻量交互层
- [ ] OpenAPI 文档自动生成
- [ ] Docker 一键部署配置
- **新增目录**：`server/`
- **新增文件**：
  - `server/app.py` — FastAPI 主应用
  - `server/ws.py` — WebSocket 进度推送
  - `server/cache.py` — Redis 缓存层
  - `server/templates/` — Jinja2 模板

### B-2 Hybrid Search 落地与优化

- [ ] embedding 模型 INT8 量化（sentence-transformers 量化功能）
- [ ] FAISS 索引体积缩小 4x
- [ ] 预构建向量索引文件放入 `dist/`
- [ ] 缓存预热：启动时预加载 Top-100 常见查询融合结果
- [ ] 检索结果高亮匹配词（matched_terms 标记）
- **涉及文件**：`bazi_pro/hybrid_search.py`, `bazi_pro/retrieve_classical.py`

### B-3 ViewModel 统一化

- [ ] SKILL.md 执行流输出结构化 JSON（而非纯 Markdown）作为统一数据源
- [ ] 废弃 `build_vm_from_analysis_text()` 正则提取方案
- [ ] 所有 UI 组件只读 ViewModel，不再各自做正则提取
- [ ] `text_cleaner.py` 精简为纯展示层清洗工具
- **涉及文件**：`bazi_pro/view_model.py`, `SKILL.md`, `bazi_pro/ui/text_cleaner.py`

---

## Phase C：功能创新

### C-1 命盘对比模式

- [ ] 双命盘 JSON 上传接口
- [ ] 并排四柱对比视图
- [ ] 五行雷达图叠加显示
- [ ] 喜用神差异高亮
- [ ] 合婚/合作场景合化关系可视化
- [ ] 兼容性报告输出
- **新增文件**：`bazi_pro/ui/compare_view.py`, `bazi_pro/compare_engine.py`

### C-2 流年推演沙盒

- [ ] 年份滑块（2020-2040），拖动实时更新
- [ ] 流年干支与原局合冲关系动态计算
- [ ] 该年五行力量动态变化可视化
- [ ] 引动十神事件预测展示
- [ ] 关键年份书签标记（⭐ 用神到位 / ⚠️ 忌神引动）
- [ ] 导出逐年 PDF 年签
- **新增文件**：`bazi_pro/liunian_sandbox.py`, `bazi_pro/ui/sandbox_ui.py`

### C-3 古籍条文双栏展示

- [ ] 左侧原文扫描风排版（竖排、仿古纸张背景、朱砂圈点）
- [ ] 右侧白话解读 + 命盘命中原因说明
- [ ] matched_terms 高亮显示
- [ ] 底部出处信息条（书名、卷数、原书位置）
- **新增文件**：`bazi_pro/ui/classics_viewer.py`

### C-4 个人命理档案系统

- [ ] SQLite / JSONL 本地存储历史分析记录
- [ ] 同一命盘不同时间喜用神判断趋势追踪
- [ ] Step 9 校准反馈闭环（用户标记准确与否 → 反馈改进权重）
- [ ] 导出个人命理年鉴
- **新增文件**：`bazi_pro/archive.py`, `bazi_pro/calibration.py`

---

## Phase D：开发者生态

### D-1 插件/扩展机制

- [ ] 定义 `BaziPlugin` 抽象基类（on_retrieve / on_evidence / on_render 钩子）
- [ ] 插件发现与加载机制（entry_points / 目录扫描）
- [ ] 内置示例插件：
  - English Translation Plugin
  - Tarot Correlation Plugin
  - Feng Shui Plugin
- [ ] 插件文档与开发指南
- **新增目录**：`plugins/`, `plugins/examples/`
- **新增文件**：`bazi_pro/plugin_api.py`

### D-2 CLI 体验升级（TUI）

- [ ] 引入 `rich` 库渲染彩色表格、进度条、面板
- [ ] Interactive REPL 模式（`bazi-retrieve --interactive`）
- [ ] Tab 补全常用查询词（"伤官见官"、"杀印相生"...）
- [ ] 分析进度 spinner 动画
- **涉及文件**：所有 `scripts/*.py` 入口
- **新增文件**：`bazi_pro/tui/`

### D-3 SDK 化

- [ ] 设计 `AnalysisEngine` 公共 API
- [ ] `pip install bazi-pro` 发布到 PyPI
- [ ] 完整类型注解与 Sphinx 文档
- [ ] Quick Start 教程 + 5 个使用示例
- **涉及文件**：`pyproject.toml`, `bazi_pro/__init__.py`

---

## 依赖清单（按阶段）

```
Phase A:
  └─ 无新依赖（纯 CSS/SVG 动画）

Phase B:
  ├─ fastapi >= 0.100
  ├─ uvicorn[standard] >= 0.20
  ├─ redis >= 4.5
  ├─ websockets >= 11.0
  └─ jinja2 >= 3.1

Phase C:
  ├─ sqlite3（标准库）
  └─ reportlab（PDF 年签，可选）

Phase D:
  ├─ rich >= 13.0
  └─ 无其他新依赖
```

---

## 版本里程碑

| 版本 | 内容 | 目标 |
|------|------|------|
| v4.5 | A-1 ~ A-4 全部完成 | 视觉体验质的飞跃 |
| v4.6 | B-1 Web 服务上线 | 从脚本进化为服务 |
| v4.7 | B-2 + B-3 架构统一 | 数据流彻底清理 |
| v4.8 | C-1 + C-3 新功能 | 对比 + 古籍双栏 |
| v5.0 | C-2 + C-4 + D-1~D-3 | 完整生态闭环 |

---

*本路线图基于 CODE_WIKI.md 架构分析制定，每个任务均可独立执行。*
