"use client";

import BirthForm from "@/components/BirthForm";

const FEATURES = [
  {
    title: "确定性计算",
    desc: "十神、藏干、五行力量、旺衰、格局、喜用神，全部确定性推导，零 LLM 参与",
    icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
  },
  {
    title: "古籍引证",
    desc: "2964 条古籍语料，6 部经典（子平真诠/滴天髓/渊海子平/穷通宝鉴/神峰通考/三命通会）",
    icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  },
  {
    title: "三大流派",
    desc: "子平法（格局用神）、盲派（宾主做功）、新派（百神空亡），一键对比三种视角",
    icon: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z",
  },
  {
    title: "破格检测",
    desc: "六层格局筛查 + 破格条件检测，每个破格类型均有古籍原文依据",
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
  },
];

const STATS = [
  { value: "507", label: "Golden Cases" },
  { value: "13", label: "核心模块" },
  { value: "6", label: "经典古籍" },
  { value: "3", label: "分析流派" },
];

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)]" style={{ background: "var(--background)" }}>
      {/* Hero + Form */}
      <section className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20 px-6 md:px-12 lg:px-16 xl:px-24 py-12 lg:py-20">
        {/* Left: intro */}
        <div className="flex-1 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-medium mb-6"
            style={{ background: "var(--accent-dim)", color: "var(--color-accent)", border: "1px solid var(--border-accent)" }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
            v5.2 · 典籍对齐版
          </div>

          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4"
            style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
            确定性八字
            <br />
            <span style={{ color: "var(--color-scholar-blue)" }}>命理引擎</span>
          </h1>

          <p className="text-base md:text-lg leading-relaxed mb-8" style={{ color: "var(--color-text-secondary)" }}>
            算析分离架构，核心计算零 LLM 依赖。十神推导、格局筛查、喜用神判定，每一步均可追溯到确定性规则与古籍原文。
          </p>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-xl md:text-2xl font-bold tabular-nums" style={{ color: "var(--color-accent)" }}>
                  {s.value}
                </div>
                <div className="text-[10px] mt-1 uppercase tracking-wider" style={{ color: "var(--color-text-muted)" }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: form */}
        <div className="w-full max-w-md">
          <div className="p-6 md:p-8 rounded-2xl"
            style={{ background: "var(--surface)", boxShadow: "0 4px 24px rgba(0,0,0,0.08)", border: "1px solid var(--color-border)" }}>
            <BirthForm />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 md:px-12 lg:px-16 xl:px-24 py-16 border-t" style={{ borderColor: "var(--color-border)" }}>
        <div className="text-center mb-12">
          <h2 className="text-xl md:text-2xl font-bold mb-2" style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
            核心能力
          </h2>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            每一项计算结果都可追溯，每一条引证都有出处
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f) => (
            <div key={f.title} className="p-5 rounded-xl transition-all duration-200 hover:shadow-md group"
              style={{ background: "var(--surface)", border: "1px solid var(--color-border)" }}>
              <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4 transition-colors"
                style={{ background: "var(--accent-dim)" }}>
                <svg className="w-5 h-5" style={{ color: "var(--color-accent)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={f.icon} />
                </svg>
              </div>
              <h3 className="text-sm font-semibold mb-1.5" style={{ color: "var(--color-text-primary)" }}>{f.title}</h3>
              <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-muted)" }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 md:px-12 lg:px-16 xl:px-24 py-8 border-t text-center" style={{ borderColor: "var(--color-border)" }}>
        <p className="text-[11px]" style={{ color: "var(--color-text-muted)" }}>
          bazi-pro · 确定性命理引擎 · 算析分离 · 古籍引证 · 零幻觉
        </p>
      </footer>
    </div>
  );
}
