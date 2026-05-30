export const WUXING_COLORS: Record<string, string> = {
  木: "var(--wood)",
  火: "var(--fire)",
  土: "var(--earth)",
  金: "var(--metal)",
  水: "var(--water)",
};

export const WUXING_BG: Record<string, string> = {
  木: "var(--wood-dim)",
  火: "var(--fire-dim)",
  土: "var(--earth-dim)",
  金: "var(--metal-dim)",
  水: "var(--water-dim)",
};

export const WUXING_GLOW: Record<string, string> = {
  木: "rgba(74,158,110,0.25)",
  火: "rgba(212,64,48,0.25)",
  土: "rgba(139,94,60,0.25)",
  金: "rgba(193,154,66,0.25)",
  水: "rgba(63,111,159,0.25)",
};

export const RELATION_COLORS: Record<string, string> = {
  合: "#C19A42",
  冲: "#C53030",
  刑: "#8A5C9E",
  害: "#999999",
  合化: "#C19A42",
  化: "#C19A42",
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
