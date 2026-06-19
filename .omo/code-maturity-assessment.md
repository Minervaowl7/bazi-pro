# bazi-pro 代码成熟度评估报告

**项目**: bazi-pro v6.0 — 八字+紫微斗数联合命理分析引擎
**平台**: Python 3.10+ / FastAPI / Next.js 16 / SQLite
**评估日期**: 2026-06-11
**评估框架**: Trail of Bits 9-Category Code Maturity v0.1.0

---

## 执行摘要

**整体成熟度**: **3.0 / 4.0 (Satisfactory)**

bazi-pro 是一个架构清晰、测试覆盖良好的命理分析引擎。核心计算层（`bazi_pro/core/`）纯确定性设计优秀，120 Golden Cases + 641 测试函数保障了计算正确性。Web 层（FastAPI + Next.js）功能完备，近期 v6.0 迭代大幅增强了紫微斗数、流式对话、和移动端体验。

**Top 3 优势**:
1. 确定性计算核心设计卓越（零 LLM 依赖，每句可追溯）
2. 测试覆盖全面（641 测试函数 + 120 Golden Cases + CI 矩阵）
3. 古籍对齐引擎（6 部经典 2964 条条文，BM25 检索）

**Top 3 缺口**:
1. LLM 调用无重试降级（chat_completion_with_tools 无 retry）
2. 安全加固不完整（部分端点缺认证、SSRF 防护仅限字面 IP）
3. 无 fuzzing / property-based testing

**优先建议**:
1. 为 LLM 工具调用函数添加 429/5xx 重试逻辑
2. 统一所有端点认证（Depends(verify_api_key)）
3. 引入 hypothesis 做 property-based testing

---

## 成熟度评分卡

| # | 类别 | 评分 | 分数 | 关键发现 |
|---|------|------|------|---------|
| 1 | 算术安全 | **Satisfactory** | 3/4 | 元素力量计算有 clamp(0,100)、百分比精度控制；无溢出风险（Python 任意精度） |
| 2 | 审计追踪 | **Satisfactory** | 3/4 | 55 条 logger 语句、结构化错误码、SSE 事件流；缺 metrics/alerting |
| 3 | 认证/访问控制 | **Moderate** | 2/4 | 20 个端点有 verify_api_key；但 SSRF 防护仅限字面 IP、无 RBAC |
| 4 | 复杂度管理 | **Satisfactory** | 3/4 | core/ 13 模块职责清晰；但 v2_chat.py 600+ 行、page.tsx 1000+ 行需拆分 |
| 5 | 去中心化 | **N/A** | - | 非区块链项目，不适用 |
| 6 | 文档 | **Strong** | 4/4 | README 详尽、AGENTS.md 21 条规则、docstring 覆盖率高、版本历史完整 |
| 7 | 交易排序风险 | **N/A** | - | 非 DeFi 项目，不适用 |
| 8 | 底层操作 | **Satisfactory** | 3/4 | 仅 shensha.py 有 subprocess 调用（Node.js），有超时+清理；无 assembly |
| 9 | 测试验证 | **Strong** | 4/4 | 641 测试函数 + 120 Golden Cases + CI 矩阵(3.10/3.11/3.12) + ruff + compile check |

**加权平均**（排除 N/A）: **(3+3+2+3+4+3+4) / 7 = 3.14 → Satisfactory**

---

## 详细分析

### 1. 算术安全 — Satisfactory (3/4)

**优势**:
- `calc_element_forces()` 对百分比做 clamp(0, 100)（`server/analysis.py`）
- Python 任意精度整数，无整数溢出风险
- 流年评分 `score_liunian_ohlc()` 对四维度做 `max(0, min(100, score))`

**缺口**:
- 无正式的公式规格文档（旺衰判定的数值权重散布在代码中）
- 边界值测试可加强（极端八字：全同天干/地支）

**证据**:
- `bazi_pro/core/elements.py` — `calc_element_forces()` 百分比计算
- `server/kline_ohlc.py:63` — `max(0, min(100, score))`

---

### 2. 审计追踪 — Satisfactory (3/4)

**优势**:
- 55 条 logger 语句覆盖关键路径
- 结构化错误码（`UNAUTHORIZED`/`NOT_FOUND`/`RATE_LIMITED` 等）
- SSE 事件流记录分析进度
- `bazi_pro/doctor.py` 16 项环境检查

**缺口**:
- 无 metrics 采集（Prometheus/Datadog）
- 无 alerting 配置
- 审计日志未持久化到独立存储

**证据**:
- `server/deps.py` — 结构化错误码
- `server/sse.py` — SSE 事件广播
- `bazi_pro/doctor.py` — 环境诊断

---

### 3. 认证/访问控制 — Moderate (2/4)

**优势**:
- 20 个端点有 `Depends(verify_api_key)` 保护
- Rate Limit 中间件（IP + API Key 维度）
- `hmac.compare_digest` 防时序攻击
- 请求体大小限制（`BAZI_MAX_PAYLOAD_BYTES`）

**缺口**:
- SSRF 防护仅限字面 IP（域名可绕过）
- 无 RBAC（所有用户权限相同）
- API Key 通过 Query String 传递（URL 泄露风险）
- 无 CSRF 防护

**证据**:
- `server/deps.py:71` — `hmac.compare_digest`
- `server/routes/v2_settings.py` — SSRF 防护（仅字面 IP）
- `server/app.py:206-224` — Rate Limit 中间件

---

### 4. 复杂度管理 — Satisfactory (3/4)

**优势**:
- `bazi_pro/core/` 13 模块职责单一（patterns/elements/strength/yongshen...）
- Schools 模块化（子平/盲派/新派独立文件 + 统一注册接口）
- Lazy loading 避免循环依赖

**缺口**:
- `v2_chat.py` 600+ 行（需拆分为 service 层）
- `page.tsx` 1000+ 行（需拆分 Tab 子组件）
- `llm.py` 1400+ 行（需拆分 prompt builder / client / tools）

**证据**:
- `bazi_pro/core/schools/` — 模块化设计
- `server/routes/v2_chat.py` — 609 行
- `frontend/src/app/analyze/[id]/page.tsx` — 1051 行
- `server/llm.py` — 1454 行

---

### 5. 去中心化 — N/A

非区块链项目，不适用。

---

### 6. 文档 — Strong (4/4)

**优势**:
- README 404 行，涵盖安装/架构/API/版本历史/依赖
- AGENTS.md 21 条开发规则 + 验证命令 + Key Gotchas
- 核心模块 docstring 覆盖率高
- 版本历史从 v3.5 到 v6.0 完整记录
- SKILL.md 1592 行（LLM 技能文档）

**缺口**:
- 无 ADR（架构决策记录）
- API 文档依赖 FastAPI 自动生成，无独立 OpenAPI spec

**证据**:
- `README.md` — 404 行完整文档
- `AGENTS.md` — 128 行开发规则
- `SKILL.md` — 1592 行技能文档

---

### 7. 交易排序风险 — N/A

非 DeFi 项目，不适用。但注意：Chat 端点无请求排队，高并发时 LLM 调用可能互相干扰。

---

### 8. 底层操作 — Satisfactory (3/4)

**优势**:
- `shensha.py` 的 Node.js subprocess 有 15 秒超时 + `finally` 清理临时文件
- 无 assembly / unsafe code
- SQLite 参数化查询（无 SQL 注入）

**缺口**:
- subprocess 使用 `mkstemp` 写入临时文件再执行（理论上可被符号链接攻击）
- 无 sandboxing（Node.js 进程可访问文件系统）

**证据**:
- `server/shensha.py:733` — `tempfile.mkstemp`
- `server/shensha.py:744` — 15 秒超时
- `server/db.py` — 参数化查询

---

### 9. 测试验证 — Strong (4/4)

**优势**:
- 641 测试函数（27 个测试文件）
- 120 Golden Cases（JSON 格式，可回归）
- CI 矩阵（Python 3.10/3.11/3.12）
- ruff lint + compile check + doctor + golden cases 全链路
- 5 个新增测试文件（test_tools.py/test_llm.py/test_db.py/test_ziwei.py/test_retrieve.py）

**缺口**:
- 无 fuzzing（hypothesis / atheris）
- 无 property-based testing
- 无性能基准测试（benchmark 目录存在但未集成 CI）

**证据**:
- `.github/workflows/ci.yml` — 完整 CI 流水线
- `tests/golden_cases/` — 120 个 JSON 文件
- `tests/test_tools.py` — 596 行工具测试
- `tests/test_llm.py` — 662 行 LLM 测试

---

## 改进路线图

### CRITICAL（立即修复）

| # | 问题 | 影响 | 修复方案 |
|---|------|------|---------|
| C1 | SSRF 防护仅限字面 IP | 域名可绕过（如 `localhost`、`metadata.google.internal`） | 添加域名黑名单 + DNS 解析校验 |
| C2 | chat_completion_with_tools 无重试 | LLM 429/5xx 直接失败 | 复用 chat_completion 的重试逻辑 |
| C3 | API Key Query String 泄露 | URL 中的 token 出现在日志/Referer | 移除 query string 认证，仅保留 header |

### HIGH（1-2 个月）

| # | 问题 | 影响 | 修复方案 |
|---|------|------|---------|
| H1 | v2_chat.py 600+ 行 | 维护困难，容易引入 bug | 拆分为 ChatService + 路由层 |
| H2 | page.tsx 1000+ 行 | Tab 切换性能差，代码难读 | 拆分 7 个 Tab 子组件 |
| H3 | 无 property-based testing | 边界值覆盖不足 | 引入 hypothesis 测试核心计算 |
| H4 | 无 metrics/alerting | 生产问题无法及时发现 | 添加 Prometheus metrics + 告警 |

### MEDIUM（2-4 个月）

| # | 问题 | 影响 | 修复方案 |
|---|------|------|---------|
| M1 | llm.py 1400+ 行 | 职责混杂 | 拆分 prompt_builder / client / tools |
| M2 | 无 ADR 文档 | 架构决策不可追溯 | 创建 docs/adr/ 目录 |
| M3 | 无性能基准测试 | 回归风险 | 集成 benchmark 到 CI |
| M4 | 无 fuzzing | 安全漏洞风险 | 引入 atheris 测试输入解析 |

---

## 总结

bazi-pro 是一个**架构成熟、测试完善**的命理分析引擎。核心计算层的纯确定性设计是最大亮点，文档覆盖也是业界少见的完整。

主要改进方向：
1. **安全加固**（SSRF、认证、密钥管理）
2. **代码拆分**（大文件 → 模块化）
3. **测试增强**（property-based、fuzzing、benchmark）

整体而言，这是一个**可以投入生产使用**的项目，但建议在部署前完成 CRITICAL 级别的安全修复。
