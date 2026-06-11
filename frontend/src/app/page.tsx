"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { gsap, useGSAP } from "@/lib/gsap";
import { useAnalysisStore } from "@/stores/analysisStore";
import BirthForm from "@/components/BirthForm";

/* ── 示例命盘预设数据 ── */
const DEMO_INPUT = { 性别: "男", 阳历: "1990-05-15 07:00" } as const;

/* ── 功能亮点数据 ── */
const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" /><path d="M2 12h20" />
      </svg>
    ),
    title: "紫微命盘",
    desc: "十二宫位完整排布，星曜组合一目了然",
    accent: "var(--wx-fire)",
    bg: "var(--wx-fire-bg)",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 3h5v5" /><path d="M21 3l-7 7" /><path d="M8 21H3v-5" /><path d="M3 21l7-7" />
      </svg>
    ),
    title: "三流派对比",
    desc: "子平·盲派·新派并行分析，综合参断",
    accent: "var(--wx-water)",
    bg: "var(--wx-water-bg)",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: "AI 智能解读",
    desc: "古籍条文驱动，每句可追溯至原文",
    accent: "var(--jade)",
    bg: "var(--wx-wood-bg)",
  },
] as const;

export default function Home() {
  const router = useRouter();
  const { submitPaipan, startAnalysis } = useAnalysisStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState("");

  /* ── 示例命盘一键体验 ── */
  async function handleDemo() {
    setDemoLoading(true);
    setDemoError("");
    try {
      // 第一步：排盘
      await submitPaipan(DEMO_INPUT);
      // 排盘结果已写入 store，读取最新值
      const paipanResult = useAnalysisStore.getState().paipanResult;
      if (!paipanResult || paipanResult.status !== "completed") {
        throw new Error("排盘失败，请稍后重试");
      }
      // 第二步：提交深度分析
      const analysisId = await startAnalysis({
        性别: paipanResult.性别,
        八字: paipanResult.八字,
        日主: paipanResult.日主,
        阳历: DEMO_INPUT.阳历,
        生肖: paipanResult.生肖,
        school: "ziping",
      });
      router.push(`/analyze/${analysisId}`);
    } catch (err) {
      setDemoError(err instanceof Error ? err.message : "示例命盘加载失败");
    } finally {
      setDemoLoading(false);
    }
  }

  /* ── GSAP 入场动画 ── */
  useGSAP(() => {
    const reduceMotion = "(prefers-reduced-motion: reduce)";

    gsap.context(() => {
      gsap.matchMedia().add(reduceMotion, (context) => {
        if (context.conditions?.[reduceMotion]) {
          gsap.set(
            [
              ".hero-seal", ".hero-title", ".hero-subtitle", ".hero-divider",
              ".hero-desc", ".hero-form", ".hero-demo-btn", ".hero-features",
            ],
            { autoAlpha: 1, y: 0, scale: 1 },
          );
          gsap.set(".feature-card", { autoAlpha: 1, y: 0 });
          return;
        }

        const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
        tl.from(".hero-seal", { autoAlpha: 0, scale: 0.6, duration: 0.6 })
          .from(".hero-title", { autoAlpha: 0, y: 24, duration: 0.6 }, "-=0.2")
          .from(".hero-subtitle", { autoAlpha: 0, y: 12, duration: 0.4 }, "-=0.15")
          .from(".hero-divider", { autoAlpha: 0, scaleX: 0, duration: 0.3 }, "-=0.1")
          .from(".hero-desc", { autoAlpha: 0, y: 10, duration: 0.4 }, "-=0.1")
          .from(".hero-form", { autoAlpha: 0, y: 16, duration: 0.6 }, "-=0.15")
          .from(".hero-demo-btn", { autoAlpha: 0, y: 10, duration: 0.4 }, "-=0.1")
          .from(".hero-features", { autoAlpha: 0, y: 16, duration: 0.5 }, "-=0.1")
          .from(".feature-card", { autoAlpha: 0, y: 20, stagger: 0.12, duration: 0.5 }, "-=0.3");
      });
    }, containerRef);
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="relative z-[1]">
      <section className="min-h-[100dvh] flex flex-col items-center justify-center px-6">
        <div className="text-center w-full max-w-[480px] flex flex-col items-center">
          {/* 品牌印章 */}
          <div className="hero-seal mb-7" style={{ visibility: "hidden" }}>
            <div
              className="w-14 h-14 rounded-[10px] flex items-center justify-center"
              style={{
                background: "linear-gradient(145deg, var(--cinnabar), #8a3a24)",
                boxShadow: "0 2px 8px rgba(201,100,66,0.2)",
              }}
            >
              <span
                className="text-2xl font-bold text-white"
                style={{ fontFamily: "var(--font-display)" }}
              >
                命
              </span>
            </div>
          </div>

          {/* 标题 */}
          <h1
            className="hero-title font-bold leading-[1.15] tracking-tight mb-1.5"
            style={{
              fontSize: "clamp(36px, 6vw, 52px)",
              color: "var(--ink)",
              fontFamily: "var(--font-display)",
              visibility: "hidden",
            }}
          >
            八字排盘
          </h1>

          {/* 副标题 */}
          <p
            className="hero-subtitle mb-2 tracking-[0.15em]"
            style={{
              fontSize: "clamp(16px, 2.5vw, 22px)",
              color: "var(--text-2)",
              fontFamily: "var(--font-display)",
              visibility: "hidden",
            }}
          >
            古法排盘 · 智能解读
          </p>

          {/* 分隔线 */}
          <div
            className="hero-divider w-10 h-[2px] rounded mb-3"
            style={{
              background: "linear-gradient(90deg, var(--gold), rgba(180,154,92,0.3))",
              visibility: "hidden",
            }}
          />

          {/* 描述 */}
          <p
            className="hero-desc text-sm mb-9 tracking-wide"
            style={{ color: "var(--text-3)", visibility: "hidden" }}
          >
            每一步推导皆可追溯至古籍原文
          </p>

          {/* 表单卡片 */}
          <div
            className="hero-form w-full max-w-[420px] relative"
            style={{
              background: "var(--surface)",
              border: "0.5px solid var(--border)",
              borderRadius: "var(--r)",
              boxShadow: "var(--shadow-card)",
              visibility: "hidden",
            }}
          >
            <div
              className="absolute top-0 left-0 right-0 h-[2px] opacity-60"
              style={{
                background: "linear-gradient(90deg, var(--cinnabar), var(--gold), var(--wx-wood))",
              }}
            />
            <div className="p-7 pb-6">
              <BirthForm />
            </div>
          </div>

          {/* 示例命盘按钮 */}
          <div className="hero-demo-btn w-full max-w-[420px] mt-5" style={{ visibility: "hidden" }}>
            <button
              type="button"
              onClick={handleDemo}
              disabled={demoLoading}
              className="w-full py-3 rounded-xl text-sm font-medium tracking-wide transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed active:scale-[0.98] flex items-center justify-center gap-2"
              style={{
                minHeight: 44,
                background: "var(--surface-2)",
                color: "var(--text-2)",
                border: "1px solid var(--border)",
              }}
            >
              {demoLoading ? (
                <>
                  <svg className="animate-spin shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                  </svg>
                  排盘中…
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  试试示例命盘
                </>
              )}
            </button>
            {demoError && (
              <p className="text-xs mt-2 text-center" style={{ color: "var(--danger)" }}>{demoError}</p>
            )}
            <p className="text-[11px] mt-2 text-center" style={{ color: "var(--text-4)" }}>
              1990-05-15 辰时 · 男 · 庚午年
            </p>
          </div>

          {/* 功能亮点 */}
          <div className="hero-features w-full max-w-[420px] mt-12 mb-8" style={{ visibility: "hidden" }}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {FEATURES.map((f) => (
                <div
                  key={f.title}
                  className="feature-card flex flex-col items-center text-center p-4 rounded-xl transition-all duration-200"
                  style={{
                    background: "var(--surface)",
                    border: "0.5px solid var(--border)",
                    visibility: "hidden",
                  }}
                >
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                    style={{ background: f.bg, color: f.accent }}
                  >
                    {f.icon}
                  </div>
                  <h3
                    className="text-xs font-semibold mb-1 tracking-wide"
                    style={{ color: "var(--ink)" }}
                  >
                    {f.title}
                  </h3>
                  <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-3)" }}>
                    {f.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
