# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the bazi-pro frontend from dark cyberpunk to "古籍感 + Apple 风" — warm paper-white background, vermilion accent, decoupled wuxing/semantic colors, Chinese semantic components, Bento Grid analysis page, immersive homepage.

**Architecture:** Replace the existing CSS custom properties system in globals.css with the new design tokens. Update all components to use the new token names and Chinese semantic tag classes. Restructure the analysis page to Bento Grid + Tab navigation. Redesign homepage to immersive whitespace. Default theme changes from dark to light.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS 4, Zustand, ECharts

**Spec:** `docs/superpowers/specs/2026-05-30-frontend-redesign-design.md`

---

## File Structure

### Modify
- `frontend/src/app/globals.css` — Complete rewrite of design tokens, add Chinese semantic classes, paper texture
- `frontend/src/app/page.tsx` — Homepage redesign (immersive whitespace)
- `frontend/src/app/layout.tsx` — Default theme light, font stack update
- `frontend/src/app/analyze/[id]/page.tsx` — Bento Grid + Tab navigation
- `frontend/src/app/report/[id]/page.tsx` — 卷式 chapter naming, verdict blocks
- `frontend/src/components/ThemeProvider.tsx` — Default to light, warm-black dark mode
- `frontend/src/components/BirthForm.tsx` — New tokens, new card style
- `frontend/src/components/BaziChartCard.tsx` — Chinese semantic tags, new tokens
- `frontend/src/components/HistorySidebar.tsx` — New tokens
- `frontend/src/components/StrengthSlider.tsx` — New tokens
- `frontend/src/components/ShishenEnergyChart.tsx` — New tokens, shishen tag class
- `frontend/src/components/DayunTimeline.tsx` — New tokens, tiangan/dizhi tag classes
- `frontend/src/components/ChatPanel.tsx` — New tokens
- `frontend/src/components/GongweiPanel.tsx` — New tokens
- `frontend/src/components/ShenShaPanel.tsx` — New tokens
- `frontend/src/components/ExportPanel.tsx` — New tokens
- `frontend/src/components/RelationGraph.tsx` — New tokens
- `frontend/src/components/SchoolPanel.tsx` — New tokens
- `frontend/src/components/SchoolComparePanel.tsx` — New tokens
- `frontend/src/components/LifeKlineChart.tsx` — New tokens
- `frontend/src/components/AnalysisProgress.tsx` — New tokens
- `frontend/src/lib/constants.ts` — Update WUXING_BG, WUXING_GLOW, RELATION_COLORS to new values

### Create
- `frontend/src/components/ui/ChineseTag.tsx` — Reusable tiangan/dizhi/shishen/wuxing tag components
- `frontend/src/components/ui/VerdictBlock.tsx` — Reusable verdict block component
- `frontend/src/components/ui/ChapterHeader.tsx` — 卷式 chapter header component

---

## Task 1: Design Tokens Foundation

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/lib/constants.ts`

- [ ] **Step 1: Replace globals.css design tokens**

Replace the entire `:root` and `[data-theme="light"]` blocks with the new token system. Key changes:
- `--bg-primary: #FAF9F6` (was `#0a0a0f`)
- `--bg-card: #FFFFFF` (was `#16162e`)
- `--bg-hover: #F7F6F2`
- `--border: #EEEAE2`
- `--accent: #8A3B2A` (was `#d4a574`)
- `--wood: #4A9E6E`, `--fire: #D44030`, `--earth: #8B5E3C`, `--metal: #C19A42`, `--water: #3F6F9F`
- `--success: #3B8D62`, `--danger: #C53030`, `--warning: #C19A42`
- `--gold: #C19A42`, `--gold-dim: rgba(193,154,66,0.08)`, `--gold-text: #9F7A2E`
- Add `--wood-dim`, `--fire-dim`, `--earth-dim`, `--metal-dim`, `--water-dim`
- Dark mode: warm-black `#1A1816` base, `#242018` cards, `#E8DCC8` text
- Add Chinese semantic tag CSS classes: `.tag-tiangan`, `.tag-dizhi`, `.tag-shishen`, `.tag-wood`, `.tag-fire`, `.tag-earth`, `.tag-metal`, `.tag-water`
- Add `.verdict-block` class (left border + dim background)
- Add `.chapter-header` class (卷式 naming)
- Add paper texture `body::before` with SVG noise at 1.5% opacity
- Update animations to match new accent color
- Update print styles for light background

- [ ] **Step 2: Update constants.ts**

Update `WUXING_BG` to use new dim values:
```ts
export const WUXING_BG: Record<string, string> = {
  木: "var(--wood-dim)",
  火: "var(--fire-dim)",
  土: "var(--earth-dim)",
  金: "var(--metal-dim)",
  水: "var(--water-dim)",
};
```

Update `WUXING_GLOW` to use new values:
```ts
export const WUXING_GLOW: Record<string, string> = {
  木: "rgba(74,158,110,0.25)",
  火: "rgba(212,64,48,0.25)",
  土: "rgba(139,94,60,0.25)",
  金: "rgba(193,154,66,0.25)",
  水: "rgba(63,111,159,0.25)",
};
```

Update `RELATION_COLORS`:
```ts
export const RELATION_COLORS: Record<string, string> = {
  合: "#C19A42",
  冲: "#C53030",
  刑: "#8A5C9E",
  害: "#999999",
  合化: "#C19A42",
  化: "#C19A42",
};
```

- [ ] **Step 3: Run build to verify no breakage**

Run: `cd /workspace/frontend && pnpm build`
Expected: Build succeeds (visual will look wrong but no errors)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/globals.css frontend/src/lib/constants.ts
git commit -m "feat: replace design tokens with 古籍感+Apple风 system"
```

---

## Task 2: Chinese Semantic UI Components

**Files:**
- Create: `frontend/src/components/ui/ChineseTag.tsx`
- Create: `frontend/src/components/ui/VerdictBlock.tsx`
- Create: `frontend/src/components/ui/ChapterHeader.tsx`

- [ ] **Step 1: Create ChineseTag.tsx**

```tsx
type TagType = "tiangan" | "dizhi" | "shishen" | "wood" | "fire" | "earth" | "metal" | "water";

const TAG_CLASS: Record<TagType, string> = {
  tiangan: "tag-tiangan",
  dizhi: "tag-dizhi",
  shishen: "tag-shishen",
  wood: "tag-wood",
  fire: "tag-fire",
  earth: "tag-earth",
  metal: "tag-metal",
  water: "tag-water",
};

interface ChineseTagProps {
  type: TagType;
  children: React.ReactNode;
  className?: string;
}

export function ChineseTag({ type, children, className = "" }: ChineseTagProps) {
  return (
    <span className={`${TAG_CLASS[type]} ${className}`.trim()}>
      {children}
    </span>
  );
}
```

- [ ] **Step 2: Create VerdictBlock.tsx**

```tsx
interface VerdictBlockProps {
  children: React.ReactNode;
  className?: string;
}

export function VerdictBlock({ children, className = "" }: VerdictBlockProps) {
  return (
    <div className={`verdict-block ${className}`.trim()}>
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Create ChapterHeader.tsx**

```tsx
interface ChapterHeaderProps {
  volume: number;
  title: string;
  className?: string;
}

export function ChapterHeader({ volume, title, className = "" }: ChapterHeaderProps) {
  return (
    <div className={`chapter-header ${className}`.trim()}>
      <span className="chapter-header-volume">卷{["一","二","三","四","五","六","七","八","九","十"][volume - 1] || volume}</span>
      <span className="chapter-header-dot"> · </span>
      <span className="chapter-header-title">{title}</span>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add Chinese semantic UI components (ChineseTag, VerdictBlock, ChapterHeader)"
```

---

## Task 3: ThemeProvider Default to Light

**Files:**
- Modify: `frontend/src/components/ThemeProvider.tsx`

- [ ] **Step 1: Change default theme from dark to light**

In ThemeProvider.tsx:
- Change `useState<Theme>("dark")` to `useState<Theme>("light")`
- Change initial fallback from `"dark"` to `"light"`
- Update title text: "切换到暗色模式" ↔ "切换到亮色模式"

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ThemeProvider.tsx
git commit -m "feat: default theme to light mode"
```

---

## Task 4: Homepage Redesign

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/BirthForm.tsx`

- [ ] **Step 1: Rewrite page.tsx to immersive whitespace**

Remove the dark background, "命" watermark, and HistorySidebar from homepage. Create a centered, clean layout:
- Full-screen centered card on #FAF9F6 background
- Minimal brand: "确定性计算引擎" tag in gold, "八字排盘" title, subtitle
- BirthForm inside a white card with warm border
- Footer: 3 feature tags in muted text
- ThemeToggle in top-right corner only
- No HistorySidebar on homepage

- [ ] **Step 2: Update BirthForm.tsx to new tokens**

Replace all inline `var()` references to match new token names:
- `var(--bg-secondary)` → `var(--bg-hover)` for input backgrounds
- `var(--accent)` stays but is now vermilion
- Button text color: `#FFFFFF` instead of `var(--bg-primary)`
- Pillar display: use ChineseTag for tiangan/dizhi
- School selector: use warm border style
- "深度解读" button: use `var(--accent)` gradient

- [ ] **Step 3: Run dev server and visually verify**

Run: `cd /workspace/frontend && pnpm dev`
Expected: Homepage shows warm white background, centered card, vermilion accent

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/page.tsx frontend/src/components/BirthForm.tsx
git commit -m "feat: redesign homepage to immersive whitespace style"
```

---

## Task 5: Analysis Page — Bento Grid + Tabs

**Files:**
- Modify: `frontend/src/app/analyze/[id]/page.tsx`

- [ ] **Step 1: Add Tab navigation state**

Add `activeTab` state with values: "overview" | "wuxing" | "dayun" | "classical" | "deep". Render tab bar below the hero section.

- [ ] **Step 2: Create Hero verdict bar**

Replace the current top area with a hero bar showing:
- "丁火日主 · 七杀佩印格 · 偏旺 · 取木水 · 置信度 82%"
- Four-pillar mini chart (horizontal, day pillar highlighted)
- Use VerdictBlock for key conclusions

- [ ] **Step 3: Restructure to Bento Grid**

Replace the current `lg:grid-cols-12` layout with a Bento grid:
- Hero bar spans full width
- Tab navigation below hero
- Content area: left 2/3 main content, right 1/3 summary metrics
- Summary metrics: 旺衰/格局/用神 as small cards with new tokens
- Remove HistorySidebar from this page (or make it a slide-out drawer)

- [ ] **Step 4: Update all inline styles to new tokens**

Replace:
- `var(--bg-secondary)` → `var(--bg-hover)` where appropriate
- `var(--bg-card)` stays
- `var(--border)` now uses warm `#EEEAE2`
- `var(--accent)` now vermilion
- Button colors: accent buttons use `color: #FFFFFF`
- School dropdown: warm border, light background

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/analyze/[id]/page.tsx
git commit -m "feat: redesign analysis page with Bento Grid and Tab navigation"
```

---

## Task 6: BaziChartCard — Chinese Semantic Tags

**Files:**
- Modify: `frontend/src/components/BaziChartCard.tsx`

- [ ] **Step 1: Replace inline tag styles with ChineseTag components**

- Tiangan characters (甲乙丙丁…) → `<ChineseTag type="tiangan">`
- Dizhi characters (子丑寅卯…) → `<ChineseTag type="dizhi">`
- Shishen labels (比肩/劫财/食神…) → `<ChineseTag type="shishen">`
- Wuxing labels (木火土金水) → `<ChineseTag type="wood|fire|earth|metal|water">`
- Day pillar highlight: use `var(--accent-dim)` background + `var(--accent)` border
- "日主" badge: use `var(--accent)` background with white text

- [ ] **Step 2: Update all color references to new tokens**

- `WUXING_BG` references now use CSS variables via `var()`
- Card background: `var(--bg-card)`, border: `var(--border)`
- Section headers: `var(--gold)` for labels, `var(--text-secondary)` for titles

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BaziChartCard.tsx
git commit -m "feat: apply Chinese semantic tags to BaziChartCard"
```

---

## Task 7: Remaining Components — Token Migration

**Files:**
- Modify: `frontend/src/components/StrengthSlider.tsx`
- Modify: `frontend/src/components/ShishenEnergyChart.tsx`
- Modify: `frontend/src/components/DayunTimeline.tsx`
- Modify: `frontend/src/components/HistorySidebar.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/components/GongweiPanel.tsx`
- Modify: `frontend/src/components/ShenShaPanel.tsx`
- Modify: `frontend/src/components/ExportPanel.tsx`
- Modify: `frontend/src/components/RelationGraph.tsx`
- Modify: `frontend/src/components/SchoolPanel.tsx`
- Modify: `frontend/src/components/SchoolComparePanel.tsx`
- Modify: `frontend/src/components/LifeKlineChart.tsx`
- Modify: `frontend/src/components/AnalysisProgress.tsx`

- [ ] **Step 1: Bulk token migration across all components**

For each component, replace:
- `var(--bg-secondary)` → `var(--bg-hover)` (for input/hover backgrounds)
- `var(--bg-elevated)` → `var(--bg-hover)` (where used as secondary surface)
- `var(--border-subtle)` → `var(--border-subtle)` (keep, but value changed in CSS)
- `var(--border-accent)` → `var(--accent)` with opacity (or use `var(--gold-dim)` border)
- `var(--day-master-bg)` → `var(--accent)` (朱砂)
- `var(--day-master-text)` → `#FFFFFF`
- `var(--shadow)` / `var(--shadow-sm)` / `var(--shadow-lg)` — keep, values changed in CSS
- Button text on accent background: `#FFFFFF` not `var(--bg-primary)`
- `WUXING_BG[wx]` → use CSS class or `var(--${wx}-dim)` pattern
- `WUXING_GLOW[wx]` → updated values from constants.ts

- [ ] **Step 2: Apply ChineseTag to DayunTimeline**

- Tiangan in dayun steps → `<ChineseTag type="tiangan">`
- Dizhi in dayun steps → `<ChineseTag type="dizhi">`
- Wuxing labels → `<ChineseTag type="wood|fire|earth|metal|water">`

- [ ] **Step 3: Apply ChineseTag to ShishenEnergyChart**

- Shishen labels → `<ChineseTag type="shishen">`

- [ ] **Step 4: Update HistorySidebar**

- Background: `var(--bg-hover)` instead of `var(--bg-secondary)`
- Border: `var(--border)` (now warm)
- Active item: `var(--accent-dim)` background
- Remove or simplify: make it a slide-out drawer instead of always-visible sidebar

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: migrate all components to new design tokens and Chinese semantic tags"
```

---

## Task 8: Report Page — 卷式 Naming + Verdict Blocks

**Files:**
- Modify: `frontend/src/app/report/[id]/page.tsx`

- [ ] **Step 1: Replace SECTION_META with 卷式 naming**

Change section titles:
- "命盘总论" → ChapterHeader volume=1 title="命局总论"
- "性格深度分析" → ChapterHeader volume=2 title="性情格局"
- "事业财运" → ChapterHeader volume=3 title="事业财运"
- "感情婚姻" → ChapterHeader volume=4 title="婚恋感情"
- "健康提醒" → ChapterHeader volume=5 title="健康提醒"
- "大运流年详批" → ChapterHeader volume=6 title="大运流年"
- "开运建议" → ChapterHeader volume=7 title="趋吉避凶"

- [ ] **Step 2: Wrap key conclusions in VerdictBlock**

For each SectionCard, detect the first paragraph or summary and wrap it in `<VerdictBlock>`.

- [ ] **Step 3: Update all token references**

Same token migration as other components. Button text on accent: `#FFFFFF`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/report/[id]/page.tsx
git commit -m "feat: redesign report page with 卷式 naming and verdict blocks"
```

---

## Task 9: Layout + Print Styles

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/globals.css` (print section)

- [ ] **Step 1: Update layout.tsx**

- Update metadata title/description if needed
- Ensure ThemeProvider wraps children (already done)
- Add `className="antialiased"` to body (already done)

- [ ] **Step 2: Update print styles in globals.css**

- Change print background to white
- Change print text to dark (#1A1A1A)
- Ensure Chinese semantic tags print with visible borders
- Verdict blocks print with left border
- Chapter headers print prominently

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/layout.tsx frontend/src/app/globals.css
git commit -m "feat: update layout and print styles for new design system"
```

---

## Task 10: Build Verification + Visual QA

**Files:**
- None (verification only)

- [ ] **Step 1: Run full build**

Run: `cd /workspace/frontend && pnpm build`
Expected: Build succeeds with no errors

- [ ] **Step 2: Run lint**

Run: `cd /workspace/frontend && pnpm lint`
Expected: No new lint errors

- [ ] **Step 3: Start dev server and manually verify**

Run: `cd /workspace/frontend && pnpm dev`

Check:
- Homepage: warm white background, centered card, vermilion accent
- Analysis page: Bento grid, tab navigation, hero verdict bar
- Report page: 卷式 headers, verdict blocks
- Theme toggle: switches to warm-black dark mode
- Chinese semantic tags: tiangan=vermilion, dizhi=indigo, shishen=gold
- Five elements: distinct colors, brown=earth, gold=metal
- Paper texture: barely visible on body background

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete frontend redesign — 古籍感+Apple风 visual system"
```
