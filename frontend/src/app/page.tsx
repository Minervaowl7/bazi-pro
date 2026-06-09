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
            [".hero-seal", ".hero-title", ".hero-subtitle", ".hero-divider", ".hero-desc", ".hero-form"],
            { autoAlpha: 1, y: 0, scale: 1 },
          );
          return;
        }

        const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
        tl.from(".hero-seal", { autoAlpha: 0, scale: 0.6, duration: 0.6 })
          .from(".hero-title", { autoAlpha: 0, y: 24, duration: 0.6 }, "-=0.2")
          .from(".hero-subtitle", { autoAlpha: 0, y: 12, duration: 0.4 }, "-=0.15")
          .from(".hero-divider", { autoAlpha: 0, scaleX: 0, duration: 0.3 }, "-=0.1")
          .from(".hero-desc", { autoAlpha: 0, y: 10, duration: 0.4 }, "-=0.1")
          .from(".hero-form", { autoAlpha: 0, y: 16, duration: 0.6 }, "-=0.15");
      });
    }, containerRef);
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="relative z-[1]">
      <section className="flex flex-col items-center justify-center px-6" style={{ minHeight: "100dvh" }}>
        <div className="text-center w-full flex flex-col items-center" style={{ maxWidth: 480 }}>
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
            className="hero-form w-full relative"
            style={{ maxWidth: 420,
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
        </div>
      </section>
    </div>
  );
}
