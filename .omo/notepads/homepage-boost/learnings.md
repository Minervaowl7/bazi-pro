
## 首页优化完成 (2026-06-11)

### 完成内容
1. SEO meta 标签完善 - layout.tsx 增加了更详细的 title、description、og:tags、twitter:tags
2. 示例命盘按钮 - page.tsx 表单下方添加"试试示例命盘"按钮，预设数据 1990-05-15 辰时 男
3. 功能亮点展示 - 3 个卡片：紫微命盘、三流派对比、AI 智能解读
4. GSAP 动画 - 新元素（demo 按钮、功能卡片）都添加了入场动画，支持 stagger 效果
5. CSS 变量 - 所有颜色、背景、边框都使用 CSS 变量，自动适配暗色模式

### 技术要点
- 示例命盘流程：submitPaipan → 获取排盘结果 → startAnalysis → 跳转 /analyze/{id}
- 功能卡片使用五行色系：紫微(火)、三流派(水)、AI(木)
- 新增 CSS 类：.hero-demo-btn、.hero-features、.feature-card 添加到 GSAP fallback 列表
- TypeScript 和 ESLint 检查通过，pnpm build 零错误

### 设计系统遵循
- 所有颜色引用 CSS 变量（var(--ink)、var(--text-2)、var(--cinnabar) 等）
- 间距使用 Tailwind 标准类（gap-3、p-4、mt-5 等）
- 圆角使用设计系统变量（var(--r)、var(--r-sm)）
- 阴影使用设计系统变量（var(--shadow-card)）
