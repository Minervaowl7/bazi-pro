# BaZi Pro · Brand Spec — Direction C (Light)

> Design philosophy: Imperial Luxury Light (故宫文创式古典奢侈 · 浅色画布)
> Created: 2026-06-08

## Design Principles

1. **Warm canvas** — 宣纸/古籍质感的米白底，不是冷白
2. **Gold whisper** — 金色只用于 0.5-1px 描边和极少量装饰线，不用金色大色块
3. **Cinnabar for emphasis** — 朱砂红是唯一强调色，选中态、关键数据、日主高亮
4. **Breathe through space** — 60%+ 是呼吸空间，内容稀疏精致
5. **Typography as hierarchy** — 衬线大字标题 + 系统正文，靠字号和粗细分层

## Color Palette

### Base
- Background: `#f5f2eb` — 宣纸色，温暖米白
- Surface: `#fffdf9` — 卡片底色，微暖白
- Surface secondary: `#f0ede6` — 次级区域
- Border: `rgba(180,160,120,0.2)` — 淡金褐描边
- Border strong: `rgba(180,160,120,0.35)` — 交互态

### Brand Colors
- Gold: `#b49a5c` — 古金色，用于描边、装饰线（不是亮金）
- Gold muted: `rgba(180,154,92,0.08)` — 金色极淡背景
- Cinnabar: `#c96442` — 朱砂红，强调色
- Cinnabar light: `rgba(201,100,66,0.1)` — 朱砂淡底
- Ink: `#2c2418` — 浓墨色，主文字

### Text
- Primary: `#2c2418` — 浓墨，主文字
- Secondary: `#6b6154` — 次要文字
- Tertiary: `#9e9488` — 辅助文字
- Muted: `#c4bcb0` — 最淡

### Five Elements (传统五行色)
- Wood: `#3a7d5c` — 翡翠绿（木之本色）
- Fire: `#c4523a` — 深朱砂（火之本色）
- Earth: `#8b6a3a` — 褐色（土之本色，黄土）
- Metal: `#c5a55a` — 金色（金之本色，金属光泽）
- Water: `#2e5c8a` — 靛蓝（水之本色，深沉墨水）

## Typography

- Display: `'Noto Serif SC', 'Songti SC', serif` — 标题、四柱天干地支
- Body: `-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif` — 正文
- Mono: `'JetBrains Mono', 'Fira Code', monospace` — 数据

### Scale
- Hero title: 64-72px, font-weight 700, letter-spacing -0.02em
- Section title: 24-28px, font-weight 600
- Card title: 17-19px, font-weight 600
- Body: 15-16px, line-height 1.65
- Caption: 12-13px, line-height 1.5

## Spacing & Layout

- Max content width: 960px (centered)
- Card padding: 28-36px
- Section gap: 16-20px
- Card border-radius: 12px
- Card border: 0.5-1px solid `rgba(180,160,120,0.2)`

## Shadows

- Card: `0 1px 3px rgba(0,0,0,0.04), 0 0 0 0.5px rgba(180,160,120,0.15)`
- Elevated: `0 8px 32px rgba(0,0,0,0.08)`
- Hover: `0 4px 16px rgba(0,0,0,0.06), 0 0 0 0.5px rgba(180,160,120,0.25)`

## Animation

- Default transition: 400ms ease-in-out
- Hover: 250ms ease
- Scroll entrance: fade-up 16px + opacity 0→1, 500ms ease-out
- Stagger delay: 60ms between items

## Component Patterns

### Card
```
background: #fffdf9
border: 0.5-1px solid rgba(180,160,120,0.2)
border-radius: 12px
padding: 28-36px
box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 0 0 0.5px rgba(180,160,120,0.15)
```

### Badge / Pill
```
background: rgba(180,154,92,0.08)
border: 1px solid rgba(180,154,92,0.15)
border-radius: 9999px
padding: 4px 14px
font-size: 12px
```

### Button (Primary)
```
background: linear-gradient(135deg, #c96442, #a8503a)
border: none
border-radius: 8px
color: #fff
box-shadow: 0 2px 12px rgba(201,100,66,0.25)
```

### Divider
```
height: 1px
background: linear-gradient(90deg, transparent, rgba(180,160,120,0.25), transparent)
```

### Decorative Gold Line
```
width: 40px
height: 2px
background: linear-gradient(90deg, #b49a5c, rgba(180,154,92,0.3))
```
