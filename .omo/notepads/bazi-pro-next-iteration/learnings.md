# Learnings

## 2026-06-11 Task: 初始化
- 项目: bazi-pro v5.3, 八字命理分析引擎
- 技术栈: Python 3.10+, FastAPI, SQLite, Next.js 16, React 19, Tailwind 4, Zustand, ECharts, GSAP
- 后端端口: 8711, 前端端口: 3000
- LLM: mimo-v2.5-pro (reasoning 模型, 返回 reasoning_content)
- iztro-py: 紫微斗数排盘依赖
- bazi_pro/core/ 纯确定性，禁止 LLM/I/O
- server/analysis.py 只追加不修改签名
- 120 Golden Cases 只增不减

## 2026-06-11 Task: BirthForm 移动端布局优化
- globals.css 中 .form-input 桌面端 height:38px，移动端通过 @media (max-width:639px) 覆盖为 min-height:44px + font-size:14px
- Tailwind 响应式前缀 sm: 断点 640px，移动端默认单列，sm 以上恢复多列
- 日期/时辰 grid-cols-1 sm:grid-cols-2，流派选择 grid-cols-1 sm:grid-cols-3
- 提交按钮 spinner 用 inline SVG nimate-spin + circle strokeDasharray 实现，无需额外依赖
- 深度解读按钮 spinner 仅在 status==="submitting" 时显示，非 submitting 时保留箭头图标
- page.tsx 不可修改（约束），其 px-6 + max-w-[480px] 在 375px 下留 327px 给卡片，足够单列布局

## 2026-06-11 Task: 创建骨架屏组件
- globals.css 已有 @keyframes shimmer 和 .animate-shimmer 类（线性渐变扫光，1.8s 循环）
- nimate-shimmer 使用 ackground: linear-gradient(90deg, var(--surface-2) 25%, var(--border-strong) 50%, var(--surface-2) 75%) + ackground-size: 200% 100%
- prefers-reduced-motion 由 globals.css 全局规则处理（所有 animation-duration 强制 0.01ms）
- cn() 工具函数在 @/lib/utils 中（简单的 filter(Boolean).join( )）
- ui/ 目录已有 Card/Badge/Button/Tabs/Accordion/Progress/Tooltip 等组件
- 骨架屏组件使用 ria-busy= true + ria-label 提供无障碍标注
- 所有颜色使用 CSS 变量（--surface-2, --border-subtle, --border），自动支持暗色模式
- ShimmerBar 作为基础原子，接受 width/height/rounded Tailwind 类名
- pnpm build 零错误通过

## 2026-06-11 Task: Chat 多轮对话上下文管理
- 对话摘要存储为 role='summary' 消息，复用 chat_messages 表
- token 估算: 中文约 1.5 字/token，英文约 4 字符/token
- 环境变量 BAZI_CHAT_CONTEXT_ROUNDS (默认10) 控制上下文轮数
- 环境变量 BAZI_CHAT_TOKEN_BUDGET (默认4000) 控制 token 预算
- 摘要生成使用 chat_completion() 复用 LLM 服务，temperature=0.3
- get_chat_messages 自动过滤 role='summary'，前端不展示摘要消息
- 流式端点 /api/v2/chat/stream 同样应用了上下文管理逻辑

## 2026-06-11 Task: ChatPanel SSE 流式渲染

### 后端改动
- server/llm.py: 新增 chat_completion_stream_typed() — 区分 easoning_content 和 content，yield {"type": "reasoning"|"token", "content": "..."} 字典
- server/routes/v2_chat.py: 新增 POST /api/v2/chat/stream SSE 端点，返回 StreamingResponse(media_type="text/event-stream")
- SSE event 格式: data: {"type": "token"|"reasoning"|"done"|"error", "content": "..."}\n\n
- 使用 X-Accel-Buffering: no header 确保 nginx 不缓冲

### 前端改动
- rontend/src/lib/api.ts: 新增 sendChatMessageStream() — 使用 etch() + ReadableStream 消费 SSE（EventSource 不支持自定义 Header）
- rontend/src/components/ChatPanel.tsx: 全面改写支持流式渲染
  - streamingContent / streamingReasoning 状态跟踪流式内容
  - ReasoningBlock 组件：reasoning_content 折叠面板（默认折叠）
  - 60 秒失速检测（复用 analysisStore 的模式）
  - 流式中断时显示 "连接中断，请重试"
  - 生成中状态指示器（绿色脉冲点）
  - 光标动画（闪烁竖线）表示正在输入
  - 停止按钮可中断流式

### 关键设计决策
- 不修改 chat_completion_stream() 签名，新增 chat_completion_stream_typed() 保持向后兼容
- 使用 etch + ReadableStream 而非 EventSource，因为需要自定义 X-API-Key header
- contentRef 用于在回调中累积内容，避免 React 状态闭包问题
- 旧的非流式 POST /api/v2/chat 端点保留不变

## 2026-06-11 Task: 分析页移动端布局优化

### 设计系统要点
- 移动端断点: sm: = 640px (Tailwind 默认), max-width: 639px 为移动端
- Z-index 层级: --z-navbar: 50, --z-dropdown: 40, 底部 Tab 用 45
- 已有 Accordion/AccordionItem 组件在 ui/Accordion.tsx，支持 defaultOpen
- 毛玻璃效果: backdrop-filter: blur(24px) saturate(1.3) + color-mix 92% 透明
- safe-area-inset-bottom: env(safe-area-inset-bottom, 0px) 处理 iPhone 底部安全区

### 移动端布局策略
- 桌面端/移动端双版本渲染: hidden sm:block + sm:hidden 分别控制
- 底部 Tab 固定导航替代桌面端顶部 Tab 分段控制器
- 摘要条 grid-cols-3 → grid-cols-2 (移动端), sm:grid-cols-5 lg:grid-cols-6
- 面板可折叠: 移动端用 AccordionItem 包裹，默认展开常用面板
- 操作栏按钮: px-3.5→px-2.5, text-[13px]→text-[12px], gap-2.5→gap-1.5

### ECharts 响应式
- echarts-for-react 支持 autoresize 属性，自动响应容器尺寸变化
- globals.css 添加 @media (max-width:639px) 规则强制 ECharts 容器 100% 宽度
- RelationGraph: style={{ height: 260, width: "100%" }} + autoresize
- LifeKlineChart: style={{ height: "min(420px, 60vw)" }} 已自带响应式

### 骨架屏移动端
- SkeletonCard grid-cols-4 → grid-cols-2 sm:grid-cols-4
