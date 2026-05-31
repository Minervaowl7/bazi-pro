# 🎨 bazi-pro 前端设计迁移指南
## 目标参考：ba-zi.ai/calculator（观象八字）

> 本文档提取自 https://www.ba-zi.ai/calculator 的视觉设计分析，
> 包含完整设计令牌、样式迁移代码和可直接使用的 Claude Code `/goal` 提示词。

---

## 一、目标网站设计特征总览（从截图+DOM 分析）

### 1.1 整体布局
```
┌──────────────┬──────────────────────────────────┐
│              │    标题：免费八字排盘在线计算器      │
│   左侧导航栏  │    副标题说明文字                    │
│   (~200px)   │  ┌────────────────────────────┐   │
│              │  │ Tab: 出生时间 | AI解析 | 四柱反查│   │
│  ☯ 观象八字  │  │                              │   │
│              │  │  性别: [乾造(男)] [坤造(女)]    │   │
│  □ 八字算命  │  │  名称: [输入框]                │   │
│  ♡ 情侣配对  │  │  地区: [下拉选择]               │   │
│  ⚖ 称骨算命  │  │                              │   │
│  🔮 SBTI     │  │  日期时间: 阳历|农历            │   │
│              │  │  [2026]年 [01]月 [01]日        │   │
│              │  │  [12]时 [00]分  [时辰选择]      │   │
│              │  │                              │   │
│              │  │  2026/01/01 12:00             │   │
│              │  │  农历乙巳年十一月十三壬午时      │   │
│              │  │                              │   │
│              │  │  [✨ 生成八字排盘及解说]         │   │
│              │  └────────────────────────────┘   │
└──────────────┴──────────────────────────────────┘
```

### 1.2 视觉风格关键词
- **极深黑底**：接近纯黑的背景色（#0d0d0f ~ #111113）
- **金色/琥珀强调**：导航高亮、Logo 用金色调
- **橙色主 CTA 按钮**：醒目的橙→金渐变按钮（#e8853c → #d4710a）
- **米白色选中态**：性别/选项选中 = 浅米白背景 + 深色文字
- **卡片容器**：微妙的深灰背景 + 细边框 + 圆角
- **滚动式日期选择器**：分段滚轮式年/月/日/时/分选择
- **左侧固定侧边栏**：暗色背景 + 图标+文字导航项

---

## 二、设计令牌对照表（精确提取值）

### 2.1 色彩系统

| 令牌名称 | ba-zi.ai 参考值 | 你当前的值 | 建议 |
|---------|-----------------|-----------|------|
| **页面背景** | `#0d0d0f` 或 `#111113` | `#0a0a12` | → `#0e0e10` |
| **侧边栏背景** | `#141416` | `#12121e` | → `#131315` |
| **卡片/表单背景** | `#18181b` 或 `#1a1a1d` | `#16162a` | → `#18181b` |
| **悬浮层背景** | `#1f1f23` | `#1c1c30` | → `#1e1e21` |
| **主文字颜色** | `#e8e6e3` (暖白) | `#edece8` | 保持 |
| **次要文字** | `#9ca3af` (中性灰) | `#a8a4a0` | → `#9ca3af` |
| **弱化文字** | `#6b7280` | `#5a5a6e` | → `#6b7280` |
| **主强调色(金)** | `#c9a227` 或 `#d4a520` | `#c9a96e` | → `#d4a520` |
| **CTA 主按钮** | `linear-gradient(135deg, #e8853c, #d4710a)` | 纯色 `#c9a96e` | → 渐变橙 |
| **CTA hover** | `linear-gradient(135deg, #f0954b, #e08015)` | `#dbb978` | → 更亮橙 |
| **边框色** | `rgba(255,255,255,0.06)` | `#24243a` | → `rgba(255,255,255,0.07)` |
| **选中态背景** | `#faf8f0` (米白) | `var(--accent)` | → `#f5f0e6` |
| **选中态文字** | `#1a1a1a` (近黑) | `var(--bg-primary)` | → `#1a1a1a` |
| **未选中态背景** | `transparent` | transparent | 保持 |
| **未选中态文字** | `#9ca3af` | var(--text-secondary) | → `#9ca3af` |
| **Tab 激活背景** | `rgba(255,255,255,0.04)` | — | 新增 |
| **Tab 未激活文字** | `#6b7280` | — | 新增 |
| **阳历 toggle 背景** | `#d4a520` (金色) | — | 新增 |
| **日期数字颜色** | `#e8e6e3` | — | 新增 |
| **日期数字字号** | `24px` bold | — | 新增 |
| **日期段背景** | `rgba(255,255,255,0.03)` | — | 新增 |

### 2.2 间距与圆角

| 属性 | ba-zi.ai 参考值 | 说明 |
|------|-----------------|------|
| **卡片圆角** | `12px ~ 16px` | 中等圆润 |
| **按钮圆角** | `8px ~ 10px` | 轻微圆角 |
| **输入框圆角** | `8px` | 统一 |
| **Tab 圆角** | `8px` | 上方两角 |
| **卡片内边距** | `24px ~ 32px` | 宽松舒适 |
| **表单项间距** | `20px ~ 24px` | 清晰分组 |
| **侧边栏宽度** | `200px ~ 220px` | 固定 |
| **导航项 padding** | `10px 16px` | 可点击区域 |

### 2.3 字体系统

| 元素 | 字体族 | 字重 | 字号 |
|------|--------|------|------|
| **H1 标题** | system-ui / sans-serif | 600 (semibold) | 24px ~ 28px |
| **正文** | system-ui / sans-serif | 400 | 14px ~ 15px |
| **标签文字** | system-ui / sans-serif | 500 | 13px ~ 14px |
| **辅助说明** | system-ui / sans-serif | 400 | 12px |
| **按钮文字** | system-ui / sans-serif | 500 medium | 14px ~ 15px |
| **导航文字** | system-ui / sans-serif | 400 | 14px |
| **日期大数字** | system-ui / monospace | 700 bold | 24px |

> ⚠️ **关键差异**：ba-zi.ai 使用 **无衬线字体 (system-ui/sans-serif)**，
> 而你当前使用 **Noto Serif SC 衬线字体**。这是最大的视觉差异来源。

### 2.4 阴影与光效

| 元素 | 阴影值 |
|------|--------|
| 卡片阴影 | `0 4px 24px rgba(0,0,0,0.3)` |
| 按钮阴影 | `0 2px 8px rgba(212,160,32,0.25)` |
| 下拉菜单阴影 | `0 8px 24px rgba(0,0,0,0.4)` |
| 侧边栏分隔线 | `1px solid rgba(255,255,255,0.05)` |

---

## 三、更新后的 globals.css（直接替换版）

```css
@import "tailwindcss";

:root {
  /* === 背景层次（对齐 ba-zi.ai 的纯黑系） === */
  --bg-primary: #0e0e10;
  --bg-secondary: #141417;
  --bg-card: #18181b;
  --bg-hover: #1e1e21;
  --bg-elevated: #222225;
  
  /* === 文字层级 === */
  --text-primary: #e8e6e3;
  --text-secondary: #9ca3af;
  --text-muted: #6b7280;
  
  /* === 强调色系 === */
  --accent: #d4a520;           /* 金色（导航/高亮） */
  --accent-hover: #e5b82e;
  --accent-dim: rgba(212,165,32,0.10);
  --accent-glow: rgba(212,165,32,0.06);
  
  /* === CTA 按钮色（橙→金渐变） === */
  --cta-bg: linear-gradient(135deg, #e8853c 0%, #d4710a 100%);
  --cta-hover: linear-gradient(135deg, #f0954b 0%, #e08015 100%);
  --cta-text: #ffffff;
  
  /* === 选中态 === */
  --selected-bg: #f5f0e6;
  --selected-text: #1a1a1a;
  
  /* === 边框与分割 === */
  --border: rgba(255,255,255,0.07);
  --border-subtle: rgba(255,255,255,0.04);
  
  /* === 阴影 === */
  --shadow: 0 4px 24px rgba(0,0,0,0.3);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
  --shadow-lg: 0 16px 48px rgba(0,0,0,0.45);
  --shadow-accent: 0 2px 8px rgba(212,165,32,0.2);
  
  /* === 圆角 === */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;
  
  /* === 功能色 === */
  --success: #22c55e;
  --danger: #ef4444;
  --warning: #eab308;
  
  /* === 五行色（保持不变） === */
  --wood: #22c55e;
  --fire: #ef4444;
  --earth: #eab308;
  --metal: #f59e0b;
  --water: #3b82f6;
}

[data-theme="light"] {
  --bg-primary: #fafaf8;
  --bg-secondary: #f2f0ec;
  --bg-card: #ffffff;
  --bg-hover: #f5f3ee;
  --bg-elevated: #fcfcfa;
  --text-primary: #1a1a1a;
  --text-secondary: #5a5a5a;
  --text-muted: #8a8a8a;
  --accent: #b8920f;
  --accent-hover: #cba30f;
  --accent-dim: rgba(184,146,15,0.08);
  --accent-glow: rgba(184,146,15,0.04);
  --cta-bg: linear-gradient(135deg, #e07010 0%, #c56000 100%);
  --cta-hover: linear-gradient(135deg, #f08020 0%, #d57010 100%);
  --selected-bg: #ede8dc;
  --selected-text: #1a1a1a;
  --border: #e5e2da;
  --border-subtle: #eceae4;
  --shadow: 0 4px 24px rgba(0,0,0,0.06);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
  --shadow-lg: 0 16px 48px rgba(0,0,0,0.08);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC",
               "PingFang SC", "Microsoft YaHei", sans-serif;  /* ← 改为无衬线 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.6;
  font-size: 15px;
  letter-spacing: 0.01em;
}

/* === 滚动条（细窄风格） === */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }

/* === 动画 === */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(212,165,32,0.35); }
  50% { box-shadow: 0 0 12px 2px rgba(212,165,32,0.18); }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slideUp 0.4s ease-out forwards; }
@keyframes dash-flow { to: stroke-dashoffset: -18; }
.animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }
.animate-shimmer {
  background: linear-gradient(90deg, var(--bg-hover) 25%, var(--border) 50%, var(--bg-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.animate-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }

::selection {
  background: color-mix(in srgb, var(--accent) 30%, transparent);
  color: var(--text-primary);
}

/* === 表单控件焦点 === */
textarea:focus,
input:focus,
select:focus {
  outline: none;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-dim);
}

a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

table { width: 100%; border-collapse: collapse; }
th, td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
th { font-weight: 600; color: var(--text-secondary); font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }
tbody tr:hover { background: var(--bg-hover); }

pre, code { font-family: "JetBrains Mono", "Fira Code", monospace; }
pre {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  overflow-x: auto;
  font-size: 13.5px;
  line-height: 1.65;
}
code { background: var(--bg-secondary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: transparent; padding: 0; border-radius: 0; }

blockquote {
  margin: 16px 0;
  padding: 12px 20px;
  border-left: 3px solid var(--accent);
  background: var(--accent-dim);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

input[type="date"], input[type="time"] { color-scheme: light dark; }

.__nextjs-edge-runtime-panel-bottom-left,
[data-nextjs-edge-runtime-panel] { display: none !important; }

@media print {
  * { transition: none !important; background: white !important; color: #1a1a1e !important;
    border-color: #ddd !important; box-shadow: none !important; text-shadow: none !important; }
}
```

---

## 四、关键组件改造要点

### 4.1 BirthForm 改造重点

**当前问题 vs 目标效果：**

| 项目 | 当前状态 | ba-zi.ai 参考 | 改造方向 |
|------|---------|--------------|---------|
| 性别选择 | 金色背景填充 | 米白色背景+深色字 | `--selected-bg` + `--selected-text` |
| 日期输入 | 原生 `<input date>` | 分段滚轮选择器 | 自定义 DatePicker 组件 |
| 时间输入 | 原生 `<input time>` | 时/分独立段 | 同上 |
| 提交按钮 | 金色纯色 | 橙→金渐变 | `background: var(--cta-bg)` |
| 表单布局 | 无 Tab 切换 | 三个 Tab（出生时间/AI解析/四柱反查） | 增加 TabBar 组件 |
| 名称字段 | 无 | 有"给TA起个名字"输入框 | 可选增加 |
| 地区选择 | 无 | 有地区下拉框 | 可选增加 |
| 农历显示 | 无 | 显示农历干支 | 排盘后展示 |

### 4.2 页面布局改造

**当前**：居中单列卡片 + 左侧 HistorySidebar
**目标**：左右分栏（固定侧边栏 + 右侧内容区），类似 ba-zi.ai

```tsx
// page.tsx 新布局结构建议：
<div className="flex min-h-screen">
  {/* 左侧固定导航栏 */}
  <aside className="w-[210px] fixed left-0 top-0 bottom-0 bg-[var(--bg-secondary)] 
                  border-r border-[var(--border-subtle)] flex flex-col">
    {/* Logo */}
    <div className="p-4 flex items-center gap-2">
      <span className="text-[var(--accent)]">☯</span>
      <span className="font-semibold text-[var(--text-primary)]">bazi-pro</span>
    </div>
    
    {/* 导航项 */}
    <nav className="flex-1 px-2 py-4 space-y-1">
      {navItems.map(item => (
        <a key={item.name} href={item.href}
           className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors
                      ${active ? 'bg-[var(--accent-dim)] text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}`}>
          <span>{item.icon}</span>
          <span>{item.name}</span>
        </a>
      ))}
    </nav>
  </aside>
  
  {/* 右侧主内容区 */}
  <main className="ml-[210px] flex-1 p-8 overflow-y-auto">
    {/* 内容区 */}
  </main>
</div>
```

### 4.3 BaziChartCard 改造重点

| 项目 | 当前 | 目标 |
|------|------|------|
| 四柱排版 | 网格 4 列 | 保持但优化间距 |
| 天干地支字体 | 默认 | 加粗加大，等宽感 |
| 五行色块 | 小圆点 | 保持但更明显 |
| 十神标注 | 文字 | 保持 |
| 刑冲合害连线 | SVG | 保持（已有实现） |
| 整体卡片风格 | 半透明毛玻璃 | 实色深灰背景 |

---

## 五、Claude Code `/goal` 提示词（直接复制使用）

```
/goal

## 目标
将 frontend/src 下所有组件的视觉设计全面对齐 https://www.ba-zi.ai/calculator （观象八字）的 UI 风格。
该网站的核心特征是：极深黑背景 + 无衬线字体 + 金/琥珀强调色 + 橙色渐变 CTA 按钮 + 左右分栏布局 + 米白色选中态。

## 设计参考网站核心特征（必须严格遵循）

### 配色（精确值）
- 页面背景: #0e0e10（极深黑，非蓝紫调）
- 卡片背景: #18181b（暖灰色）
- 侧边栏: #141417
- 主文字: #e8e6e3（暖白）
- 次要文字: #9ca3af（中性灰）
- 弱化文字: #6b7280
- 金色强调: #d4a520（用于 Logo、导航高亮、图标）
- CTA 按钮: linear-gradient(135deg, #e8853c, #d4710a) 橙→金渐变
- CTA hover: linear-gradient(135deg, #f0954b, #e08015)
- 边框: rgba(255,255,255,0.07)
- 选中态(如性别): 背景 #f5f0e6 米白 + 文字 #1a1a1a 近黑
- 未选中态: 透明背景 + 文字 #9ca3af

### 字体
- 全局改为无衬线: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif
- 不再使用 Noto Serif SC 衬线体（除特殊装饰性标题外）
- 字号基准: 正文 15px, 标签 13px, 辅助 12px, H1 26px

### 布局
- 首页改为左右分栏: 左侧 210px 固定导航栏 + 右侧自适应内容区
- 导航栏包含: Logo(☯ bazi-pro) + 导航项(八字排盘/流派对比/历史记录/设置)
- 表单区域放在右侧居中卡片中
- 卡片最大宽度约 600px

### 组件细节
1. **BirthForm 表单**:
   - 性别选择: 选中=米白背景(#f5f0e6)+深色字(#1a1a1a), 未选中=透明+灰色字
   - 日期/时间: 如果保持原生 input 则美化样式；如果资源允许则改用分段滚轮式
   - 提交按钮: 橙→金渐变背景, 白色文字, 圆角 10px, 全宽, py-3.5
   - 增加 Tab 切换条在表单顶部（可选: "基本信息 / 高级选项"）
   
2. **BaziChartCard 排盘卡**:
   - 四柱天干地支: 字号加大(20px+), font-weight 700
   - 干支显示用等宽/半等宽字体
   - 五行色标清晰可见
   - 卡片背景实色(非透明), 边框 subtle
   
3. **全局**:
   - 所有圆角统一: sm:6px, md:10px, lg:14px, xl:18px
   - 阴影统一: --shadow, --shadow-sm, --shadow-lg
   - 过渡动画统一: transition-all duration-200
   - hover 态统一: bg 变深或亮度微增

## 技术约束
- Next.js 16 App Router + React 19 + TypeScript
- Tailwind CSS v4（用 @theme 定义自定义值）
- Zustand 状态管理
- pnpm 包管理
- 所有 UI 文本中文

## 绝对不能改 ✗
- server/ 目录任何文件
- bazi_pro/core/ 任何计算逻辑
- API 数据结构和 DashboardVM 契约
- 路由路径结构
- 组件 props 接口定义（可以新增可选 prop）
- 业务逻辑和事件处理函数

## 执行顺序
1. 第一步: 替换 globals.css 的 :root 设计令牌（配色/字体/间距/圆角/阴影）
2. 第二步: 改造 page.tsx 首页布局（左右分栏 + 侧边栏）
3. 第三步: 改造 BirthForm.tsx（性别选择/按钮/输入框样式）
4. 第四步: 改造 BaziChartCard.tsx（排版/字号/色标）
5. 第五步: 改造其余组件（ChatPanel/DayunTimeline/SchoolComparePanel 等）
6. 第六步: 微调全局一致性（滚动条/selection/focus 状态）

## 验证标准（每步必须通过）
- cd frontend && pnpm build 零错误
- cd frontend && pnpm lint 通过
- TypeScript 类型检查通过
- 暗色主题正常（不出现不可读的文字）
- 移动端响应式不破坏（可降级为单列）

## 迭代规则
- 每次聚焦 1 个文件或 1 个组件
- 每次修改后运行 build 验证
- 失败立即回滚，换方案重试
- commit 信息格式: `style: 组件名 - 简短描述`
- 优先 Tailwind 工具类，少写内联 style
- 保持代码整洁，删除无用样式
```

---

## 六、快速对比清单（验收用）

完成迁移后，逐项检查：

- [ ] 背景是否从蓝紫调(#0a0a12)变为纯黑调(#0e0e10)
- [ ] 字体是否从衬线(Noto Serif SC)变为无衬线(system-ui/Noto Sans SC)
- [ ] 强调色是否从淡金(#c9a96e)变为亮金(#d4a520)
- [ ] CTA 按钮是否变为橙→金渐变
- [ ] 性别/选项选中态是否为米白背景+深色文字
- [ ] 是否有左侧固定导航栏（~210px 宽）
- [ ] 表单卡片是否使用 #18181b 背景
- [ ] 边框是否使用 rgba(255,255,255,0.07) 低透明度
- [ ] 圆角是否统一（6/10/14/18 四档）
- [ ] pnpm build 是否零错误通过

---

## 七、注意事项

### 7.1 版权与合规
- **只借鉴视觉设计和配色方案**，不复制任何代码
- **不抄袭**其文案内容、图片素材或商标
- 设计风格本身不受版权保护，但具体代码和素材受保护

### 7.2 差异化建议
在参考 ba-zi.ai 的基础上，保留你项目的独特优势：
- 你的**确定性计算引擎 + 古籍引证**是其没有的卖点
- **三流派对比**功能是你的差异化特性
- 可以在视觉对齐的基础上，加入你自己的品牌元素（如古籍纹理装饰、印章风格的 logo 等）

### 7.3 渐进式迁移策略
如果一次性改动太大风险高，可以按以下顺序分批迭代：

```
第一批（低风险，仅 CSS 变量）:
  └─ globals.css 设计令牌替换
  
第二批（中等风险，布局调整）:
  ├─ page.tsx 布局重构
  └─ HistorySidebar → 固定导航栏改造
  
第三批（较高风险，组件样式）:
  ├─ BirthForm 样式重做
  ├─ BaziChartCard 样式优化
  └─ 其余组件逐一适配
```

---

*文档生成时间: 2026-05-29*
*参考版本: ba-zi.ai/calculator (观象八字)*
*适用项目: bazi-pro v5.2 frontend/*
