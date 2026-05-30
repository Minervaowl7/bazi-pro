# bazi-pro Frontend Redesign — Design Specification

> Date: 2026-05-30
> Status: Approved
> Target: Full frontend visual system rewrite + page redesign

---

## 1. Design Philosophy

**Positioning: 古籍感 + Apple 风**

Not a 玄学网站 (superstition site), not an 互联网后台 (generic dashboard). A professional bazi analysis tool that feels like reading classical Chinese texts on a modern, Apple-quality interface.

**Reference products:**
- Deep Oracle (deeporacle.ai) — clean SaaS product feel, tab-based report navigation
- Apple Health — bento grid, clean data presentation
- Kindle 古籍阅读器 — paper texture, reading comfort
- 《子平真诠》《滴天髓》— classical text aesthetics

**Keywords:** 克制 · 留白 · 纸张感 · 朱砂印 · 金墨批注 · 现代专业

---

## 2. Design Tokens

### 2.1 Color System — Light Mode (Primary)

```css
:root {
  --bg-primary: #FAF9F6;
  --bg-card: #FFFFFF;
  --bg-hover: #F7F6F2;
  --bg-elevated: #F0EFEB;
  --bg-input: #FFFFFF;

  --border: #EEEAE2;
  --border-subtle: #F2F0EA;

  --text-primary: #1A1A1A;
  --text-secondary: #555555;
  --text-muted: #999999;

  --accent: #8A3B2A;
  --accent-hover: #A04832;
  --accent-dim: rgba(138, 59, 42, 0.08);
  --accent-glow: rgba(138, 59, 42, 0.04);

  --gold: #C19A42;
  --gold-dim: rgba(193, 154, 66, 0.08);
  --gold-text: #9F7A2E;

  --success: #3B8D62;
  --success-dim: rgba(59, 141, 98, 0.08);
  --danger: #C53030;
  --danger-dim: rgba(197, 48, 48, 0.08);
  --warning: #C19A42;
  --warning-dim: rgba(193, 154, 66, 0.08);

  --wood: #4A9E6E;
  --fire: #D44030;
  --earth: #8B5E3C;
  --metal: #C19A42;
  --water: #3F6F9F;

  --wood-dim: rgba(74, 158, 110, 0.08);
  --fire-dim: rgba(212, 64, 48, 0.08);
  --earth-dim: rgba(139, 94, 60, 0.08);
  --metal-dim: rgba(193, 154, 66, 0.08);
  --water-dim: rgba(63, 111, 159, 0.08);

  --shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.08);

  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 16px;
  --radius-xl: 20px;
}
```

### 2.2 Color System — Dark Mode (Optional Toggle)

```css
[data-theme="dark"] {
  --bg-primary: #1A1816;
  --bg-card: #242018;
  --bg-hover: #2E2A22;
  --bg-elevated: #342E24;
  --bg-input: #2A241C;

  --border: #3A3428;
  --border-subtle: #302A20;

  --text-primary: #E8DCC8;
  --text-secondary: #C4B89A;
  --text-muted: #8A7A60;

  --accent: #D8845A;
  --accent-hover: #E0946A;
  --accent-dim: rgba(216, 132, 90, 0.10);
  --accent-glow: rgba(216, 132, 90, 0.06);

  --gold: #D4B45A;
  --gold-dim: rgba(212, 180, 90, 0.10);
  --gold-text: #C4A44A;

  --success: #6AAC7A;
  --success-dim: rgba(106, 172, 122, 0.10);
  --danger: #E06060;
  --danger-dim: rgba(224, 96, 96, 0.10);
  --warning: #D4B45A;
  --warning-dim: rgba(212, 180, 90, 0.10);

  --wood: #7AAD8A;
  --fire: #E87858;
  --earth: #C89A6A;
  --metal: #D4B45A;
  --water: #6A90A8;

  --wood-dim: rgba(122, 173, 138, 0.12);
  --fire-dim: rgba(232, 120, 88, 0.12);
  --earth-dim: rgba(200, 154, 106, 0.12);
  --metal-dim: rgba(212, 180, 90, 0.12);
  --water-dim: rgba(106, 144, 168, 0.12);

  --shadow: 0 1px 4px rgba(0, 0, 0, 0.20);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.30);
}
```

### 2.3 Typography Scale

| Level | Size | Weight | Letter-spacing | Usage |
|-------|------|--------|---------------|-------|
| Hero | 28px | 700 | -0.01em | Core verdict (日主+格局+旺衰) |
| H2 | 22px | 600 | 0 | Section titles |
| H3 | 16px | 600 | 0 | Card titles |
| Body | 15px | 400 | 0.02em | Main text |
| Meta | 12px | 400 | 0.02em | Secondary info |
| Micro | 10px | 500 | 0.04em | Tags, badges |

Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif`

### 2.4 Paper Texture

Body background gets a subtle noise overlay:

```css
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.015;
  background-image: url("data:image/svg+xml,..."); /* fine grain noise SVG */
  z-index: 0;
}
```

- Opacity: 1-2%, barely visible but perceptible
- Only on body, not on cards
- Creates paper feel without being obvious

---

## 3. Chinese Semantic Components

### 3.1 Tiangan (天干) Tag

For: 甲 乙 丙 丁 戊 己 庚 辛 壬 癸

```css
.tag-tiangan {
  background: rgba(138, 59, 42, 0.08);
  border: 1px solid rgba(138, 59, 42, 0.15);
  color: #8A3B2A;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
}
```

Visual feel: 朱砂印泥 (vermilion seal ink)

### 3.2 Dizhi (地支) Tag

For: 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥

```css
.tag-dizhi {
  background: rgba(63, 111, 159, 0.08);
  border: 1px solid rgba(63, 111, 159, 0.15);
  color: #3F6F9F;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
}
```

Visual feel: 藏蓝墨 (indigo ink)

### 3.3 Shishen (十神) Tag

For: 比肩 劫财 食神 伤官 偏财 正财 七杀 正官 偏印 正印

```css
.tag-shishen {
  background: rgba(193, 154, 66, 0.08);
  border: 1px solid rgba(193, 154, 66, 0.15);
  color: #9F7A2E;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
}
```

Visual feel: 金墨批注 (gold ink annotation). Text uses darker #9F7A2E for readability; --metal stays #C19A42 for decorative use.

### 3.4 Wuxing (五行) Tag

For: 木 火 土 金 水

```css
.tag-wood  { background: var(--wood-dim);  color: var(--wood);  border: 1px solid rgba(74,158,110,0.15); }
.tag-fire  { background: var(--fire-dim);  color: var(--fire);  border: 1px solid rgba(212,64,48,0.15); }
.tag-earth { background: var(--earth-dim); color: var(--earth); border: 1px solid rgba(139,94,60,0.15); }
.tag-metal { background: var(--metal-dim); color: var(--metal); border: 1px solid rgba(193,154,66,0.15); }
.tag-water { background: var(--water-dim); color: var(--water); border: 1px solid rgba(63,111,159,0.15); }
```

### 3.5 Verdict Block (裁决区)

For: 用神裁决, 格局判定, 旺衰结论

```css
.verdict-block {
  border-left: 3px solid var(--accent);
  background: var(--accent-dim);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  padding: 16px 20px;
}
```

Visual feel: 古籍批注 (classical text annotation with red margin line)

### 3.6 Chapter Naming Convention

**Report/Analysis pages** use 卷式 naming:
- 卷一 · 命局总论
- 卷二 · 旺衰裁决
- 卷三 · 格局与用神
- 卷四 · 大运流年
- 卷五 · 古籍引证

**Navigation tabs** use plain naming (lower barrier for new users):
- 排盘
- 命局总论
- 旺衰分析
- 格局用神
- 大运流年
- 古籍参考

---

## 4. Page Layouts

### 4.1 Homepage (排盘输入页)

**Style: 沉浸留白 (Immersive whitespace)**

- Centered input card on large whitespace
- Subtle paper texture background
- Minimal brand elements: 朱砂 tag "确定性计算引擎", title "八字排盘", subtitle
- No sidebar on homepage
- After paipan: result card appears below with animation
- Footer: 3 feature tags (古籍引证 / 零幻觉 / 三大流派)

### 4.2 Analysis Result Page (分析结果页)

**Style: Bento Grid + Tab Navigation**

Top section:
- Back link + school selector dropdown + theme toggle + export button
- Hero verdict bar: "丁火日主 · 七杀佩印格 · 偏旺 · 取木水 · 置信度 82%"
- Four-pillar mini chart (horizontal, day pillar highlighted with accent border)

Tab navigation (plain naming):
- 命盘总览 | 五行能量 | 大运流年 | 古籍引证 | 深度解读

Content area (Bento grid):
- Left 2/3: main content cards
- Right 1/3: summary metrics (旺衰/格局/用神/喜忌), dayun timeline, gongwei, shensha

Cards: white background, 1px solid #EEEAE2 border, 14px radius, minimal shadow

### 4.3 Report Page (报告页)

**Style: 卷轴阅读 (Scroll reading)**

- Full-width reading layout
- 卷式 chapter headers
- Verdict blocks for key conclusions
- Evidence cards with claim/confidence/basis structure
- Print-friendly: clean typography, no interactive elements

---

## 5. Component Specifications

### 5.1 Card

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow);
}
```

No border on default cards — use background level distinction. Only active/important cards get accent border.

### 5.2 Button

Primary (朱砂):
```css
background: var(--accent); color: #FFFFFF; border-radius: var(--radius-md);
```

Secondary:
```css
background: transparent; border: 1px solid var(--border); color: var(--text-secondary);
```

### 5.3 Input

```css
background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md);
focus: border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-dim);
```

### 5.4 Pillar Display (四柱)

- 4-column grid, each pillar centered
- Tiangan: large font, colored by wuxing
- Dizhi: large font, colored by wuxing
- Day pillar: accent background glow + "日主" badge
- Canggan: small tiangan tags below
- Separator: thin dashed line between gan and zhi

---

## 6. Key Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Color direction | 宣纸朱砂 (warm white + vermilion) | Modern minimal + Eastern accent, not yellow background |
| Layout | Bento Grid | Apple Health feel, modular, information hierarchy |
| Homepage | Immersive whitespace | First impression: calm, professional, not cluttered |
| Wuxing colors | Custom set with distinct earth/metal | Intuitive: brown=earth, gold=metal, not ambiguous |
| Wuxing vs semantic colors | Decoupled | Wood≠success, Fire≠danger to avoid confusion |
| Gold saturation | #C19A42 (lowered) | 古籍金墨 feel, not flashy |
| Card style | White + warm border + minimal shadow | Clean, paper-like, not heavy |
| Background | #FAF9F6 + paper texture | Paper feel without being yellow |
| Chapter naming | 卷式 for reports, plain for nav | Classical feel where appropriate, accessible elsewhere |
| Dark mode | Optional, warm-black base | Secondary priority, warm tones not cold gray |
| Tiangan/Dizhi/Shishen tags | Distinct visual languages | Users build visual memory: vermilion=天干, indigo=地支, gold=十神 |

---

## 7. Pages to Implement (Priority Order)

1. **Homepage** — 排盘输入页 (沉浸留白)
2. **Analysis Result Page** — 分析结果页 (Bento Grid + Tabs)
3. **Report Page** — 报告页 (卷轴阅读)
4. **History Sidebar** — 历史记录 (simplified, matches new tokens)
5. **Chat Panel** — AI 对话 (matches new tokens)

---

## 8. Acceptance Criteria

- Dashboard: 3 seconds to understand core verdict
- Report: feels like a professional consultation report, not markdown-to-HTML
- Screenshot: one screenshot looks premium, not like a debug page
- No placeholder text: no "未提取", "None", "null", "undefined", "NaN"
- Wuxing colors are immediately intuitive (brown=earth, gold=metal)
- Tiangan/Dizhi/Shishen are visually distinguishable at a glance
- Paper texture is perceptible but not distracting
- Dark mode maintains warm tones, not cold gray
