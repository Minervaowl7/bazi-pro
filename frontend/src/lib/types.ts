export interface Wangshuai {
  verdict: string;
  deling_score: number;
  dedi_score: number;
  deshi_score: number;
  is_weak: boolean;
  is_strong: boolean;
  is_extreme_weak: boolean;
  is_extreme_strong: boolean;
}

export interface Strength {
  day_master: string;
  deling: { status: string; score: number };
  dedi: { score: number; details: unknown[]; level: string };
  deshi: { score: number; details: unknown[]; level: string };
  wangshuai: Wangshuai;
}

export interface Pattern {
  pattern: string;
  layer: number;
  confidence: number;
  reason: string;
}

export interface CangganItem {
  gan: string;
  qi: string;
  wuxing: string;
  shishen: string;
}

export interface ShishenPillar {
  position: string;
  gan: string;
  zhi: string;
  wuxing_gan: string;
  wuxing_zhi: string;
  shishen: string;
  shishen_gan: string;
  shishen_zhi: string;
  nayin: string;
  changsheng: string;
  canggan: CangganItem[];
}

export interface Shishen {
  pillars: ShishenPillar[];
  note?: string;
}

export interface Yongshen {
  yongshen: string;
  xishen: string[];
  jishen: string[];
  confidence: number;
}

export interface ElementForces {
  raw: Record<string, number>;
  percent: Record<string, number>;
  total: number;
  note?: string;
}

export interface Tiaohou {
  has_tiaohou: boolean;
  tiaohou_gan: string[];
  tiaohou_wx: string[];
}

export interface Relation {
  type: string;
  description: string;
}

export interface ShenshaItem {
  name: string;
  position: string;
  type: string;
  desc: string;
}

export interface DayunStep {
  age_range: string;
  gan: string;
  zhi: string;
  gan_wuxing: string;
  zhi_wuxing: string;
  start_age?: number;
  end_age?: number;
}

export interface ValidationResult {
  valid: boolean;
  bazi: string;
  day_master: string;
  gender: string;
  errors?: string[];
}

export interface AnalysisResultData {
  [key: string]: unknown;
  run_id: string;
  status: string;
  detail_level: string;
  school: string;
  started_at: string;
  completed_at?: string;
  disclaimer: string;
  validation: ValidationResult;
  strength: Strength;
  pattern: Pattern;
  shishen: Shishen;
  yongshen: Yongshen;
  elements: ElementForces;
  tiaohou: Tiaohou;
  relations: Relation[];
  shensha?: ShenshaItem[];
  gongwei?: unknown;
  dayun?: DayunStep[];
  qiyun_age?: number;
  birth_year?: number;
  school_analysis?: unknown;
  school_analyses?: Record<string, unknown>;
  school_warning?: string;
  error?: string;
}
