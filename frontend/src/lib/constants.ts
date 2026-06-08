// ================================================================
// Design Tokens (JS 层) — 引用 globals.css 变量，单一数据源
// ================================================================

/** 五行主色 */
export const WUXING_COLORS: Record<string, string> = {
  木: "var(--wx-wood)",
  火: "var(--wx-fire)",
  土: "var(--wx-earth)",
  金: "var(--wx-metal)",
  水: "var(--wx-water)",
};

/** 五行背景色 */
export const WUXING_BG: Record<string, string> = {
  木: "var(--wx-wood-bg)",
  火: "var(--wx-fire-bg)",
  土: "var(--wx-earth-bg)",
  金: "var(--wx-metal-bg)",
  水: "var(--wx-water-bg)",
};

/** 五行渐变背景（四柱干支方块） */
export const WUXING_GRADIENT_BG: Record<string, string> = {
  木: "linear-gradient(135deg, var(--wx-wood-bg), rgba(58,125,92,0.16))",
  火: "linear-gradient(135deg, var(--wx-fire-bg), rgba(196,82,58,0.16))",
  土: "linear-gradient(135deg, var(--wx-earth-bg), rgba(139,106,58,0.16))",
  金: "linear-gradient(135deg, var(--wx-metal-bg), rgba(197,165,90,0.16))",
  水: "linear-gradient(135deg, var(--wx-water-bg), rgba(46,92,138,0.16))",
};

/** 五行渐变填充（力量分布条） */
export const WUXING_BAR_GRADIENT: Record<string, string> = {
  木: "linear-gradient(90deg, var(--wx-wood), rgba(58,125,92,0.6))",
  火: "linear-gradient(90deg, var(--wx-fire), rgba(196,82,58,0.6))",
  土: "linear-gradient(90deg, var(--wx-earth), rgba(139,106,58,0.6))",
  金: "linear-gradient(90deg, var(--wx-metal), rgba(197,165,90,0.6))",
  水: "linear-gradient(90deg, var(--wx-water), rgba(46,92,138,0.6))",
};

/** 刑冲合害关系色 */
export const RELATION_COLORS: Record<string, string> = {
  合: "var(--wx-wood)",
  冲: "var(--wx-fire)",
  刑: "var(--wx-metal)",
  害: "var(--wx-earth)",
  合化: "var(--wx-wood)",
  化: "var(--wx-wood)",
};

// ================================================================
// 命理映射表
// ================================================================

export const GAN_WUXING: Record<string, string> = {
  甲: "木", 乙: "木", 丙: "火", 丁: "火", 戊: "土",
  己: "土", 庚: "金", 辛: "金", 壬: "水", 癸: "水",
};

export const ZHI_WUXING: Record<string, string> = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

// ================================================================
// 流派选项
// ================================================================

export const SCHOOL_OPTIONS = [
  { value: "ziping", label: "传统子平法", desc: "格局用神 · 破格调整" },
  { value: "mangpai", label: "盲派", desc: "宾主体用 · 做功论命" },
  { value: "xinpai", label: "新派", desc: "百神空亡 · 反断论命" },
];

export const SCHOOL_OPTIONS_WITH_ALL = [
  ...SCHOOL_OPTIONS,
  { value: "all", label: "全流派对比", desc: "三派并排 · 综合参断" },
];
