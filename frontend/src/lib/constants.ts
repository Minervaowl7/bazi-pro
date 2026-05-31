export const WUXING_COLORS: Record<string, string> = {
  木: "var(--wood)",
  火: "var(--fire)",
  土: "var(--earth)",
  金: "var(--metal)",
  水: "var(--water)",
};

export const WUXING_BG: Record<string, string> = {
  木: "rgba(74,222,128,0.14)",
  火: "rgba(251,113,133,0.14)",
  土: "rgba(251,191,36,0.12)",
  金: "rgba(212,212,224,0.10)",
  水: "rgba(96,165,250,0.14)",
};

export const WUXING_GLOW: Record<string, string> = {
  木: "rgba(74,222,128,0.25)",
  火: "rgba(251,113,133,0.25)",
  土: "rgba(251,191,36,0.25)",
  金: "rgba(212,212,224,0.2)",
  水: "rgba(96,165,250,0.25)",
};

export const WUXING_PILL_BG: Record<string, string> = {
  木: "var(--wood-pill)",
  火: "var(--fire-pill)",
  土: "var(--earth-pill)",
  金: "var(--metal-pill)",
  水: "var(--water-pill)",
};

export const WUXING_PILL_BORDER: Record<string, string> = {
  木: "var(--wood-pill-border)",
  火: "var(--fire-pill-border)",
  土: "var(--earth-pill-border)",
  金: "var(--metal-pill-border)",
  水: "var(--water-pill-border)",
};

export const RELATION_COLORS: Record<string, string> = {
  合: "#22c55e",
  冲: "#ef4444",
  刑: "#f97316",
  害: "#a855f7",
  合化: "#22c55e",
  化: "#22c55e",
};

export const GAN_WUXING: Record<string, string> = {
  甲: "木",
  乙: "木",
  丙: "火",
  丁: "火",
  戊: "土",
  己: "土",
  庚: "金",
  辛: "金",
  壬: "水",
  癸: "水",
};

export const ZHI_WUXING: Record<string, string> = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

export const SCHOOL_OPTIONS = [
  { value: "ziping", label: "传统子平法", desc: "格局用神 · 破格调整" },
  { value: "mangpai", label: "盲派", desc: "宾主体用 · 做功论命" },
  { value: "xinpai", label: "新派", desc: "百神空亡 · 反断论命" },
];

export const SCHOOL_OPTIONS_WITH_ALL = [
  ...SCHOOL_OPTIONS,
  { value: "all", label: "全流派对比", desc: "三派并排 · 综合参断" },
];