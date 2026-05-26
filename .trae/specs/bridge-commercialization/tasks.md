# Tasks

## 阶段 1：MVP 上线（最小可收费产品）

- [x] Task 1: 容器化部署 — 创建 Dockerfile 和 docker-compose.yml
  - [x] SubTask 1.1: 创建多阶段 Dockerfile（Python 基础镜像 + 依赖安装 + 应用代码）
  - [x] SubTask 1.2: 创建 docker-compose.yml（FastAPI + PostgreSQL + Redis 三服务编排）
  - [x] SubTask 1.3: 添加 .dockerignore 和环境变量模板 .env.example
  - [x] SubTask 1.4: 验证 `docker-compose up` 一键启动，健康检查通过

- [x] Task 2: PostgreSQL 持久化层 — 用户数据和分析历史存储
  - [x] SubTask 2.1: 设计数据库 schema（users、analyses、subscriptions 表）
  - [x] SubTask 2.2: 创建 database/ 模块（连接池、迁移脚本、CRUD 操作）
  - [x] SubTask 2.3: 实现 analyses 历史记录的存储和查询 API
  - [x] SubTask 2.4: 编写数据库迁移脚本（Alembic 或手动 SQL）
  - [x] SubTask 2.5: 集成到现有 server/app.py，替换内存 taskstore 为 PostgreSQL 后端

- [x] Task 3: 用户认证系统 — 注册/登录/OAuth
  - [x] SubTask 3.1: 创建 server/auth/ 模块（JWT 签发/验证、密码哈希）
  - [x] SubTask 3.2: 实现邮箱+密码注册和登录 API（/api/auth/register, /api/auth/login）
  - [x] SubTask 3.3: 实现微信 OAuth 2.0 登录流程
  - [x] SubTask 3.4: 升级 API 鉴权中间件，支持 JWT + API Key 双模式
  - [x] SubTask 3.5: 编写认证相关测试

- [x] Task 4: 支付集成 — 按次付费和包月订阅
  - [x] SubTask 4.1: 创建 server/billing/ 模块（订单模型、配额检查、余额管理）
  - [x] SubTask 4.2: 集成微信支付（统一下单 + 回调通知 + 签名验证）
  - [x] SubTask 4.3: 集成支付宝（手机网站支付 + 异步通知）
  - [x] SubTask 4.4: 实现包月订阅逻辑（创建/续费/过期检查）
  - [x] SubTask 4.5: 在 /api/analyze 端点增加配额/余额前置检查
  - [x] SubTask 4.6: 编写支付流程测试（mock 支付回调）

- [x] Task 5: 基础前端 SPA — 分析输入 → 结果展示 → 历史查看
  - [x] SubTask 5.1: 初始化前端项目（React + Vite + TailwindCSS 或 Next.js）
  - [x] SubTask 5.2: 实现登录/注册页面
  - [x] SubTask 5.3: 实现分析输入页面（八字信息表单 + 提交）
  - [x] SubTask 5.4: 实现结果展示页面（consumer 报告嵌入 + WebSocket 进度）
  - [x] SubTask 5.5: 实现历史记录页面（列表 + 详情查看）
  - [x] SubTask 5.6: 实现账户设置页面（余额/订阅状态/修改密码）

## 阶段 2：产品化（可规模化运营）

- [ ] Task 6: 管理后台
  - [ ] SubTask 6.1: 创建 admin/ 模块（管理员鉴权、角色权限）
  - [ ] SubTask 6.2: 实现用户管理页面（列表/搜索/封禁/详情）
  - [ ] SubTask 6.3: 实现用量统计仪表盘（日活/分析次数/付费转化）
  - [ ] SubTask 6.4: 实现财务报表页面（收入/退款/订阅统计）

- [ ] Task 7: 监控告警基础设施
  - [ ] SubTask 7.1: 集成 Prometheus 指标采集（请求 QPS/延迟/错误率/业务指标）
  - [ ] SubTask 7.2: 配置 Grafana 仪表盘模板
  - [ ] SubTask 7.3: 配置结构化日志（JSON 格式 + ELK 或 Loki）
  - [ ] SubTask 7.4: 配置告警规则（错误率 > 5%、延迟 P99 > 10s、服务不可用）

- [ ] Task 8: API 文档站
  - [ ] SubTask 8.1: 启用 Swagger/ReDoc 并配置完整示例
  - [ ] SubTask 8.2: 创建独立 API 文档站（MkDocs 或 Docusaurus）
  - [ ] SubTask 8.3: 编写快速入门指南、认证说明、错误码参考

- [ ] Task 9: 隐私合规
  - [ ] SubTask 9.1: 实现用户数据删除 API（GDPR/个保法"被遗忘权"）
  - [ ] SubTask 9.2: 敏感信息加密存储（用户 PII 字段 AES 加密）
  - [ ] SubTask 9.3: 编写隐私政策和用户协议
  - [ ] SubTask 9.4: 添加数据导出功能（用户可下载所有个人数据）

## 阶段 3：增长（市场拓展）

- [ ] Task 10: API 开放平台
  - [ ] SubTask 10.1: 开发者注册 → API Key 自动签发
  - [ ] SubTask 10.2: 开发者用量仪表盘和计费
  - [ ] SubTask 10.3: SDK 封装（Python/JavaScript）

- [ ] Task 11: 多语言支持
  - [ ] SubTask 11.1: 提取所有 UI 文本为 i18n 资源文件
  - [ ] SubTask 11.2: 英文翻译（核心术语 + 报告模板）
  - [ ] SubTask 11.3: 英文版 consumer 报告渲染

- [ ] Task 12: 移动端适配
  - [ ] SubTask 12.1: 将 consumer 报告改造为 PWA（离线缓存 + 添加到主屏幕）
  - [ ] SubTask 12.2: 或开发微信小程序版本

# Task Dependencies

- Task 2 (PostgreSQL) → Task 3 (用户认证), Task 4 (支付), Task 5 (前端历史)
- Task 3 (用户认证) → Task 4 (支付), Task 5 (前端登录)
- Task 1 (容器化) 可与 Task 2-5 并行
- Task 5 (前端) 依赖 Task 3 (认证) 和 Task 4 (支付) 的 API 就绪
- Task 6-9 (阶段 2) 均依赖 Task 1-5 (阶段 1) 完成
- Task 10-12 (阶段 3) 依赖 Task 6-9 (阶段 2) 完成
