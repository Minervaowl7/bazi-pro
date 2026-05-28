"use client";

import { WUXING_COLORS } from "@/lib/constants";

interface Props {
  result: Record<string, unknown>;
}

export default function DayunTimeline({ result }: Props) {
  const dayun = (result.dayun as Array<Record<string, unknown>> | undefined)
    || (result.paipan_dayun as Array<Record<string, unknown>> | undefined);

  if (!dayun || dayun.length === 0) return null;

  return (
    <div
      className="rounded-2xl p-6 animate-fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <h3
        className="text-base font-semibold mb-5"
        style={{ color: "var(--accent)" }}
      >
        大运时间线
      </h3>
      <div
        className="flex overflow-x-auto gap-3 pb-2"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {dayun.map((d, i) => {
          const ganWuxing = d.gan_wuxing as string | undefined;
          const zhiWuxing = d.zhi_wuxing as string | undefined;
          const ganColor = ganWuxing ? WUXING_COLORS[ganWuxing] : "var(--text-primary)";
          const zhiColor = zhiWuxing ? WUXING_COLORS[zhiWuxing] : "var(--text-primary)";

          return (
            <div
              key={i}
              className="flex-shrink-0 px-4 py-3 rounded-xl text-center min-w-[80px] transition-all duration-200 hover:-translate-y-0.5"
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
              }}
            >
              <div
                className="text-base font-bold tracking-wide"
                style={{ color: ganColor }}
              >
                {String(d.gan || "")}
              </div>
              <div
                className="text-base font-bold tracking-wide"
                style={{ color: zhiColor }}
              >
                {String(d.zhi || "")}
              </div>
              <div
                className="text-xs mt-1.5"
                style={{ color: "var(--text-muted)" }}
              >
                {String(d.age_range || `${i + 1}运`)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
