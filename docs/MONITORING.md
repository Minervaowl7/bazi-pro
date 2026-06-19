# 监控与事件响应手册

本文档描述 bazi-pro 的监控策略、告警阈值、日志审查流程和事件响应手册。

---

## 1. 监控指标

### 1.1 核心指标

| 指标名称 | 类型 | 说明 | 获取方式 |
|----------|------|------|---------|
| `bazi_requests_total` | Counter | HTTP 请求总数 | `/metrics` |
| `bazi_request_duration_seconds` | Histogram | 请求延迟 | `/metrics` |
| `bazi_analysis_total` | Counter | 分析请求总数 | `/metrics` |
| `bazi_analysis_duration_seconds` | Histogram | 分析延迟 | `/metrics` |
| `bazi_cache_hits_total` | Counter | 缓存命中次数 | `/metrics` |
| `bazi_cache_misses_total` | Counter | 缓存未命中次数 | `/metrics` |
| `bazi_errors_total` | Counter | 5xx 错误总数 | `/metrics` |
| `bazi_rate_limited_total` | Counter | 被限流请求总数 | `/metrics` |

### 1.2 健康检查端点

```
GET /api/health
```

返回示例：
```json
{
    "version": "5.0.0",
    "cache_backend": "redis",
    "task_store_backend": "redis",
    "rate_limiter_backend": "redis",
    "degraded": ["rate_limiter: redis degraded, using memory fallback"]
}
```

**关键字段**：
- `degraded`: 存在时表示有组件降级，需要关注
- `cache_backend`: `redis` 或 `lru_memory`
- `task_store_backend`: `redis`、`redis(degraded)` 或 `memory`

---

## 2. 告警阈值

### 2.1 CRITICAL（立即响应）

| 条件 | 告警消息 | 可能原因 |
|------|---------|---------|
| 错误率 > 10%（5 分钟窗口） | "高错误率告警" | 代码 bug、依赖故障 |
| `/api/health` 返回 degraded | "组件降级" | Redis 不可用 |
| 分析延迟 p99 > 30s | "分析延迟异常" | LLM 超时、资源不足 |
| SQLite 数据库文件不存在 | "数据库丢失" | 磁盘故障、误删除 |

### 2.2 WARNING（1 小时内响应）

| 条件 | 告警消息 | 可能原因 |
|------|---------|---------|
| 错误率 > 5%（5 分钟窗口） | "错误率升高" | 边界情况、输入异常 |
| 缓存命中率 < 30%（1 小时窗口） | "缓存命中率低" | 缓存过期、流量模式变化 |
| 限流触发 > 10 次/分钟 | "频繁限流" | 可能的滥用或 DDoS |
| 分析延迟 p95 > 10s | "分析延迟升高" | LLM 响应慢 |

### 2.3 INFO（日常关注）

| 条件 | 说明 |
|------|------|
| Redis 降级为内存 | 关注 Redis 恢复 |
| 新版本部署 | 确认健康检查通过 |
| BM25 索引预热失败 | 首次请求会延迟 |

---

## 3. 日志审查流程

### 3.1 日志级别

| 级别 | 含义 | 审查频率 |
|------|------|---------|
| ERROR | 严重错误，需要立即处理 | 每日 |
| WARNING | 异常情况，可能需要处理 | 每日 |
| INFO | 正常操作记录 | 每周 |
| DEBUG | 调试信息（生产环境关闭） | 仅调试时 |

### 3.2 关键日志模式

```
# 需要立即关注的日志
ERROR.*Unhandled           # 未捕获异常
ERROR.*run_analysis failed # 分析失败
WARNING.*Redis.*failed     # Redis 连接失败
WARNING.*degraded          # 组件降级
ERROR.*API key not configured in production  # 生产环境未配置 API key
```

### 3.3 日志审查检查清单

每日审查：
- [ ] 检查 ERROR 日志数量和模式
- [ ] 检查 WARNING 日志中的 Redis/缓存问题
- [ ] 检查 `/api/health` 端点状态
- [ ] 检查错误率趋势

每周审查：
- [ ] 分析请求量趋势
- [ ] 检查缓存命中率趋势
- [ ] 审查限流触发情况
- [ ] 检查磁盘空间（SQLite 数据库）

---

## 4. 事件响应手册

### 4.1 Redis 不可用

**症状**：
- `/api/health` 返回 `degraded`
- 日志出现 `Redis connection failed`

**影响**：
- 缓存降级为内存 LRU（容量有限）
- 任务存储降级为内存（重启丢失）
- 限流降级为内存（多实例不共享）

**响应步骤**：
1. 检查 Redis 进程状态：`systemctl status redis` 或 `docker ps | grep redis`
2. 检查 Redis 连接：`redis-cli ping`
3. 检查 Redis 日志：`journalctl -u redis` 或 `docker logs redis`
4. 如果 Redis 无法恢复，确认内存降级正常工作
5. 通知团队 Redis 状态

**恢复**：
- Redis 恢复后，系统自动重新连接
- 内存中的缓存数据不会同步到 Redis

### 4.2 LLM API 超时

**症状**：
- 分析请求延迟异常高
- 日志出现 LLM 调用超时

**影响**：
- LLM 辅助解读功能不可用
- 核心计算功能不受影响

**响应步骤**：
1. 检查 LLM API 状态（OpenAI/DeepSeek/通义千问）
2. 检查网络连接
3. 如果 LLM 不可用，系统会跳过 LLM 解读部分
4. 考虑临时禁用 LLM 功能：设置 `LLM_API_KEY=""`

### 4.3 SQLite 数据库问题

**症状**：
- 分析结果无法保存
- 历史记录查询失败

**影响**：
- 分析功能正常（不依赖数据库）
- 历史记录和聊天功能不可用

**响应步骤**：
1. 检查磁盘空间：`df -h`
2. 检查数据库文件权限：`ls -la bazi_pro.db`
3. 检查数据库完整性：`sqlite3 bazi_pro.db "PRAGMA integrity_check;"`
4. 如果数据库损坏，从备份恢复或删除重建

### 4.4 高错误率

**症状**：
- 错误率 > 10%
- 大量 5xx 错误

**影响**：
- 用户请求失败

**响应步骤**：
1. 检查错误日志，识别错误类型
2. 检查最近的代码部署
3. 如果是新部署引起，考虑回滚
4. 如果是输入数据问题，检查输入验证逻辑

### 4.5 DDoS / 滥用

**症状**：
- 限流触发频率异常高
- 请求量突然增加
- 来自单一 IP 的大量请求

**响应步骤**：
1. 检查限流日志，识别来源 IP
2. 考虑临时降低限流阈值
3. 在防火墙层面封锁恶意 IP
4. 考虑启用更严格的 CORS 策略

---

## 5. 监控配置示例

### 5.1 Prometheus 配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'bazi-pro'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8711']
    metrics_path: '/metrics/text'
```

### 5.2 Grafana Dashboard

推荐面板：
1. 请求量（QPS）趋势图
2. 延迟分布（p50/p95/p99）
3. 错误率趋势图
4. 缓存命中率
5. 分析请求量按流派分类
6. 限流触发次数

---

## 6. 运维检查清单

### 日常检查

- [ ] `/api/health` 返回正常
- [ ] 无 CRITICAL 告警
- [ ] 错误率在正常范围
- [ ] 磁盘空间充足

### 每周检查

- [ ] 审查日志趋势
- [ ] 检查缓存命中率
- [ ] 检查数据库大小
- [ ] 确认备份正常

### 每月检查

- [ ] 安全更新
- [ ] 依赖更新
- [ ] 性能基准测试
- [ ] 灾难恢复演练
