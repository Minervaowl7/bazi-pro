export const WUXING_COLORS: Record<string, string> = {
  木: "var(--wood)",
  火: "var(--fire)",
  土: "var(--earth)",
  金: "var(--metal)",
  水: "var(--water)",
};

export const WUXING_BG: Record<string, string> = {
  木: "rgba(34,197,94,0.12)",
  火: "rgba(239,68,68,0.12)",
  土: "rgba(234,179,8,0.12)",
  金: "rgba(245,158,11,0.12)",
  水: "rgba(59,130,246,0.12)",
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

export const SCHOOL_OPTIONS = [
  { value: "ziping", label: "传统子平法", desc: "格局用神 · 破格调整" },
  { value: "mangpai", label: "盲派", desc: "宾主体用 · 做功论命" },
  { value: "xinpai", label: "新派", desc: "百神空亡 · 反断论命" },
];

export const SCHOOL_OPTIONS_WITH_ALL = [
  ...SCHOOL_OPTIONS,
  { value: "all", label: "全流派对比", desc: "三派并排 · 综合参断" },
];