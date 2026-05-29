"use client";

import { WUXING_COLORS, WUXING_BG } from "@/lib/constants";

interface Props {
  result: Record<string, unknown>;
}

export default function DayunTimeline({ result }: Props) {
  const dayun = (result.dayun as Array<Record<string, unknown>> | undefined)
    || (result.paipan_dayun as Array<Record<string, unknown>> | undefined);

  if (!dayun || dayun.length === 0) return null;

  const currentAge = new Date().getFullYear() - (Number(result.birth_year) || 0);

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
          大运时间线
        </h3>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          共{dayun.length}步大运
        </span>
      </div>

      <div className="px-6 py-5">
        <div
          className="flex overflow-x-auto gap-2.5 pb-2"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {dayun.map((d, i) => {
            const ganWuxing = d.gan_wuxing as string | undefined;
            const zhiWuxing = d.zhi_wuxing as string | undefined;
            const ganColor = ganWuxing ? WUXING_COLORS[ganWuxing] : "var(--text-primary)";
            const zhiColor = zhiWuxing ? WUXING_COLORS[zhiWuxing] : "var(--text-primary)";

            const startAge = Number(d.start_age || 0);
            const endAge = startAge + 9;
            const isCurrent = currentAge >= startAge && currentAge <= endAge && startAge > 0;

            return (
              <div
                key={i}
                className="flex-shrink-0 flex flex-col items-center gap-1 px-4 py-3.5 rounded-xl text-center min-w-[76px] transition-all duration-200 hover:-translate-y-0.5 relative"
                style={{
                  background: isCurrent ? "var(--accent-dim)" : "var(--bg-secondary)",
                  border: isCurrent ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                  boxShadow: isCurrent ? "0 0 12px rgba(201,169,110,0.15)" : "none",
                }}
              >
                {isCurrent && (
                  <span
                    className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] px-1.5 py-px rounded-full font-medium"
                    style={{ background: "var(--accent)", color: "var(--bg-primary)" }}
                  >
                    当前
                  </span>
                )}
                <span
                  className="text-lg font-bold leading-none"
                  style={{ color: ganColor }}
                >
                  {String(d.gan || "")}
                </span>
                <span
                  className="w-4 my-0.5"
                  style={{ height: "1px", background: "var(--border)" }}
                />
                <span
                  className="text-lg font-bold leading-none"
                  style={{ color: zhiColor }}
                >
                  {String(d.zhi || "")}
                </span>
                <div className="flex gap-0.5 mt-1.5">
                  {ganWuxing && (
                    <span
                      className="text-[9px] px-1 py-px rounded"
                      style={{ color: ganColor, background: WUXING_BG[ganWuxing] || "transparent" }}
                    >
                      {ganWuxing}
                    </span>
                  )}
                  {zhiWuxing && (
                    <span
                      className="text-[9px] px-1 py-px rounded"
                      style={{ color: zhiColor, background: WUXING_BG[zhiWuxing] || "transparent" }}
                    >
                      {zhiWuxing}
                    </span>
                  )}
                </div>
                <span
                  className="text-[10px] mt-1 tabular-nums"
                  style={{ color: "var(--text-muted)" }}
                >
                  {String(d.age_range || `${i + 1}运`)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
