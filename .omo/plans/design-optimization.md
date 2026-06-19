# bazi-pro 前端设计优化计划

## TL;DR

> **核心目标**: 修复设计缺陷、统一设计系统、提升性能和无障碍。
>
> **交付物**:
> - 暗色模式可读性修复
> - 设计 Token 统一（ZiweiPanel + 学校面板 + 维度面板）
> - ECharts 内存泄漏修复
> - 表单无障碍修复
> - 模态框焦点陷阱
> - 移动端布局优化
> - SEO 元数据补全
>
> **预估周期**: 2-3 周
> **并行执行**: YES - 3 波次

---

## Context

### 审查发现汇总

| 类别 | 问题数 | CRITICAL | HIGH | MEDIUM | LOW |
|------|--------|----------|------|--------|-----|
| 色彩一致性 | ~148 处硬编码 | 1 | 3 | 2 | 0 |
| 无障碍 | 8 项 | 0 | 3 | 3 | 2 |
| 性能 | 5 项 | 0 | 2 | 2 | 1 |
| 一致性 | 12 项 | 0 | 2 | 5 | 5 |
| SEO | 4 项 | 0 | 1 | 2 | 1 |

---

## Work Objectives

### Must Have
- ChatPanel 暗色模式可读性
- ZiweiPanel 设计 Token 化
- ECharts 内存泄漏修复
- 表单标签关联
- 模态框焦点陷阱

### Must NOT Have
- 不改变任何功能行为
- 不修改后端代码
- 不引入新的重依赖

---

## Execution Strategy

### Wave 1: 关键修复（5 任务并行）
- T1: ChatPanel 暗色模式 + 硬编码颜色清理
- T2: ZiweiPanel 设计 Token 化
- T3: ECharts 内存泄漏修复
- T4: 表单无障碍修复
- T5: 模态框焦点陷阱

### Wave 2: 一致性提升（4 任务并行）
- T6: 学校/维度面板颜色 Token 化
- T7: ErrorBoundary 提取 + ErrorMessage 组件
- T8: 移动端布局优化
- T9: SEO 元数据补全

### Wave 3: 性能优化（3 任务并行）
- T10: ECharts 响应式 resize
- T11: GSAP 动画优化（无限循环 → IntersectionObserver）
- T12: 无用依赖清理 + ScrollTrigger 移除

---

## TODOs

- [ ] 1. ChatPanel 暗色模式 + 硬编码颜色清理

  **What to do**:
  - `ChatPanel.tsx:504` 用户气泡文字改为 `color: var(--surface)`
  - `ChatPanel.tsx:457` 硬编码 `#2ecc71` 改为 `var(--success)`
  - `ChatPanel.tsx:447,488,518` 硬编码 `#c0392b` 改为 `var(--danger)`

  **Commit**: `fix(ui): ChatPanel 暗色模式可读性 + 硬编码颜色清理`

---

- [ ] 2. ZiweiPanel 设计 Token 化

  **What to do**:
  - `ZiweiPanel.tsx` 全部 14 处 Tailwind 色彩类替换为 CSS 变量
  - `bg-purple-100` → `var(--wx-water-bg)` 或新 CSS 变量
  - `text-gray-600` → `var(--text-2)`
  - `border-gray-200` → `var(--border)`

  **Commit**: `fix(ui): ZiweiPanel 设计 Token 化`

---

- [ ] 3. ECharts 内存泄漏修复

  **What to do**:
  - `LifeKlineChart.tsx` 添加 `useEffect` cleanup 调用 `chart.dispose()`
  - `RelationGraph.tsx` 同上
  - `ReportCharts.tsx` 同上
  - 添加 `autoresize` prop 处理窗口 resize

  **Commit**: `fix(perf): ECharts 实例 dispose + resize 处理`

---

- [ ] 4. 表单无障碍修复

  **What to do**:
  - `BirthForm.tsx` 所有输入添加 `id`，标签添加 `htmlFor`
  - 城市下拉添加键盘导航（Arrow/Enter/Escape）
  - 学校卡片添加 `role="radiogroup"` / `role="radio"`
  - 错误消息添加 `aria-live="polite"`

  **Commit**: `fix(a11y): BirthForm 标签关联 + 键盘导航 + ARIA`

---

- [ ] 5. 模态框焦点陷阱

  **What to do**:
  - `ReportPreviewModal.tsx` 添加焦点陷阱
  - 关闭按钮添加 `aria-label`
  - ESC 键关闭功能

  **Commit**: `fix(a11y): ReportPreviewModal 焦点陷阱`

---

- [ ] 6. 学校/维度面板颜色 Token 化

  **What to do**:
  - 新增 CSS 变量：`--school-mangpai: #a855f7`, `--school-xinpai: #22c55e`
  - `SchoolPanel.tsx` ~30 处硬编码替换
  - `SchoolComparePanel.tsx` ~20 处硬编码替换
  - `JointAnalysisPanel.tsx` ~10 处硬编码替换
  - `DimensionAnalysisPanel.tsx` ~12 处硬编码替换
  - `ZiweiNarrationPanel.tsx` ~12 处硬编码替换

  **Commit**: `fix(ui): 学校/维度面板颜色 Token 化`

---

- [ ] 7. ErrorBoundary 提取 + ErrorMessage 组件

  **What to do**:
  - 提取共享 `ErrorBoundary` 组件到 `components/ui/ErrorBoundary.tsx`
  - 创建 `ErrorMessage` 组件统一错误显示
  - 3 个页面的 ErrorBoundary 改为引用共享组件

  **Commit**: `refactor(ui): 提取共享 ErrorBoundary + ErrorMessage`

---

- [ ] 8. 移动端布局优化

  **What to do**:
  - `page.tsx:244` 功能卡片改为 `grid-cols-1 sm:grid-cols-3`
  - `ChatPanel.tsx` 移动端 padding 优化
  - `ZiweiPanel.tsx` 移动端卡片布局替代表格

  **Commit**: `fix(ui): 移动端布局优化`

---

- [ ] 9. SEO 元数据补全

  **What to do**:
  - `analyze/[id]/page.tsx` 添加 `generateMetadata`（日主、格局、用神）
  - `report/[id]/page.tsx` 添加 `generateMetadata`
  - `compare/page.tsx` 添加 `generateMetadata`
  - `layout.tsx` 添加 `twitter:image`
  - `not-found.tsx` 移除 `"use client"` 允许静态生成

  **Commit**: `fix(seo): 动态页面元数据 + Twitter Card`

---

- [ ] 10. ECharts 响应式 resize

  **What to do**:
  - 所有 ECharts 组件添加 `autoresize` prop
  - 或监听 `window.resize` 事件手动触发 `chart.resize()`

  **Commit**: `fix(perf): ECharts 响应式 resize`

---

- [ ] 11. GSAP 动画优化

  **What to do**:
  - `DayunTimeline.tsx:175-178` 无限脉冲动画改为 IntersectionObserver 控制
  - 组件不可见时暂停动画

  **Commit**: `fix(perf): GSAP 无限动画 IntersectionObserver 控制`

---

- [ ] 12. 无用依赖清理

  **What to do**:
  - `package.json` 移除 `html2pdf.js`（未使用）
  - `gsap.ts` 移除未使用的 `ScrollTrigger` import
  - `globals.css` 修复 `select.form-input` 硬编码箭头颜色

  **Commit**: `chore: 清理无用依赖 + 修复硬编码`

---

## Commit Strategy

| Task | Commit Message |
|------|---------------|
| 1 | `fix(ui): ChatPanel 暗色模式可读性 + 硬编码颜色清理` |
| 2 | `fix(ui): ZiweiPanel 设计 Token 化` |
| 3 | `fix(perf): ECharts 实例 dispose + resize 处理` |
| 4 | `fix(a11y): BirthForm 标签关联 + 键盘导航 + ARIA` |
| 5 | `fix(a11y): ReportPreviewModal 焦点陷阱` |
| 6 | `fix(ui): 学校/维度面板颜色 Token 化` |
| 7 | `refactor(ui): 提取共享 ErrorBoundary + ErrorMessage` |
| 8 | `fix(ui): 移动端布局优化` |
| 9 | `fix(seo): 动态页面元数据 + Twitter Card` |
| 10 | `fix(perf): ECharts 响应式 resize` |
| 11 | `fix(perf): GSAP 无限动画 IntersectionObserver 控制` |
| 12 | `chore: 清理无用依赖 + 修复硬编码` |

---

## Success Criteria

### 验证命令
```bash
cd frontend && pnpm build             # Expected: 0 errors
ruff check server/ bazi_pro/ tests/   # Expected: 0 errors
python -m pytest tests/ -q            # Expected: all pass
```

### 设计质量目标
- 色彩一致性: C+ (68) → A- (90)
- 无障碍: B (76) → A- (90)
- 性能: B (78) → A- (92)
- 整体评分: B- (72) → A- (91)
