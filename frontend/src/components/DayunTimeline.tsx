"use client";

import { useState } from "react";
import { WUXING_COLORS, WUXING_BG, GAN_WUXING } from "@/lib/constants";

const TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
const SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];

function getYearGanzhi(year: number) {
  const ganIdx = (year - 4) % 10;
  const zhiIdx = (year - 4) % 12;
  return { gan: TIANGAN[ganIdx], zhi: DIZHI[zhiIdx], shengxiao: SHENGXIAO[zhiIdx] };
}

interface DayunStep {
  gan?: string;
  zhi?: string;
  age_range?: string;
  start_age?: number;
  gan_wuxing?: string;
  zhi_wuxing?: string;
  shishen_gan?: string;
  [key: string]: unknown;
}

interface Props {
  result: Record<string, unknown>;
}

export default function DayunTimeline({ result }: Props) {
  const dayun = (result.dayun as DayunStep[] | undefined)
    || (result.paipan_dayun as DayunStep[] | undefined);

  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (!dayun || dayun.length === 0) return null;

  const birthYear = Number(result.birth_year) || 0;
  const currentYear = new Date().getFullYear();
  const currentAge = birthYear ? currentYear - birthYear : 0;

  return (
    <div
      className="rounded-2xl overflow-hidden animate-fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)" }}
      >
        <h3
          className="text-base font-semibold tracking-wide"
          style={{ color: "var(--accent)" }}
        >
          大运流年
        </h3>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          共{dayun.length}步大运
        </span>
      </div>

      <div className="divide-y" style={{ borderColor: "var(--border-subtle)" }}>
        {dayun.map((d, i) => {
          const gan = String(d.gan || "");
          const zhi = String(d.zhi || "");
          const ganWuxing = d.gan_wuxing as string | undefined;
          const zhiWuxing = d.zhi_wuxing as string | undefined;
          const ganColor = ganWuxing ? WUXING_COLORS[ganWuxing] : "var(--text-primary)";
          const zhiColor = zhiWuxing ? WUXING_COLORS[zhiWuxing] : "var(--text-primary)";
          const ageRange = String(d.age_range || "");

          const startAge = Number(d.start_age || 0);
          const endAge = startAge + 9;
          const isCurrent = currentAge >= startAge && currentAge <= endAge && startAge > 0;
          const isExpanded = expandedIdx === i;

          const startYear = birthYear ? birthYear + startAge : 0;

          return (
            <div key={i}>
              <button
                className="w-full px-6 py-3.5 flex items-center gap-3 transition-colors duration-150"
                style={{
                  background: isCurrent ? "var(--accent-glow)" : "transparent",
                }}
                onClick={() => setExpandedIdx(isExpanded ? null : i)}
              >
                {isCurrent && (
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded font-bold shrink-0"
                    style={{ background: "var(--accent)", color: "var(--bg-primary)" }}
                  >
                    当前
                  </span>
                )}
                <span className="font-bold text-base" style={{ color: ganColor }}>{gan}</span>
                <span className="font-bold text-base" style={{ color: zhiColor }}>{zhi}</span>
                <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>
                  {ageRange || `${startAge}-${endAge}岁`}
                </span>
                {startYear > 0 && (
                  <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>
                    ({startYear}-{startYear + 9})
                  </span>
                )}
                <div className="flex gap-1 ml-auto">
                  {ganWuxing && (
                    <span
                      className="text-[9px] px-1 py-px rounded"
                      style={{ color: ganColor, background: WUXING_BG[ganWuxing] }}
                    >
                      {ganWuxing}
                    </span>
                  )}
                  {zhiWuxing && (
                    <span
                      className="text-[9px] px-1 py-px rounded"
                      style={{ color: zhiColor, background: WUXING_BG[zhiWuxing] }}
                    >
                      {zhiWuxing}
                    </span>
                  )}
                </div>
                <svg
                  width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className="shrink-0 transition-transform duration-200"
                  style={{
                    color: "var(--text-muted)",
                    transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                  }}
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              {isExpanded && (
                <div
                  className="px-6 pb-4 grid grid-cols-2 gap-1.5"
                  style={{ background: "var(--bg-secondary)" }}
                >
                  {Array.from({ length: 10 }, (_, j) => {
                    const year = startYear > 0 ? startYear + j : 0;
                    const age = startAge + j;
                    const { gan: lnGan, zhi: lnZhi, shengxiao } = year > 0
                      ? getYearGanzhi(year)
                      : { gan: "—", zhi: "", shengxiao: "" };
                    const lnGanWx = GAN_WUXING[lnGan] || "";
                    const lnGanColor = lnGanWx ? WUXING_COLORS[lnGanWx] : "var(--text-primary)";
                    const isThisYear = year > 0 && year === currentYear;
                    return (
                      <div
                        key={j}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs"
                        style={{
                          background: isThisYear ? "var(--accent-dim)" : "transparent",
                          border: isThisYear ? "1px solid var(--border-accent)" : "1px solid transparent",
                        }}
                      >
                        <span className="tabular-nums w-10" style={{ color: "var(--text-muted)" }}>{year > 0 ? year : `${age}岁`}</span>
                        <span className="font-medium" style={{ color: lnGanColor }}>{lnGan}{lnZhi}</span>
                        <span style={{ color: "var(--text-muted)" }}>{shengxiao}</span>
                        <span className="ml-auto tabular-nums" style={{ color: "var(--text-muted)" }}>{year > 0 ? `${age}岁` : ""}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}