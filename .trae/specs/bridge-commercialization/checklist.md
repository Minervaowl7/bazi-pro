# 商业化差距分析 Checklist

## 阶段 1：MVP 上线

### 容器化部署
- [x] Dockerfile 存在且可通过 `docker build` 构建成功
- [x] docker-compose.yml 包含 FastAPI + PostgreSQL + Redis 三个服务
- [x] `docker-compose up` 一键启动后 `/api/health` 返回 200
- [x] .env.example 包含所有必需环境变量及说明

### PostgreSQL 持久化
- [x] 数据库 schema 包含 users、analyses、subscriptions 表
- [x] 迁移脚本可从空库创建完整 schema
- [x] 分析历史 API `/api/history` 返回当前用户的历史记录
- [x] 内存 taskstore 在 PostgreSQL 可用时自动切换

### 用户认证
- [x] `/api/auth/register` 邮箱注册成功返回 JWT
- [x] `/api/auth/login` 登录成功返回 JWT
- [x] 微信 OAuth 回调完成登录流程
- [x] JWT 和 API Key 双模式鉴权均可用
- [x] 无效 JWT 返回 401

### 支付集成
- [x] 微信支付下单 API 返回预支付参数
- [x] 微信支付回调验证签名并更新订单状态
- [x] 支付宝下单和回调流程完整
- [x] 余额不足时 /api/analyze 返回 402
- [x] 包月订阅创建、续费、过期检查逻辑正确

### 前端 SPA
- [x] 登录/注册页面可用
- [x] 分析输入页面可提交八字信息
- [x] 结果页面可展示 consumer 报告
- [x] 历史记录页面可查看和重新打开历史分析
- [x] 账户设置页面可查看余额和订阅状态

## 阶段 2：产品化

### 管理后台
- [ ] 管理员可查看用户列表和详情
- [ ] 用量统计仪表盘展示日活/分析次数/付费转化
- [ ] 财务报表展示收入/退款/订阅统计

### 监控告警
- [ ] Prometheus 指标端点 `/metrics` 可采集
- [ ] Grafana 仪表盘展示 QPS/延迟/错误率
- [ ] 错误率超阈值触发告警通知

### API 文档
- [ ] Swagger UI 可访问且包含完整示例
- [ ] 独立文档站包含快速入门、认证说明、错误码参考

### 隐私合规
- [ ] 用户可请求删除所有个人数据
- [ ] PII 字段加密存储
- [ ] 隐私政策页面公开可访问
- [ ] 用户可导出所有个人数据

## 阶段 3：增长

### API 开放平台
- [ ] 开发者可自助注册获取 API Key
- [ ] 开发者仪表盘展示用量和计费

### 多语言
- [ ] 英文版 consumer 报告可正常渲染
- [ ] UI 文本全部通过 i18n 资源文件加载

### 移动端
- [ ] PWA 可添加到主屏幕并离线访问
- [ ] 或微信小程序可正常使用核心功能
