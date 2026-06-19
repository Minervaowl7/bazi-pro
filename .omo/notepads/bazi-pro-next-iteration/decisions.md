# Decisions

## 2026-06-11 Task: 初始化
- 三波并行执行策略: Wave 1 (6任务) → Wave 2 (7任务) → Wave 3 (5任务) → Final (4任务)
- Wave 1 无依赖，可全部并行
- 前端不引入新重依赖（禁止 Redux）
- Chat 流式化复用现有 chat_completion_stream()
