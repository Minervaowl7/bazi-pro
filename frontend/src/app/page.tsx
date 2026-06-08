"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import BirthForm from "@/components/BirthForm";

export default function Home() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const reduceMotion = "(prefers-reduced-motion: reduce)";

    gsap.context(() => {
      gsap.matchMedia().add(reduceMotion, (context) => {
        if (context.conditions?.[reduceMotion]) {
          gsap.set(
            [".hero-seal", ".hero-title", ".hero-subtitle", ".hero-divider", ".hero-desc", ".hero-form", ".cap-item"],
            { autoAlpha: 1, y: 0, x: 0, scale: 1, rotation: 0 },
          );
          return;
        }

        const heroTL = gsap.timeline({ defaults: { ease: "power2.out" } });

        heroTL
          .from(".hero-seal", { autoAlpha: 0, scale: 0.4, rotation: -15, duration: 0.7 })
          .from(".hero-title", { autoAlpha: 0, y: 30, duration: 0.7 }, "-=0.3")
          .from(".hero-subtitle", { autoAlpha: 0, y: 16, duration: 0.5 }, "-=0.2")
          .from(".hero-divider", { autoAlpha: 0, scaleX: 0, duration: 0.4 }, "-=0.1")
          .from(".hero-desc", { autoAlpha: 0, y: 12, duration: 0.5 }, "-=0.1")
          .from(".hero-form", { autoAlpha: 0, y: 20, duration: 0.7, ease: "power3.out" }, "-=0.2");

        gsap.from(".cap-item", {
          autoAlpha: 0, y: 16, stagger: 0.08, duration: 0.5, delay: 1.2,
        });
      });
    }, containerRef);
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="relative z-[1]">
      {/* Hero */}
      <section className="min-h-[100dvh] flex flex-col items-center justify-center relative overflow-hidden px-6">
        {/* 同心圆装饰 */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(600px,80vw)] h-[min(600px,80vw)] rounded-full pointer-events-none" style={{ border: "1px solid var(--border-subtle)" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(400px,56vw)] h-[min(400px,56vw)] rounded-full pointer-events-none" style={{ border: "1px solid rgba(180,160,120,0.06)" }} />

        {/* 五行方位文字 */}
        {[
          { wx: "木", cls: "top-[18%] left-1/2 -translate-x-[180px]", color: "var(--wx-wood)" },
          { wx: "火", cls: "top-[35%] right-[18%]", color: "var(--wx-fire)" },
          { wx: "土", cls: "bottom-[30%] right-[22%]", color: "var(--wx-earth)" },
          { wx: "金", cls: "bottom-[18%] left-1/2 -translate-x-[180px]", color: "var(--wx-metal)" },
          { wx: "水", cls: "top-[35%] left-[18%]", color: "var(--wx-water)" },
        ].map(({ wx, cls, color }) => (
          <span key={wx} className={`hidden sm:block absolute ${cls} text-base font-semibold pointer-events-none select-none`} style={{ fontFamily: "var(--font-display)", color, opacity: 0.10 }} aria-hidden="true">
            {wx}
          </span>
        ))}

        {/* 内容区 */}
        <div className="text-center relative z-1 w-full max-w-[480px] flex flex-col items-center">
          {/* 品牌印章 */}
          <div className="hero-seal mb-7" style={{ visibility: "hidden" }}>
            <div className="w-14 h-14 rounded-[10px] flex items-center justify-center relative" style={{ background: "linear-gradient(145deg, var(--cinnabar), #8a3a24)", boxShadow: "0 0 0 1px rgba(255,255,255,0.08) inset, 0 2px 8px rgba(201,100,66,0.2), 0 0 24px rgba(201,100,66,0.1)" }}>
              <span className="text-2xl font-bold text-white" style={{ fontFamily: "var(--font-display)" }}>命</span>
              <div className="absolute inset-[3px] rounded-[7px] pointer-events-none" style={{ border: "1px solid rgba(255,255,255,0.1)" }} />
            </div>
          </div>

          {/* 标题 */}
          <h1 className="hero-title font-bold leading-[1.15] tracking-tight mb-1.5" style={{ fontSize: "clamp(36px, 6vw, 52px)", color: "var(--ink)", fontFamily: "var(--font-display)", visibility: "hidden" }}>
            八字排盘
          </h1>

          {/* 副标题 */}
          <p className="hero-subtitle font-normal mb-2 tracking-[0.15em]" style={{ fontSize: "clamp(16px, 2.5vw, 22px)", color: "var(--text-2)", fontFamily: "var(--font-display)", visibility: "hidden" }}>
            古法排盘 · 智能解读
          </p>

          {/* 金色分隔线 */}
          <div className="hero-divider w-10 h-[2px] rounded mb-3" style={{ background: "linear-gradient(90deg, var(--gold), rgba(180,154,92,0.3))", visibility: "hidden" }} />

          {/* 描述 */}
          <p className="hero-desc text-sm mb-9 tracking-wide" style={{ color: "var(--text-3)", visibility: "hidden" }}>
            每一步推导皆可追溯至古籍原文，零幻觉
          </p>

          {/* 表单卡片 */}
          <div className="hero-form w-full max-w-[420px] relative" style={{ background: "var(--surface)", border: "0.5px solid var(--border)", borderRadius: "var(--r)", boxShadow: "var(--shadow-card)", visibility: "hidden" }}>
            {/* 顶部金线 */}
            <div className="absolute top-0 left-0 right-0 h-[2px] opacity-60" style={{ background: "linear-gradient(90deg, var(--cinnabar), var(--gold), var(--wx-wood))" }} />
            <div className="p-7 pb-6">
              <BirthForm />
            </div>
          </div>

          {/* 能力标签 */}
          <div className="cap-bar flex gap-5 justify-center mt-10 flex-wrap">
            {[
              { dot: "var(--wx-wood)", text: "确定性计算 · 零 LLM" },
              { dot: "var(--wx-earth)", text: "古籍引用 · 2964 条" },
              { dot: "var(--wx-water)", text: "三流派 · 一键对比" },
              { dot: "var(--wx-fire)", text: "破格检测 · 六层筛查" },
            ].map((f, i) => (
              <div key={i} className="cap-item flex items-center gap-1.5 text-xs tracking-wide" style={{ color: "var(--text-3)", visibility: "hidden" }}>
                <span className="w-[5px] h-[5px] rounded-full shrink-0" style={{ background: f.dot }} />
                {f.text}
              </div>
            ))}
          </div>
        </div>

        {/* 页脚版本号 */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-[11px] tracking-widest z-[1]" style={{ color: "var(--text-4)" }}>
          bazi-pro v5.3
        </div>
      </section>
    </div>
  );
}
