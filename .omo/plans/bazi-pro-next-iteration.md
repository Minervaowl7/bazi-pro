# bazi-pro v6.0 大版本迭代计划

## TL;DR

> **核心目标**: 三大方向并行推进——紫微斗数深度整合、前端体验全面升级、LLM 智能体增强，打造八字+紫微联合命理分析平台。
>
> **交付物**:
> - 八字+紫微联合分析视图（前后端）
> - 紫微大运/流年/四化飞星完整展示
> - 流式 Chat 对话（SSE）
> - 移动端响应式适配
> - Agent 多轮对话 + 上下文记忆
> - RAG 检索增强（向量融合 + 引用溯源）
>
> **预估周期**: 4-6 周（三波并行）
> **并行执行**: YES - 3 波次，最多 8 个并行任务

---

## Context

### 原始需求
用户希望对 bazi-pro 进行大版本迭代，重点方向：
1. **紫微斗数完善** — 前端紫微命盘展示、八字+紫微联合分析、紫微大运流年
2. **前端体验升级** — 移动端适配、流式报告生成、交互优化、性能提升
3. **LLM 智能体增强** — 流式对话、RAG 检索增强、多轮对话上下文、Agent 编排

### 现状分析

#### 紫微斗数模块现状
- **后端核心** (`bazi_pro/core/ziwei/`): 已实现 constants(405行)、patterns(1500行,42个格局)、sihua(205行)、stars(146行)、utils(236行)、narrator(310行) — **成熟**
- **服务层** (`server/ziwei.py`): 基于 iztro-py 封装，提供 chart/horoscope/palace 三个查询函数 — **可用**
- **API 路由** (`server/routes/v2_ziwei.py`): 3 个 POST 端点 — **基础**
- **智能体** (`server/agents/ziwei_agent.py`): 调用 server.ziwei + 可选 LLM 解读 — **可用**
- **前端** (`ZiweiPanel.tsx`): 12 宫格渲染，显示主星/辅星/煞星 — **基础可用**
- **测试** (`test_ziwei.py`): 524 行测试 — **覆盖良好**
- **缺口**: 无紫微大运/流年展示、无四化飞星动态、无八字+紫微联合视图、无紫微专属报告章节

#### 前端体验现状
- **框架**: Next.js 16 + React 19 + Tailwind 4 + Zustand + ECharts + GSAP
- **页面**: 首页(BirthForm)、分析页(642行，27+组件)、报告页、对比页
- **SSE**: 失速检测60s超时 + 轮询降级 — **可靠**
- **缺口**: 移动端适配不完整、Chat 非流式、加载骨架屏缺失、首页引导弱、错误状态 UI 粗糙

#### LLM 智能体现状
- **LLM 客户端** (`server/llm.py`): 1108行，支持 OpenAI 兼容 API、streaming、reasoning_content — **成熟**
- **Agent 编排** (`server/agents/orchestrator.py`): 八字+紫微并行 → 综合智能体 — **可用**
- **RAG** (`server/rag_engine.py`): 问题分类(7类) + BM25 古籍检索 + 动态 query 构造 — **基础**
- **Chat** (`server/routes/v2_chat.py`): 支持流式/非流式，学校视角切换 — **可用**
- **缺口**: Chat 前端非流式显示、多轮上下文管理粗糙、无 function calling/tool use、RAG 仅 BM25 无向量融合

### 技术约束
- Python >= 3.10, Node >= 18, pnpm
- 前端: Next.js 16 + React 19 + Tailwind 4 (已有 `// @ts-nocheck` echarts 兼容)
- 后端: FastAPI + SQLite + SSE
- LLM: mimo-v2.5-pro (reasoning 模型，返回 reasoning_content)
- `bazi_pro/core/` 纯确定性，禁止 LLM/I/O
- `server/analysis.py` 只追加不修改签名
- 120 Golden Cases 只增不减

---

## Work Objectives

### 核心目标
将 bazi-pro 从"八字分析工具"升级为"八字+紫微联合命理平台"，具备流式 AI 对话、完善的移动端体验、和智能 RAG 检索能力。

### 具体交付物
1. 紫微大运/流年/四化飞星 API + 前端展示
2. 八字+紫微联合分析面板（前后端）
3. 紫微专属报告章节（含 PDF）
4. 流式 Chat 对话（前端 SSE 渲染）
5. 移动端响应式适配（关键页面）
6. 加载骨架屏 + 错误状态 UI
7. Agent 多轮对话上下文管理
8. RAG 向量融合检索（可选，依赖 hybrid 配置）

### Definition of Done
- [ ] `ruff check server/ bazi_pro/ tests/` 零错误
- [ ] `python -m pytest tests/ -q` 全部通过
- [ ] `python tests/run_golden.py` 120/120 通过
- [ ] 前端 `pnpm build` 零错误
- [ ] 移动端（375px 宽度）关键页面可用
- [ ] Chat 流式响应正常显示

### Must Have
- 紫微大运/流年数据 API
- 八字+紫微联合分析视图
- Chat 流式显示（前端 SSE）
- 移动端 BirthForm + 分析页适配
- 加载骨架屏

### Must NOT Have (守卫线)
- 禁止在 `bazi_pro/core/` 中引入 LLM 调用或 I/O
- 禁止修改 `server/analysis.py` 已有函数签名
- 禁止减少 Golden Cases 数量
- 禁止引入新的前端重状态依赖（如 Redux）
- 禁止硬编码 API Key 或密钥

---

## Verification Strategy

### 测试决策
- **基础设施**: YES (pytest + ruff)
- **自动化测试**: Tests-after（先实现后补测试）
- **框架**: pytest (后端), pnpm build (前端)

### QA 策略
每个任务必须包含 agent 可执行的 QA 场景。证据保存到 `.omo/evidence/task-{N}-*.ext`。

---

## Execution Strategy

### 并行执行波次

```
Wave 1 (基础设施 + 紫微 API):
├── Task 1: 紫微大运/流年 API [deep]
├── Task 2: 紫微四化飞星 API [deep]
├── Task 3: Chat 流式 SSE 前端改造 [unspecified-high]
├── Task 4: 前端加载骨架屏组件 [visual-engineering]
├── Task 5: 移动端 BirthForm 适配 [visual-engineering]
└── Task 6: Agent 多轮上下文管理 [deep]

Wave 2 (核心功能 + UI):
├── Task 7: 八字+紫微联合分析面板(前端) (depends: 1, 2) [visual-engineering]
├── Task 8: 紫微大运/流年前端时间轴 (depends: 1) [visual-engineering]
├── Task 9: 紫微四化飞星可视化 (depends: 2) [visual-engineering]
├── Task 10: 移动端分析页适配 (depends: 4, 5) [visual-engineering]
├── Task 11: RAG 检索增强 — 向量融合 (depends: 6) [deep]
├── Task 12: Agent Tool Use / Function Calling (depends: 6) [deep]
└── Task 13: Chat 引用溯源显示 (depends: 3, 11) [visual-engineering]

Wave 3 (报告 + 集成):
├── Task 14: 紫微专属报告章节 (depends: 7, 8, 9) [unspecified-high]
├── Task 15: 联合分析 PDF 报告 (depends: 14) [unspecified-high]
├── Task 16: 错误状态 UI 完善 (depends: 10) [visual-engineering]
├── Task 17: 性能优化 — 懒加载 + 代码分割 (depends: 10) [visual-engineering]
└── Task 18: 首页引导优化 (depends: 4, 5) [visual-engineering]

Wave FINAL (验证):
├── Task F1: 计划合规审计 [oracle]
├── Task F2: 代码质量审查 [unspecified-high]
├── Task F3: 端到端 QA [unspecified-high]
└── Task F4: 范围保真检查 [deep]
-> 展示结果 -> 获取用户确认
```

### 依赖矩阵

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | - | 7, 8 |
| 2 | - | 7, 9 |
| 3 | - | 13 |
| 4 | - | 10, 18 |
| 5 | - | 10, 18 |
| 6 | - | 11, 12 |
| 7 | 1, 2 | 14 |
| 8 | 1 | 14 |
| 9 | 2 | 14 |
| 10 | 4, 5 | 16, 17 |
| 11 | 6 | 13 |
| 12 | 6 | - |
| 13 | 3, 11 | - |
| 14 | 7, 8, 9 | 15 |
| 15 | 14 | - |
| 16 | 10 | - |
| 17 | 10 | - |
| 18 | 4, 5 | - |

### Agent Dispatch Summary

- **Wave 1**: 6 任务 — T1→`deep`, T2→`deep`, T3→`unspecified-high`, T4→`visual-engineering`, T5→`visual-engineering`, T6→`deep`
- **Wave 2**: 7 任务 — T7→`visual-engineering`, T8→`visual-engineering`, T9→`visual-engineering`, T10→`visual-engineering`, T11→`deep`, T12→`deep`, T13→`visual-engineering`
- **Wave 3**: 5 任务 — T14→`unspecified-high`, T15→`unspecified-high`, T16→`visual-engineering`, T17→`visual-engineering`, T18→`visual-engineering`
- **FINAL**: 4 任务 — F1→`oracle`, F2→`unspecified-high`, F3→`unspecified-high`, F4→`deep`

---

## TODOs

- [x] 1. 紫微大运/流年 API

  **What to do**:
  - 在 `server/ziwei.py` 中新增 `get_ziwei_dayun()` 函数，调用 iztro-py 获取大运数据
  - 在 `server/routes/v2_ziwei.py` 新增 `POST /api/v2/ziwei/dayun` 端点
  - 返回结构: 每步大运包含 `{ age_range, palace, major_stars, sihua_flow, decade_score }`
  - 新增 `POST /api/v2/ziwei/liunian` 端点，返回流年数据
  - 添加测试用例到 `tests/test_ziwei.py`

  **Must NOT do**:
  - 不修改 `bazi_pro/core/` 中的任何文件
  - 不硬编码大运判定逻辑（依赖 iztro-py）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要深入理解 iztro-py API 和紫微斗数大运排盘逻辑
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `frontend-design`: 纯后端任务

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: Tasks 7, 8
  - **Blocked By**: None

  **References**:
  **Pattern References**:
  - `server/ziwei.py:get_ziwei_chart()` — 现有的 chart 查询模式，新函数应遵循相同结构
  - `server/routes/v2_ziwei.py:33-45` — 现有端点注册模式

  **API/Type References**:
  - `bazi_pro/core/ziwei/constants.py` — 紫微斗数常量定义
  - iztro-py 文档: `https://github.com/SylarLong/iztro` — 大运/流年 API

  **WHY Each Reference Matters**:
  - `get_ziwei_chart()` 展示了如何封装 iztro-py 调用，新函数应保持一致的错误处理和返回结构
  - 现有端点展示了 Pydantic model + asyncio.to_thread 模式

  **Acceptance Criteria**:
  - [ ] `POST /api/v2/ziwei/dayun` 返回有效大运数据
  - [ ] `POST /api/v2/ziwei/liunian` 返回有效流年数据
  - [ ] `tests/test_ziwei.py` 新增大运/流年测试用例

  **QA Scenarios**:

  ```
  Scenario: 大运 API 正常返回
    Tool: Bash (curl)
    Preconditions: 后端运行在 8711 端口
    Steps:
      1. curl -X POST http://127.0.0.1:8711/api/v2/ziwei/dayun -H "Content-Type: application/json" -d '{"solar_date":"1990-05-15","hour":8,"gender":1}'
      2. 解析 JSON 响应
      3. 验证返回包含 "dayun" 键，值为数组
      4. 验证每个大运条目包含 "age_range" 和 "palace" 字段
    Expected Result: HTTP 200，返回结构化大运数据
    Failure Indicators: HTTP 4xx/5xx，缺少 "dayun" 键
    Evidence: .omo/evidence/task-1-dayun-api.json

  Scenario: 流年 API 正常返回
    Tool: Bash (curl)
    Preconditions: 后端运行在 8711 端口
    Steps:
      1. curl -X POST http://127.0.0.1:8711/api/v2/ziwei/liunian -H "Content-Type: application/json" -d '{"solar_date":"1990-05-15","hour":8,"gender":1}'
      2. 解析 JSON 响应
      3. 验证返回包含 "liunian" 键
    Expected Result: HTTP 200，返回流年数据
    Evidence: .omo/evidence/task-1-liunian-api.json
  ```

  **Commit**: YES
  - Message: `feat(ziwei): 大运/流年 API 端点`
  - Files: `server/ziwei.py`, `server/routes/v2_ziwei.py`, `tests/test_ziwei.py`

---

- [x] 2. 紫微四化飞星 API

  **What to do**:
  - 在 `server/ziwei.py` 中新增 `get_ziwei_sihua()` 函数
  - 返回每颗星的四化状态 (化禄/化权/化科/化忌) + 飞星轨迹
  - 在 `server/routes/v2_ziwei.py` 新增 `POST /api/v2/ziwei/sihua` 端点
  - 支持按宫位查询四化飞入/飞出

  **Must NOT do**:
  - 不修改已有端点的返回结构

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 四化飞星是紫微斗数最复杂的部分之一，需要深入理解
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 9
  - **Blocked By**: None

  **References**:
  - `bazi_pro/core/ziwei/sihua.py` — 四化计算核心逻辑
  - `server/ziwei.py:get_ziwei_chart()` — API 封装模式

  **Acceptance Criteria**:
  - [ ] `POST /api/v2/ziwei/sihua` 返回四化数据
  - [ ] 每颗星显示化禄/化权/化科/化忌状态
  - [ ] 测试覆盖正常和边界情况

  **QA Scenarios**:

  ```
  Scenario: 四化 API 返回完整数据
    Tool: Bash (curl)
    Steps:
      1. curl -X POST http://127.0.0.1:8711/api/v2/ziwei/sihua -H "Content-Type: application/json" -d '{"solar_date":"1990-05-15","hour":8,"gender":1}'
      2. 验证返回包含 "sihua" 键
      3. 验证每条记录包含 "star" 和 "mutagen" 字段
    Expected Result: HTTP 200，四化数据完整
    Evidence: .omo/evidence/task-2-sihua-api.json
  ```

  **Commit**: YES
  - Message: `feat(ziwei): 四化飞星 API 端点`
  - Files: `server/ziwei.py`, `server/routes/v2_ziwei.py`, `tests/test_ziwei.py`

---

- [x] 3. Chat 流式 SSE 前端改造

  **What to do**:
  - 改造 `ChatPanel.tsx` 支持 SSE 流式渲染（逐字显示）
  - 后端 `v2_chat.py` 的 chat 端点改为 SSE streaming 响应
  - 支持 reasoning_content 的渐进显示（思考过程折叠）
  - 流式中断时的优雅降级

  **Must NOT do**:
  - 不修改 `server/llm.py` 已有函数签名

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 涉及前后端联调，SSE 协议处理
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 13
  - **Blocked By**: None

  **References**:
  - `frontend/src/components/ChatPanel.tsx` — 当前 Chat UI
  - `server/routes/v2_chat.py` — 当前 Chat API
  - `server/llm.py:chat_completion_stream()` — 现有流式 LLM 调用
  - `frontend/src/stores/analysisStore.ts:_resetStallTimeout()` — SSE 失速检测模式

  **Acceptance Criteria**:
  - [ ] Chat 消息逐字流式显示
  - [ ] reasoning_content 折叠显示
  - [ ] 流式中断时显示友好提示

  **QA Scenarios**:

  ```
  Scenario: Chat 流式响应
    Tool: Playwright
    Preconditions: 前后端运行，已完成一次分析
    Steps:
      1. 导航到分析页，打开 Chat 面板
      2. 输入 "分析我的事业运势"，点击发送
      3. 观察响应是否逐字出现（非一次性全部显示）
      4. 验证 reasoning 内容可折叠
    Expected Result: 流式逐字显示，reasoning 可折叠
    Evidence: .omo/evidence/task-3-chat-stream.png
  ```

  **Commit**: YES
  - Message: `feat(chat): 流式 SSE 对话`
  - Files: `frontend/src/components/ChatPanel.tsx`, `server/routes/v2_chat.py`

---

- [x] 4. 前端加载骨架屏组件

  **What to do**:
  - 创建 `SkeletonCard.tsx` 通用骨架屏组件
  - 为分析页各面板创建专属骨架屏（四柱、五行、大运、叙述）
  - 在数据加载态替换空白/闪烁为骨架屏动画

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 纯前端 UI 组件，需要动画和视觉设计
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 10, 18
  - **Blocked By**: None

  **References**:
  - `frontend/src/components/AnalysisProgress.tsx` — 现有进度组件
  - `frontend/src/app/analyze/[id]/page.tsx` — 分析页面加载逻辑

  **Acceptance Criteria**:
  - [ ] 骨架屏组件可复用
  - [ ] 分析页各面板有对应骨架屏
  - [ ] 骨架屏动画流畅（CSS animation）

  **QA Scenarios**:

  ```
  Scenario: 分析页加载骨架屏
    Tool: Playwright
    Steps:
      1. 导航到分析页（分析进行中）
      2. 验证四柱区域显示骨架屏占位
      3. 验证五行区域显示骨架屏占位
      4. 等待数据加载完成，骨架屏消失
    Expected Result: 加载态显示骨架屏，数据到后平滑替换
    Evidence: .omo/evidence/task-4-skeleton.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 加载骨架屏组件`
  - Files: `frontend/src/components/ui/Skeleton*.tsx`

---

- [x] 5. 移动端 BirthForm 适配

  **What to do**:
  - BirthForm 表单移动端布局优化（单列、大按钮、触摸友好）
  - 日期/时间选择器移动端适配
  - 表单验证反馈优化（toast 替代 alert）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 响应式设计 + 移动端交互
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 10, 18
  - **Blocked By**: None

  **References**:
  - `frontend/src/components/BirthForm.tsx` — 当前表单
  - `frontend/src/app/page.tsx` — 首页布局

  **Acceptance Criteria**:
  - [ ] 375px 宽度下表单可用
  - [ ] 日期选择器触摸友好
  - [ ] 表单提交后有 loading 状态

  **QA Scenarios**:

  ```
  Scenario: 移动端表单填写
    Tool: Playwright (viewport 375x812)
    Steps:
      1. 设置 viewport 为 375x812
      2. 导航到首页
      3. 填写性别、阳历、时间
      4. 点击提交
      5. 验证表单不溢出、按钮可点击
    Expected Result: 表单正常填写和提交
    Evidence: .omo/evidence/task-5-mobile-form.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 移动端 BirthForm 适配`
  - Files: `frontend/src/components/BirthForm.tsx`

---

- [x] 6. Agent 多轮上下文管理

  **What to do**:
  - `v2_chat.py` 实现对话历史持久化（SQLite）
  - 每次 LLM 调用携带最近 N 轮对话上下文
  - 实现上下文窗口管理（token 预算控制）
  - 对话摘要机制（超过阈值时压缩历史）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 涉及 LLM 上下文管理、token 预算、摘要策略
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 11, 12
  - **Blocked By**: None

  **References**:
  - `server/routes/v2_chat.py` — 当前 Chat API
  - `server/db.py` — 数据库操作模式
  - `server/llm.py` — LLM 调用接口

  **Acceptance Criteria**:
  - [ ] 对话历史持久化到 SQLite
  - [ ] LLM 调用携带上下文
  - [ ] 超长对话自动摘要

  **QA Scenarios**:

  ```
  Scenario: 多轮对话上下文
    Tool: Bash (curl)
    Steps:
      1. 发送第一条消息 "我叫张三"
      2. 发送第二条消息 "我的名字是什么"
      3. 验证第二条回复中包含 "张三"
    Expected Result: LLM 能记住上下文
    Evidence: .omo/evidence/task-6-multi-turn.json
  ```

  **Commit**: YES
  - Message: `feat(chat): 多轮对话上下文管理`
  - Files: `server/routes/v2_chat.py`, `server/db.py`

---

- [x] 7. 八字+紫微联合分析面板

  **What to do**:
  - 创建 `JointAnalysisPanel.tsx` 组件
  - 左侧八字命盘 + 右侧紫微命盘并排显示
  - 中间联动区域：相同维度对比（事业、财运、感情）
  - 综合智能体结果的可视化呈现

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 复杂前端布局 + 数据可视化
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 14
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `frontend/src/components/ZiweiPanel.tsx` — 现有紫微面板
  - `frontend/src/components/BaziChartCard.tsx` — 八字命盘卡片
  - `frontend/src/components/SchoolComparePanel.tsx` — 流派对比面板（布局参考）

  **Acceptance Criteria**:
  - [ ] 八字+紫微并排显示
  - [ ] 维度对比联动
  - [ ] 移动端可折叠为上下布局

  **QA Scenarios**:

  ```
  Scenario: 联合分析面板渲染
    Tool: Playwright
    Steps:
      1. 导航到分析页
      2. 切换到 "联合分析" 视图
      3. 验证左侧显示八字命盘
      4. 验证右侧显示紫微命盘
      5. 验证中间区域显示维度对比
    Expected Result: 联合面板正确渲染
    Evidence: .omo/evidence/task-7-joint-panel.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 八字+紫微联合分析面板`
  - Files: `frontend/src/components/JointAnalysisPanel.tsx`

---

- [x] 8. 紫微大运/流年前端时间轴

  **What to do**:
  - 扩展 `DayunTimeline.tsx` 支持紫微大运数据
  - 紫微大运与八字大运双轨显示
  - 流年叠加层：点击大运展开该运内的流年
  - 四化飞星在时间轴上的标注

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 复杂时间轴 UI + GSAP 动画
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 14
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/components/DayunTimeline.tsx` — 现有大运时间轴
  - GSAP ScrollTrigger 动画模式

  **Acceptance Criteria**:
  - [ ] 紫微大运数据在时间轴上显示
  - [ ] 八字+紫微大运双轨并行
  - [ ] 点击大运可展开流年

  **QA Scenarios**:

  ```
  Scenario: 紫微大运时间轴
    Tool: Playwright
    Steps:
      1. 导航到分析页
      2. 滚动到大运时间轴区域
      3. 验证显示两行大运（八字 + 紫微）
      4. 点击某步大运，验证流年展开
    Expected Result: 双轨大运正确显示
    Evidence: .omo/evidence/task-8-ziwei-dayun.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 紫微大运/流年双轨时间轴`
  - Files: `frontend/src/components/DayunTimeline.tsx`

---

- [x] 9. 紫微四化飞星可视化

  **What to do**:
  - 创建 `SihuaFlowChart.tsx` 组件
  - 12 宫格上标注四化星（化禄绿、化权蓝、化科紫、化忌红）
  - 飞星轨迹动画（从一个宫位飞向另一个宫位）
  - 交互：点击宫位显示该宫四化详情

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 复杂 SVG/Canvas 可视化 + 动画
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 14
  - **Blocked By**: Task 2

  **References**:
  - `frontend/src/components/ZiweiPanel.tsx` — 现有 12 宫格渲染
  - `frontend/src/components/RelationGraph.tsx` — 关系图可视化（动画参考）

  **Acceptance Criteria**:
  - [ ] 四化星在宫格上正确标注
  - [ ] 飞星轨迹有动画效果
  - [ ] 点击宫位显示四化详情

  **QA Scenarios**:

  ```
  Scenario: 四化飞星显示
    Tool: Playwright
    Steps:
      1. 导航到分析页紫微面板
      2. 开启四化飞星模式
      3. 验证化禄/化权/化科/化忌在对应宫位显示
      4. 验证飞星轨迹动画可见
    Expected Result: 四化正确标注，动画流畅
    Evidence: .omo/evidence/task-9-sihua-flow.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 紫微四化飞星可视化`
  - Files: `frontend/src/components/SihuaFlowChart.tsx`

---

- [x] 10. 移动端分析页适配

  **What to do**:
  - 分析页各面板移动端布局（单列、可折叠）
  - 底部 Tab 导航（命盘/分析/大运/对话）
  - 滑动手势切换面板
  - 图表组件响应式缩放

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 移动端响应式设计 + 手势交互
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 16, 17
  - **Blocked By**: Tasks 4, 5

  **References**:
  - `frontend/src/app/analyze/[id]/page.tsx` — 当前分析页
  - `frontend/src/components/Navbar.tsx` — 导航组件

  **Acceptance Criteria**:
  - [ ] 375px 宽度下各面板正常显示
  - [ ] 底部 Tab 导航可用
  - [ ] 图表组件自适应缩放

  **QA Scenarios**:

  ```
  Scenario: 移动端分析页
    Tool: Playwright (viewport 375x812)
    Steps:
      1. 设置 viewport 375x812
      2. 导航到分析页
      3. 验证底部 Tab 导航可见
      4. 点击 "大运" Tab，验证切换
      5. 验证图表不溢出
    Expected Result: 移动端各面板正常
    Evidence: .omo/evidence/task-10-mobile-analysis.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 移动端分析页适配`
  - Files: `frontend/src/app/analyze/[id]/page.tsx`

---

- [x] 11. RAG 检索增强 — 向量融合

  **What to do**:
  - 扩展 `rag_engine.py` 支持 hybrid 检索（BM25 + FAISS 向量）
  - 检索结果带引用溯源（出处古籍 + 条文编号）
  - 动态调整 BM25/向量权重（根据查询类型）
  - 检索结果缓存（避免重复计算）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: RAG 管道优化 + 向量检索 + 权重调优
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 13
  - **Blocked By**: Task 6

  **References**:
  - `server/rag_engine.py` — 现有 RAG 引擎
  - `bazi_pro/hybrid_search.py` — 现有混合检索
  - `bazi_pro/retrieve_classical.py` — BM25 检索

  **Acceptance Criteria**:
  - [ ] RAG 结果包含引用溯源
  - [ ] hybrid 检索可用（需安装 [hybrid] 依赖）
  - [ ] 降级到纯 BM25 时无异常

  **QA Scenarios**:

  ```
  Scenario: RAG 引用溯源
    Tool: Bash (curl)
    Steps:
      1. 发送 Chat 消息 "食神制杀是什么意思"
      2. 验证回复包含古籍引用
      3. 验证引用包含出处信息
    Expected Result: 回复带引用溯源
    Evidence: .omo/evidence/task-11-rag-citation.json
  ```

  **Commit**: YES
  - Message: `feat(rag): 向量融合检索 + 引用溯源`
  - Files: `server/rag_engine.py`

---

- [x] 12. Agent Tool Use / Function Calling

  **What to do**:
  - 定义命理工具集（排盘、查格局、查用神、查神煞、查古籍）
  - LLM 通过 function calling 调用确定性计算
  - 工具调用结果自动注入对话上下文
  - 工具调用链可视化（前端可选展示）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: LLM function calling 设计 + 工具编排
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: Task 6

  **References**:
  - `server/llm.py` — LLM 客户端
  - `bazi_pro/core/` — 确定性计算入口
  - OpenAI function calling 文档

  **Acceptance Criteria**:
  - [ ] LLM 能调用排盘工具
  - [ ] 工具结果注入对话
  - [ ] 调用链可追溯

  **QA Scenarios**:

  ```
  Scenario: Function calling 排盘
    Tool: Bash (curl)
    Steps:
      1. 发送 "帮我排一下 1990年5月15日早上8点的八字"
      2. 验证 LLM 调用了排盘工具
      3. 验证回复包含正确的八字信息
    Expected Result: LLM 通过工具调用获取准确数据
    Evidence: .omo/evidence/task-12-function-call.json
  ```

  **Commit**: YES
  - Message: `feat(agent): function calling 工具集`
  - Files: `server/agents/tools.py`, `server/llm.py`

---

- [x] 13. Chat 引用溯源显示

  **What to do**:
  - Chat 消息中的古籍引用以折叠卡片展示
  - 点击引用跳转到古籍原文
  - 引用可信度评分（基于检索分数）
  - 支持引用展开/折叠

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 前端富文本渲染 + 交互设计
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: Tasks 3, 11

  **References**:
  - `frontend/src/components/ChatPanel.tsx` — Chat UI
  - `react-markdown` + `remark-gfm` — Markdown 渲染

  **Acceptance Criteria**:
  - [ ] 古籍引用以卡片展示
  - [ ] 点击引用可查看详情
  - [ ] 引用可折叠

  **QA Scenarios**:

  ```
  Scenario: 引用溯源显示
    Tool: Playwright
    Steps:
      1. 发送 Chat 消息
      2. 等待回复
      3. 验证回复中有引用卡片
      4. 点击引用卡片，验证展开详情
    Expected Result: 引用正确显示和交互
    Evidence: .omo/evidence/task-13-citation-ui.png
  ```

  **Commit**: YES
  - Message: `feat(chat): 引用溯源卡片`
  - Files: `frontend/src/components/ChatPanel.tsx`

---

- [x] 14. 紫微专属报告章节

  **What to do**:
  - 在报告生成中新增紫微斗数专属章节
  - 包含：命盘总览、主星分析、四化解读、大运流年、与八字交叉验证
  - 支持 consumer/dashboard/report 三种模式
  - 紫微术语 tooltip（与八字术语词典统一）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 报告生成逻辑 + 模板设计
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 15
  - **Blocked By**: Tasks 7, 8, 9

  **References**:
  - `frontend/src/components/report/ReportChapter.tsx` — 报告章节组件
  - `server/report_pdf.py` — PDF 生成
  - `bazi_pro/narrator.py` — 叙述器模式

  **Acceptance Criteria**:
  - [ ] 报告包含紫微章节
  - [ ] consumer 模式有术语解释
  - [ ] PDF 导出包含紫微内容

  **QA Scenarios**:

  ```
  Scenario: 紫微报告章节
    Tool: Playwright
    Steps:
      1. 导航到报告页
      2. 验证紫微斗数章节存在
      3. 验证包含命盘、主星、四化内容
    Expected Result: 紫微章节正确渲染
    Evidence: .omo/evidence/task-14-ziwei-report.png
  ```

  **Commit**: YES
  - Message: `feat(report): 紫微斗数专属报告章节`
  - Files: `frontend/src/components/report/ReportChapter.tsx`, `server/report_pdf.py`

---

- [x] 15. 联合分析 PDF 报告

  **What to do**:
  - PDF 报告包含八字+紫微联合分析
  - 封面显示双命盘缩略图
  - 目录自动生成
  - 支持 A4/Letter 纸张

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: PDF 生成 + 排版设计
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 14

  **References**:
  - `server/report_pdf.py` — 现有 PDF 生成
  - `frontend/src/components/report/ReportPdfButton.tsx` — PDF 下载按钮

  **Acceptance Criteria**:
  - [ ] PDF 包含八字+紫微联合内容
  - [ ] 封面有双命盘缩略图
  - [ ] 目录可点击跳转

  **QA Scenarios**:

  ```
  Scenario: PDF 导出
    Tool: Playwright
    Steps:
      1. 导航到报告页
      2. 点击 "导出 PDF"
      3. 验证 PDF 下载成功
      4. 验证 PDF 包含紫微章节
    Expected Result: PDF 正确导出
    Evidence: .omo/evidence/task-15-pdf-export.pdf
  ```

  **Commit**: YES
  - Message: `feat(report): 联合分析 PDF 报告`
  - Files: `server/report_pdf.py`

---

- [x] 16. 错误状态 UI 完善

  **What to do**:
  - 网络断开时的离线提示
  - 分析失败时的重试按钮 + 错误详情
  - LLM 不可用时的降级提示
  - 404/500 错误页面美化

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 错误状态 UI 设计
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 10

  **References**:
  - `frontend/src/app/not-found.tsx` — 404 页面
  - `frontend/src/app/analyze/[id]/page.tsx:ErrorBoundary` — 错误边界

  **Acceptance Criteria**:
  - [ ] 网络断开显示离线提示
  - [ ] 分析失败有重试按钮
  - [ ] 404/500 页面美观

  **QA Scenarios**:

  ```
  Scenario: 分析失败重试
    Tool: Playwright
    Steps:
      1. 模拟后端不可用
      2. 提交分析
      3. 验证显示错误提示和重试按钮
      4. 恢复后端，点击重试
    Expected Result: 错误提示友好，重试成功
    Evidence: .omo/evidence/task-16-error-ui.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 错误状态 UI 完善`
  - Files: `frontend/src/app/analyze/[id]/page.tsx`

---

- [x] 17. 性能优化 — 懒加载 + 代码分割

  **What to do**:
  - 分析页组件按需加载（dynamic import）
  - ECharts 懒加载
  - 图片/字体预加载优化
  - Bundle size 分析和优化

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 前端性能优化
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 10

  **References**:
  - `frontend/src/app/analyze/[id]/page.tsx` — 已有部分 dynamic import
  - `frontend/next.config.ts` — Next.js 配置

  **Acceptance Criteria**:
  - [ ] 首屏 JS < 500KB
  - [ ] 分析页组件按需加载
  - [ ] Lighthouse 性能分 > 80

  **QA Scenarios**:

  ```
  Scenario: 性能指标
    Tool: Playwright
    Steps:
      1. 打开首页
      2. 记录首屏加载时间
      3. 导航到分析页
      4. 记录各组件加载时间
    Expected Result: 首屏 < 2s，分析页 < 3s
    Evidence: .omo/evidence/task-17-perf.json
  ```

  **Commit**: YES
  - Message: `perf(ui): 懒加载 + 代码分割`
  - Files: `frontend/src/app/analyze/[id]/page.tsx`, `frontend/next.config.ts`

---

- [x] 18. 首页引导优化

  **What to do**:
  - 首页增加示例命盘快速体验
  - 功能亮点展示（紫微、三流派、AI 对话）
  - 用户引导流程（首次访问）
  - SEO meta 标签完善

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 首页设计 + 用户引导
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Tasks 4, 5

  **References**:
  - `frontend/src/app/page.tsx` — 首页
  - `frontend/src/components/BirthForm.tsx` — 表单

  **Acceptance Criteria**:
  - [ ] 首页有示例命盘按钮
  - [ ] 功能亮点展示
  - [ ] SEO meta 完整

  **QA Scenarios**:

  ```
  Scenario: 示例命盘体验
    Tool: Playwright
    Steps:
      1. 导航到首页
      2. 点击 "试试示例命盘"
      3. 验证跳转到分析页
      4. 验证分析结果正常显示
    Expected Result: 示例命盘一键体验
    Evidence: .omo/evidence/task-18-demo.png
  ```

  **Commit**: YES
  - Message: `feat(ui): 首页引导优化`
  - Files: `frontend/src/app/page.tsx`

---

## Final Verification Wave

- [x] F1. **计划合规审计** — `oracle`
  读取计划，逐项检查 Must Have 是否实现，Must NOT Have 是否遵守。检查 evidence 文件存在。
  输出: `Must Have [N/N] | Must NOT Have [N/N] | VERDICT`

- [x] F2. **代码质量审查** — `unspecified-high`
  运行 `ruff check` + `python -m pytest` + `pnpm build`。审查所有变更文件的代码质量。
  输出: `Lint [PASS/FAIL] | Tests [N pass/N fail] | Build [PASS/FAIL] | VERDICT`

- [x] F3. **端到端 QA** — `unspecified-high`
  从 clean state 开始，执行每个任务的 QA 场景。测试跨任务集成。
  输出: `Scenarios [N/N pass] | Integration [N/N] | VERDICT`

- [x] F4. **范围保真检查** — `deep`
  对比每个任务的 "What to do" 与实际 diff，验证 1:1 对应。
  输出: `Tasks [N/N compliant] | VERDICT`

---

## Commit Strategy

| Task | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat(ziwei): 大运/流年 API 端点` | server/ziwei.py, server/routes/v2_ziwei.py, tests/ |
| 2 | `feat(ziwei): 四化飞星 API 端点` | server/ziwei.py, server/routes/v2_ziwei.py, tests/ |
| 3 | `feat(chat): 流式 SSE 对话` | frontend/ChatPanel.tsx, server/v2_chat.py |
| 4 | `feat(ui): 加载骨架屏组件` | frontend/Skeleton*.tsx |
| 5 | `feat(ui): 移动端 BirthForm 适配` | frontend/BirthForm.tsx |
| 6 | `feat(chat): 多轮对话上下文管理` | server/v2_chat.py, server/db.py |
| 7 | `feat(ui): 八字+紫微联合分析面板` | frontend/JointAnalysisPanel.tsx |
| 8 | `feat(ui): 紫微大运/流年双轨时间轴` | frontend/DayunTimeline.tsx |
| 9 | `feat(ui): 紫微四化飞星可视化` | frontend/SihuaFlowChart.tsx |
| 10 | `feat(ui): 移动端分析页适配` | frontend/analyze/[id]/page.tsx |
| 11 | `feat(rag): 向量融合检索 + 引用溯源` | server/rag_engine.py |
| 12 | `feat(agent): function calling 工具集` | server/agents/tools.py, server/llm.py |
| 13 | `feat(chat): 引用溯源卡片` | frontend/ChatPanel.tsx |
| 14 | `feat(report): 紫微斗数专属报告章节` | frontend/report/, server/report_pdf.py |
| 15 | `feat(report): 联合分析 PDF 报告` | server/report_pdf.py |
| 16 | `feat(ui): 错误状态 UI 完善` | frontend/analyze/[id]/page.tsx |
| 17 | `perf(ui): 懒加载 + 代码分割` | frontend/analyze/[id]/page.tsx, next.config.ts |
| 18 | `feat(ui): 首页引导优化` | frontend/page.tsx |

---

## Success Criteria

### 验证命令
```bash
ruff check server/ bazi_pro/ tests/  # Expected: 0 errors
python -m pytest tests/ -q            # Expected: all pass
python tests/run_golden.py            # Expected: 120/120
cd frontend && pnpm build             # Expected: 0 errors
```

### 最终清单
- [ ] 所有 "Must Have" 已实现
- [ ] 所有 "Must NOT Have" 未违反
- [ ] 120 Golden Cases 全部通过
- [ ] 前端 build 成功
- [ ] 移动端关键页面可用
- [ ] Chat 流式响应正常
