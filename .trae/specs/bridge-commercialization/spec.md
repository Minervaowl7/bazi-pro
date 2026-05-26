# bazi-pro 商业化差距分析与路线图 Spec

## Why

bazi-pro v5.0 已具备完整的命理计算引擎、证据链推理、多模式报告渲染和 FastAPI 服务层，但距离可面向用户收费的商业产品仍有显著差距：缺少用户系统、支付集成、容器化部署、生产级监控等关键基础设施。本 spec 系统梳理现状与差距，规划分阶段商业化路径。

## 现状盘点

### ✅ 已具备（技术底座扎实）

| 维度 | 现状 | 关键文件 |
|------|------|----------|
| 核心引擎 | 确定性命理计算（十神/藏干/五行/旺衰/格局/喜用神/刑冲合害），98 项 golden 回归测试 | `bazi_pro/core/` |
| 古籍检索 | BM25 + jieba，2964 条语料，6 部经典 | `bazi_pro/retrieve_classical.py` |
| 证据链 | 结构化推理 + 置信度 + 反证 | `bazi_pro/evidence.py`, `bazi_pro/trace.py` |
| 报告渲染 | 三种模式（report/dashboard/consumer），术语词典，SVG 图表 | `bazi_pro/ui/` |
| API 服务 | FastAPI，4 个端点（analyze/status/result/ws），API Key 鉴权 | `server/app.py` |
| 输入校验 | Pydantic schema，天干地支格式验证 | `server/schemas.py` |
| 安全中间件 | CORS、TrustedHost、安全头、请求体大小限制、速率限制 | `server/app.py` |
| 缓存/存储 | Redis 优先 + 内存降级，LRU + TTL | `server/cache.py`, `server/taskstore.py` |
| 速率限制 | Redis/内存双后端，可配置窗口 | `server/ratelimiter.py` |
| WebSocket | 多连接管理，进度推送 | `server/ws.py` |
| CI/CD | GitHub Actions：lint + 编译 + 审计 + 测试 + 构建校验 | `.github/workflows/ci.yml` |
| 插件系统 | `plugins/` 目录，BaziPlugin ABC，on_retrieve/on_evidence/on_render | `plugins/loader.py` |
| 测试体系 | 98 golden + 62 consumer + 专项审计脚本 | `tests/`, `scripts/audit_*.py` |

### ❌ 缺失（商业化必需）

| 维度 | 差距 | 严重度 |
|------|------|--------|
| 用户系统 | 无注册/登录/OAuth，无用户画像，无会话持久化 | 🔴 阻塞 |
| 支付计费 | 无支付集成、无订阅管理、无用量计费、无配额管理 | 🔴 阻塞 |
| 容器化部署 | 无 Dockerfile、无 docker-compose、无 K8s manifest | 🔴 阻塞 |
| 生产数据库 | 无持久化用户数据存储（仅 Redis/内存任务存储） | 🔴 阻塞 |
| 前端应用 | 仅有 API 演示页，无独立前端 SPA | 🟡 重要 |
| 监控告警 | 无 APM、无日志聚合、无指标采集、无告警 | 🟡 重要 |
| API 文档 | Swagger/ReDoc 默认关闭，无公开 API 文档站 | 🟡 重要 |
| 隐私合规 | 无隐私政策、无数据删除机制、无 GDPR/个保法适配 | 🟡 重要 |
| 多语言 | 仅中文，无 i18n 框架 | 🟢 可选 |
| 移动端 | 无原生/混合 App，consumer 报告有移动端 CSS 但非 PWA | 🟢 可选 |

## 商业化分阶段路线图

### 阶段 1：MVP 上线（最小可收费产品）

**目标**：用户可通过 Web 注册 → 付费 → 获取命理分析报告

**核心差距**：
1. 用户注册/登录系统（邮箱 + OAuth）
2. 分析历史记录持久化（PostgreSQL）
3. 支付集成（微信支付/支付宝 或 Stripe）
4. 容器化部署（Docker + docker-compose）
5. 基础前端（分析输入 → 结果展示 → 历史查看）

**预估工作量**：6-8 周

### 阶段 2：产品化（可规模化运营）

**目标**：多租户 SaaS，自助服务，运营数据可观测

**核心差距**：
1. 订阅/计费系统（免费额度 + 按次/包月）
2. 管理后台（用户管理、用量统计、财务报表）
3. 监控告警（Prometheus + Grafana 或 Datadog）
4. API 文档站 + 开发者门户
5. 隐私合规（数据删除、加密存储、隐私政策）

**预估工作量**：4-6 周

### 阶段 3：增长（市场拓展）

**目标**：多渠道获客，API 开放平台，品牌差异化

**核心差距**：
1. API 开放平台（开发者注册 → API Key → 调用 → 计费）
2. 多语言支持（英文版报告）
3. 移动端适配（PWA 或小程序）
4. SEO + 内容营销（命理知识库、免费基础解读引流）
5. 合作伙伴/白标方案

**预估工作量**：8-12 周

## What Changes

- 新增用户认证系统（注册/登录/OAuth/会话管理）
- 新增 PostgreSQL 持久化层（用户、分析历史、订阅）
- 新增支付集成模块
- 新增 Dockerfile + docker-compose.yml
- 新增前端 SPA（React/Vue 或服务端渲染）
- 新增管理后台
- 新增监控/日志/告警基础设施
- 新增 API 文档站
- 新增隐私合规机制
- **BREAKING**: API 鉴权从单一 API Key 升级为用户级 JWT + API Key 双模式

## Impact

- Affected specs: 用户系统、API 鉴权、数据存储、计费、部署
- Affected code: `server/app.py`（鉴权重构）、`server/schemas.py`（新增用户/订单模型）、`server/taskstore.py`（扩展为通用存储）、`pyproject.toml`（新增依赖）

## ADDED Requirements

### Requirement: 用户认证系统

系统 SHALL 提供用户注册（邮箱+密码）、登录（JWT）、OAuth 2.0（微信/GitHub）功能。

#### Scenario: 用户注册
- **WHEN** 用户提交邮箱和密码
- **THEN** 系统创建账户，发送验证邮件，返回 JWT token

#### Scenario: OAuth 登录
- **WHEN** 用户通过微信/GitHub OAuth 授权
- **THEN** 系统创建或关联账户，返回 JWT token

### Requirement: 分析历史持久化

系统 SHALL 将每次分析请求和结果持久化到 PostgreSQL，用户可查看历史记录。

#### Scenario: 查看历史
- **WHEN** 已登录用户请求历史列表
- **THEN** 返回该用户所有历史分析记录（含时间、八字、状态）

### Requirement: 支付与计费

系统 SHALL 支持按次付费和包月订阅两种模式，集成微信支付/支付宝。

#### Scenario: 按次付费
- **WHEN** 用户发起分析请求且账户余额不足
- **THEN** 系统引导支付，支付成功后执行分析

#### Scenario: 包月订阅
- **WHEN** 用户订阅月度套餐
- **THEN** 在有效期内可无限次使用分析功能

### Requirement: 容器化部署

系统 SHALL 提供 Dockerfile 和 docker-compose.yml，支持一键部署（含 FastAPI + PostgreSQL + Redis）。

#### Scenario: 一键部署
- **WHEN** 运行 `docker-compose up`
- **THEN** 所有服务启动，健康检查通过，API 可用

### Requirement: 前端应用

系统 SHALL 提供独立前端 SPA，包含：分析输入页、结果展示页、历史记录页、账户设置页。

#### Scenario: 完整用户流程
- **WHEN** 用户登录后输入八字信息
- **THEN** 系统展示分析进度和 consumer 报告结果

### Requirement: 监控告警

系统 SHALL 采集请求指标（QPS/延迟/错误率）、业务指标（分析次数/付费转化），支持告警。

#### Scenario: 异常告警
- **WHEN** API 错误率超过 5%
- **THEN** 触发告警通知

### Requirement: 隐私合规

系统 SHALL 提供数据删除功能（用户可请求删除所有个人数据），敏感信息加密存储，公开隐私政策。

#### Scenario: 数据删除
- **WHEN** 用户请求删除账户
- **THEN** 系统在 30 天内删除所有关联数据

## MODIFIED Requirements

### Requirement: API 鉴权

现有单一 API Key 鉴权 SHALL 升级为 JWT（用户级）+ API Key（开发者级）双模式，保持向后兼容。

#### Scenario: JWT 鉴权
- **WHEN** 用户通过前端发起请求
- **THEN** 系统验证 JWT token，关联用户身份

#### Scenario: API Key 鉴权（向后兼容）
- **WHEN** 开发者通过 X-API-Key 发起请求
- **THEN** 系统验证 API Key，关联开发者账户

## REMOVED Requirements

无移除项。所有现有功能保持向后兼容。
