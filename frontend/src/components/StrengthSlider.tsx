"use client";

import { useRef, useMemo } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";

const LEVELS = ["极弱", "偏弱", "中和", "偏旺", "极旺"] as const;

function verdictToPosition(verdict?: string): number {
  if (!verdict) return 2;
  if (verdict === "极弱") return 0;
  if (verdict === "身弱" || verdict === "中和偏弱" || verdict === "偏弱") return 1;
  if (verdict === "中和") return 2;
  if (verdict === "偏旺" || verdict === "中和偏旺" || verdict === "身旺") return 3;
  if (verdict === "极旺") return 4;
  if (verdict.includes("弱")) return 1;
  if (verdict.includes("旺") || verdict.includes("强")) return 3;
  return 2;
}

function scoreToBarWidth(score?: number): number {
  if (typeof score !== "number" || score === 0) return 8;
  return Math.min(Math.abs(score) * 6 + 8, 100);
}

interface StrengthData {
  wangshuai?: { verdict?: string };
  deling?: { status?: string; score?: number };
  dedi?: { score?: number; level?: string };
  deshi?: { score?: number; level?: string };
}

interface Props {
  strength?: StrengthData;
  dayMaster?: string;
}

export default function StrengthSlider({ strength, dayMaster }: Props) {
  const verdict = strength?.wangshuai?.verdict;
  const deling = strength?.deling;
  const dedi = strength?.dedi;
  const deshi = strength?.deshi;
  const position = verdictToPosition(verdict);
  const pct = (position / (LEVELS.length - 1)) * 100;

  const sectionRef = useRef<HTMLDivElement>(null);
  const verdictBadgeRef = useRef<HTMLDivElement>(null);
  const barRefs = useRef<(HTMLDivElement | null)[]>([]);
  const reasonRef = useRef<HTMLDivElement>(null);

  const bars = useMemo(() => [
    { label: "得令", data: deling },
    { label: "得地", data: dedi },
    { label: "得势", data: deshi },
  ], [deling, dedi, deshi]);

  const prefersReducedMotion = usePrefersReducedMotion();

  useGSAP(
    () => {
      if (prefersReducedMotion) {
        gsap.set(sectionRef.current, { autoAlpha: 1 });
        gsap.set(verdictBadgeRef.current, { autoAlpha: 1, x: 0 });
        gsap.set(barRefs.current, { scaleX: 1 });
        gsap.set(reasonRef.current, { autoAlpha: 1, y: 0 });
        return;
      }

      gsap.set(barRefs.current, { scaleX: 0, transformOrigin: "left center" });
      gsap.set(verdictBadgeRef.current, { autoAlpha: 0, x: -24 });
      gsap.set(reasonRef.current, { autoAlpha: 0, y: 8 });

      const tl = gsap.timeline();

      tl.fromTo(
        sectionRef.current,
        { autoAlpha: 0, y: 28 },
        { autoAlpha: 1, y: 0, duration: 0.7, ease: "power3.out" }
      );

      tl.fromTo(
        verdictBadgeRef.current,
        { autoAlpha: 0, x: -24 },
        { autoAlpha: 1, x: 0, duration: 0.5, ease: "back.out(1.4)" },
        "-=0.3"
      );

      tl.to(
        barRefs.current,
        { scaleX: 1, duration: 0.8, stagger: 0.15, ease: "power2.out" },
        "-=0.2"
      );

      if (reasonRef.current) {
        tl.fromTo(
          reasonRef.current,
          { autoAlpha: 0, y: 8 },
          { autoAlpha: 1, y: 0, duration: 0.5, ease: "power2.out" },
          "-=0.2"
        );
      }
    },
    { scope: sectionRef }
  );

  return (
    <section
      ref={sectionRef}
      className="card"
      style={{ opacity: prefersReducedMotion ? 1 : 0 }}
    >
      <div className="relative flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
        <div className="flex items-center gap-3">
          {/* 标题左侧金色装饰条 */}
          <div className="w-[3px] h-3.5 rounded-sm" style={{ background: "linear-gradient(180deg, var(--gold), rgba(180,154,92,0.3))" }} />
          <h3 className="font-bold text-sm" style={{ fontFamily: "var(--font-display)" }}>日主强弱</h3>
        </div>
        {dayMaster && (
          <span className="font-bold text-[17px]" style={{ fontFamily: "var(--font-display)" }}>{dayMaster}</span>
        )}
      </div>

      <div className="p-6">
        {/* 三色渐变轨道 */}
        <div className="relative mb-6">
          <div style={{
            height: 6,
            borderRadius: 3,
            background: "linear-gradient(90deg, var(--wx-water) 0%, var(--wx-water) 20%, var(--wx-earth) 40%, var(--wx-earth) 60%, var(--wx-fire) 80%, var(--wx-fire) 100%)",
            opacity: 0.7,
          }} />

          {/* 圆形 marker */}
          <div className="absolute top-1/2" style={{ left: `${pct}%`, transform: "translate(-50%,-50%)" }}>
            <div style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: "var(--surface)",
              border: "2px solid var(--cinnabar)",
              boxShadow: "0 0 0 3px rgba(201,100,66,0.12), 0 1px 4px rgba(201,100,66,0.2)",
            }} />
          </div>
        </div>

        {/* 五段标签 */}
        <div className="flex justify-between mb-6">
          {LEVELS.map((l, i) => (
            <span key={l} className="font-medium" style={{
              fontSize: 13,
              color: i === position ? "var(--cinnabar)" : "var(--text-4)",
              fontWeight: i === position ? 700 : 400,
              fontFamily: "var(--font-display)",
            }}>
              {l}
            </span>
          ))}
        </div>

        {/* 判定结论 — 「」引号装饰 */}
        {verdict && (
          <div ref={verdictBadgeRef} className="text-center mb-7">
            <span style={{
              fontSize: 20,
              fontWeight: 600,
              color: "var(--cinnabar)",
              fontFamily: "var(--font-display)",
            }}>
              「{verdict}」
            </span>
          </div>
        )}

        {/* 得令/得地/得势 三栏 */}
        <div className="grid grid-cols-3 gap-4">
          {bars.map((item, idx) => {
            const d = item.data as Record<string, unknown> | undefined;
            const display = (d?.status as string | undefined) || (d?.level as string | undefined) || "—";
            const scoreDisplay = typeof item.data?.score === "number"
              ? `${item.data.score > 0 ? "+" : ""}${Number.isInteger(item.data.score) ? item.data.score : item.data.score.toFixed(1)}`
              : "";
            const barWidth = scoreToBarWidth(item.data?.score);

            return (
              <div key={item.label} className="text-center p-5 rounded-[10px]" style={{ background: "var(--surface-2)" }}>
                <div className="mb-2 font-semibold text-[11px] uppercase tracking-[0.08em]" style={{ color: "var(--text-4)" }}>{item.label}</div>
                <div className="font-bold text-lg mb-1" style={{ fontFamily: "var(--font-display)" }}>{display}</div>
                {scoreDisplay && <div className="text-[13px]" style={{ color: "var(--text-3)" }}>{scoreDisplay}</div>}
                <div
                  ref={(el) => { barRefs.current[idx] = el; }}
                  style={{
                    height: 3,
                    marginTop: 6,
                    width: `${barWidth}%`,
                    borderRadius: 2,
                    background: "linear-gradient(90deg, var(--gold), rgba(180,154,92,0.5))",
                    transformOrigin: "left center",
                    transform: prefersReducedMotion ? "scaleX(1)" : "scaleX(0)",
                  }}
                />
              </div>
            );
          })}
        </div>

        {verdict && (
          <div ref={reasonRef} className="mt-5 text-center text-[13px]" style={{ color: "var(--text-3)" }}>
            {position <= 1 ? "日主偏弱，宜扶助" : position >= 3 ? "日主偏旺，宜抑制" : "日主中和，五行流通"}
          </div>
        )}
      </div>
    </section>
  );
}
