"use client";

import { WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";

interface SummaryPillsProps {
  wangshuaiVerdict?: string;
  patternName?: string;
  yongshen?: string;
  xishen?: string[];
  jishen?: string[];
  hasTiaohou?: boolean;
  tiaohouGan?: string[];
}

export default function SummaryPills({ wangshuaiVerdict, patternName, yongshen, xishen, jishen, hasTiaohou, tiaohouGan }: SummaryPillsProps) {
  const pills = [
    { label: "旺衰", value: wangshuaiVerdict || "—" },
    { label: "格局", value: patternName || "—" },
    { label: "用神", value: yongshen || "—", bg: "var(--wx-wood-bg)" },
    { label: "喜神", value: (xishen || []).join(" ") || "—", bg: "var(--wx-water-bg)" },
    { label: "忌神", value: (jishen || []).join(" ") || "—", bg: "var(--wx-fire-bg)" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 mb-6 sm:mb-8">
      {pills.map((item) => (
        <div data-pill key={item.label} className="card text-center relative overflow-hidden p-3 sm:p-4 px-2 sm:px-3" style={{ background: item.bg || "var(--surface)" }}>
          <div style={{ position: "absolute", top: 0, left: "20%", right: "20%", height: 1, background: "linear-gradient(90deg,transparent,var(--gold),transparent)", opacity: 0.4 }} />
          <div className="mb-1 sm:mb-1.5 text-[10px] sm:text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--text-3)" }}>{item.label}</div>
          <div className="text-base sm:text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            {item.value.split("").map((ch, i) => {
              const wx = GAN_WUXING[ch] || ZHI_WUXING[ch] || (["金", "木", "水", "火", "土"].includes(ch) ? ch : "");
              const color = wx ? WUXING_COLORS[wx] : "var(--ink)";
              return <span key={i} style={{ color, marginRight: 1 }}>{ch}</span>;
            })}
          </div>
        </div>
      ))}
      {hasTiaohou && (
        <div data-pill className="card text-center relative overflow-hidden p-3 sm:p-4 px-2 sm:px-3" style={{ background: "rgba(197,165,90,0.04)" }}>
          <div className="absolute top-0 left-[20%] right-[20%] h-px opacity-40" style={{ background: "linear-gradient(90deg,transparent,var(--gold),transparent)" }} />
          <div className="mb-1 sm:mb-1.5 text-[10px] sm:text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--gold)" }}>调候</div>
          <div className="text-base sm:text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            {(tiaohouGan || []).map((ch, i) => {
              const wx = GAN_WUXING[ch] || "";
              const color = wx ? WUXING_COLORS[wx] : "var(--gold)";
              return <span key={i} style={{ color, marginRight: 2 }}>{ch}</span>;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
