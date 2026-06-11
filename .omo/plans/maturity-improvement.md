# bazi-pro 代码成熟度提升计划

## TL;DR

> **核心目标**: 根据 Trail of Bits 代码成熟度评估报告，全面加固安全、代码质量和测试能力。
>
> **交付物**:
> - SSRF 防护增强（域名 DNS 解析校验）
> - LLM 工具调用重试逻辑
> - API 认证覆盖补全
> - llm.py 三模块拆分（客户端/上下文/提示词）
> - v2_chat.py ChatService 提取
> - page.tsx Tab 组件拆分
> - Property-based testing（hypothesis）
>
> **预估周期**: 2-3 周
> **并行执行**: YES - 4 波次

---

## Context

### 评估发现（代码成熟度 3.14/4.0）

| # | 问题 | 级别 | 评分影响 |
|---|------|------|---------|
| C1 | SSRF 防护仅限字面 IP | CRITICAL | 认证 2/4 |
| C2 | LLM 工具调用无重试 | CRITICAL | 测试 4/4→3/4 |
| C3 | API Key Query String 泄露 | CRITICAL | 认证 2/4 |
| H1 | llm.py 1456 行未拆分 | HIGH | 复杂度 3/4 |
| H2 | v2_chat.py 重复代码 80 行 | HIGH | 复杂度 3/4 |
| H3 | page.tsx 1053 行未拆分 | HIGH | 复杂度 3/4 |
| H4 | 无 property-based testing | HIGH | 测试 4/4→3/4 |
| M1 | 8/33 端点缺认证 | MEDIUM | 认证 2/4 |

### 技术约束
- Python >= 3.10, Node >= 18, pnpm
- `bazi_pro/core/` 纯确定性，禁止 LLM/I/O
- `server/analysis.py` 只追加不修改签名
- `server/llm.py` 必须保持向后兼容（改为 re-export shim）
- 120 Golden Cases 只增不减
- `ruff check` + `pytest` + `pnpm build` 每个任务后必须通过

---

## Work Objectives

### Must Have
- SSRF 域名 DNS 解析校验
- LLM 工具调用 429/5xx 重试
- API 认证覆盖补全
- Property-based testing 核心计算函数

### Must NOT Have
- 不修改 `bazi_pro/core/` 已有函数签名
- 不修改 `server/analysis.py` 已有函数签名
- 不减少 Golden Cases
- 不引入 Redux 等重依赖

---

## Execution Strategy

### Wave 1: 安全加固（3 任务并行）
- T1: SSRF 域名 DNS 解析校验
- T2: LLM 工具调用重试逻辑
- T3: API 认证覆盖补全

### Wave 2: 代码拆分（3 任务并行）
- T4: llm.py 三模块拆分
- T5: v2_chat.py ChatService 提取
- T6: page.tsx Tab 组件拆分

### Wave 3: 测试增强（2 任务并行）
- T7: Property-based testing 核心计算
- T8: 集成测试补充

### Wave 4: 验证
- T9: 全量回归测试 + 代码审查

---

## TODOs

- [x] 1. SSRF 域名 DNS 解析校验

  **What to do**:
  - 修改 `server/routes/v2_settings.py` 的 `_is_private_ip()` 函数
  - 对域名使用 `socket.getaddrinfo()` 解析 IP，检查所有解析结果是否在私有 IP 段
  - 添加域名黑名单（`localhost`、`*.nip.io`、`*.localtest.me`、`metadata.google.internal`）
  - 在 `server/llm.py` 的 `update_llm_config()` 中添加二次校验（防御纵深）

  **Must NOT do**:
  - 不修改已有 API 返回结构

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要理解 DNS 解析 + IP 地址段校验
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] `http://localhost:8080/v1` 被拒绝
  - [ ] `http://169.254.169.254` 被拒绝
  - [ ] `http://api.openai.com/v1` 被允许
  - [ ] `ruff check server/` 零错误

  **Commit**: `fix(security): SSRF 域名 DNS 解析校验`

---

- [x] 2. LLM 工具调用重试逻辑

  **What to do**:
  - 从 `chat_completion()` 提取重试逻辑为 `_retry_on_error()` 辅助函数
  - 在 `chat_completion_with_tools()` 和 `chat_completion_stream_with_tools()` 中复用
  - 429 限流：指数退避重试（最多 3 次）
  - 5xx 服务端错误：递增延迟重试（最多 3 次）
  - 401/403 认证失败：不重试，直接抛异常

  **Must NOT do**:
  - 不修改 `chat_completion()` 的已有行为
  - 不修改已有函数签名

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要理解 HTTP 重试策略和幂等性
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] 429 限流后自动重试成功
  - [ ] 5xx 错误后自动重试成功
  - [ ] 401/403 不重试
  - [ ] `ruff check server/` 零错误

  **Commit**: `fix(llm): 工具调用函数添加 429/5xx 重试逻辑`

---

- [x] 3. API 认证覆盖补全

  **What to do**:
  - 为以下 8 个端点添加 `Depends(verify_api_key)`：
    - `POST /api/v2/paipan` (v2_analysis.py)
    - `POST /api/v2/analyze/compare` (v2_analysis.py)
    - `GET /api/v2/analysis/{id}` (v2_analysis.py)
    - `POST /api/v2/hehun` (v2_tools.py)
    - `POST /api/v2/reverse-lookup` (v2_tools.py)
    - `GET /api/v2/history` (v2_tools.py)
    - `GET /api/v2/fortune/daily/{id}` (v2_fortune.py)
    - `GET /api/v2/fortune/monthly/{id}` (v2_fortune.py)
  - `GET /api/v2/cities` 保持公开（城市坐标数据）

  **Must NOT do**:
  - 不修改已有认证端点的行为
  - 不删除 `?token=` query string 支持（单独处理）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 机械性添加 Depends 依赖，无复杂逻辑
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] 无 API Key 时返回 401
  - [ ] 有 API Key 时返回正常结果
  - [ ] `ruff check server/` 零错误

  **Commit**: `fix(security): 补全 8 个端点的 API 认证`

---

- [x] 4. llm.py 三模块拆分

  **What to do**:
  - 创建 `server/llm_client.py`（~370 行）：配置管理 + HTTP 调用 + 函数调用
  - 创建 `server/llm_context.py`（~530 行）：干支计算 + 上下文格式化 + 检索结果格式化 + 学校视角
  - 创建 `server/llm_prompts.py`（~560 行）：提示词模板 + 构建器
  - `server/llm.py` 改为 re-export shim（向后兼容）
  - 更新所有消费者的 import 路径

  **Must NOT do**:
  - 不修改已有函数签名
  - 不改变任何函数行为
  - 不修改 `server/analysis.py`

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 大文件拆分需要精确理解依赖关系
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] `from server.llm import chat_completion` 仍然可用（shim）
  - [ ] `ruff check server/` 零错误
  - [ ] `python -m pytest tests/test_llm.py -v` 全部通过

  **Commit**: `refactor(llm): 拆分为 llm_client/llm_context/llm_prompts 三模块`

---

- [x] 5. v2_chat.py ChatService 提取

  **What to do**:
  - 创建 `server/chat_service.py`
  - 提取 `prepare_chat_context()` 共享函数（~80 行）
  - `api_v2_chat` 和 `api_v2_chat_stream` 调用共享函数
  - 提取 `build_report_context()` 共享函数

  **Must NOT do**:
  - 不修改已有 API 返回结构
  - 不修改 `server/llm.py`

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要精确理解两个端点的共享逻辑
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] 两个 chat 端点行为不变
  - [ ] 重复代码消除
  - [ ] `ruff check server/` 零错误

  **Commit**: `refactor(chat): 提取 ChatService 消除重复代码`

---

- [x] 6. page.tsx Tab 组件拆分

  **What to do**:
  - 提取 `useAnalyzePageState` hook
  - 提取 7 个 Tab 子组件（BaziTab, DayunTab, DetailTab, ZiweiTab, DeepTab, AnalysisTab, ChatTab）
  - 提取布局组件（ActionBar, ErrorState, LoadingState, SummaryPills）
  - 创建 `ResponsiveTabPanel` 工具组件消除桌面/移动端重复
  - `page.tsx` 缩减至 ~200 行

  **Must NOT do**:
  - 不改变任何功能行为
  - 不修改 API 调用逻辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: 前端组件拆分 + 响应式布局
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] `pnpm build` 零错误
  - [ ] 所有 Tab 功能不变
  - [ ] 移动端布局不变

  **Commit**: `refactor(ui): page.tsx Tab 组件拆分`

---

- [x] 7. Property-based testing 核心计算

  **What to do**:
  - 在 `pyproject.toml` 添加 `hypothesis` 测试依赖
  - 创建 `tests/test_property.py`
  - 定义共享策略：`st_gan`, `st_zhi`, `st_bazi_parts`, `st_datetime_str`
  - 为 5 个核心函数编写 hypothesis 测试：
    1. `calc_element_forces` — 百分比求和 ~100、非负、键完整
    2. `judge_wangshuai` — 判定在闭合集合内、布尔标志一致、极值互斥
    3. `paipan_from_datetime` — 八字格式有效、日主合法、确定性
    4. `detect_relations` — 必需键存在、无重复、元素合法
    5. `screen_pattern` — 格局名非空、置信度在 [0,1]

  **Must NOT do**:
  - 不修改 `bazi_pro/core/` 中的任何文件
  - 不删除现有测试

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要深入理解核心函数的不变量
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_property.py -v` 全部通过
  - [ ] 5 个核心函数各有 2+ 个 hypothesis 测试
  - [ ] `ruff check tests/` 零错误

  **Commit**: `test: 添加 property-based testing 核心计算函数`

---

- [x] 8. 集成测试补充

  **What to do**:
  - 为新增的 SSRF 防护添加测试
  - 为 LLM 重试逻辑添加测试（mock 429/5xx 响应）
  - 为 ChatService 共享函数添加测试
  - 为 API 认证覆盖添加测试

  **Must NOT do**:
  - 不修改已有测试

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要 mock HTTP 响应和 SSE 流
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/ -q` 全部通过
  - [ ] 新增测试覆盖 SSRF/重试/认证

  **Commit**: `test: 补充 SSRF/重试/认证集成测试`

---

- [x] 9. 全量回归测试 + 代码审查

  **What to do**:
  - 运行 `ruff check server/ bazi_pro/ tests/`
  - 运行 `python -m pytest tests/ -q`
  - 运行 `python tests/run_golden.py`
  - 运行 `cd frontend && pnpm build`
  - 运行 `python scripts/doctor.py`
  - 代码审查所有变更文件

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 全量验证
  - **Skills**: []

  **Acceptance Criteria**:
  - [ ] 所有验证命令通过
  - [ ] 无新增 warning 或 error

  **Commit**: 无（验证任务）

---

## Commit Strategy

| Task | Commit Message |
|------|---------------|
| 1 | `fix(security): SSRF 域名 DNS 解析校验` |
| 2 | `fix(llm): 工具调用函数添加 429/5xx 重试逻辑` |
| 3 | `fix(security): 补全 8 个端点的 API 认证` |
| 4 | `refactor(llm): 拆分为 llm_client/llm_context/llm_prompts 三模块` |
| 5 | `refactor(chat): 提取 ChatService 消除重复代码` |
| 6 | `refactor(ui): page.tsx Tab 组件拆分` |
| 7 | `test: 添加 property-based testing 核心计算函数` |
| 8 | `test: 补充 SSRF/重试/认证集成测试` |

---

## Success Criteria

### 验证命令
```bash
ruff check server/ bazi_pro/ tests/  # Expected: 0 errors
python -m pytest tests/ -q            # Expected: all pass
python tests/run_golden.py            # Expected: 120/120
cd frontend && pnpm build             # Expected: 0 errors
python scripts/doctor.py              # Expected: all pass
```

### 评估目标
- 认证/访问控制: 2/4 → 3/4
- 复杂度管理: 3/4 → 4/4
- 测试验证: 4/4 保持
- 整体成熟度: 3.14 → 3.5+
