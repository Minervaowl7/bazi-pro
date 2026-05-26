"use client";

import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Pillar {
  position: string;
  gan: string;
  zhi: string;
  wuxing_gan: string;
  wuxing_zhi: string;
  shishen: string;
  canggan: Array<{ gan: string; qi: string; wuxing: string; shishen: string }>;
}

interface BaziChartCardProps {
  result: Record<string, unknown>;
}

const WUXING_COLORS: Record<string, string> = {
  木: "#22c55e",
  火: "#ef4444",
  土: "#eab308",
  金: "#f59e0b",
  水: "#3b82f6",
};

export default function BaziChartCard({ result }: BaziChartCardProps) {
  const pillars: Pillar[] = (result.shishen as { pillars?: Pillar[] })?.pillars || [];
  const elements = result.elements as { percent?: Record<string, number> } | undefined;
  const strength = result.strength as {
    wangshuai?: { verdict?: string };
    day_master?: string;
  } | undefined;
  const pattern = result.pattern as { pattern?: string; confidence?: number } | undefined;
  const yongshen = result.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[] } | undefined;

  const elementPercent = elements?.percent || { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };

  const radarOption = {
    backgroundColor: "transparent",
    radar: {
      indicator: Object.keys(elementPercent).map((name) => ({ name, max: 60 })),
      shape: "polygon",
      axisName: { color: "#9ca3af", fontSize: 12 },
      splitArea: { areaStyle: { color: ["rgba(42,48,64,0.3)", "rgba(42,48,64,0.5)"] } },
      splitLine: { lineStyle: { color: "#2a3040" } },
      axisLine: { lineStyle: { color: "#2a3040" } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: Object.values(elementPercent).map((v) => Math.round(v)),
            name: "五行力量",
            areaStyle: { color: "rgba(196,168,108,0.2)" },
            lineStyle: { color: "#c4a86c", width: 2 },
            itemStyle: { color: "#c4a86c" },
          },
        ],
      },
    ],
  };

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium">
          命盘 · <span className="text-[var(--accent)]">{strength?.day_master || ""}木日主</span>
        </h2>
        <div className="flex gap-3 text-xs text-[var(--text-muted)]">
          <span>旺衰: <span className="text-[var(--text-primary)]">{strength?.wangshuai?.verdict || "—"}</span></span>
          <span>格局: <span className="text-[var(--text-primary)]">{pattern?.pattern || "—"}</span></span>
        </div>
      </div>

      {/* Four Pillars Grid */}
      <div className="grid grid-cols-4 gap-2 mb-5">
        {["年柱", "月柱", "日柱", "时柱"].map((label, i) => {
          const p = pillars[i];
          if (!p) {
            return (
              <div key={label} className="text-center p-3 bg-[var(--bg-secondary)] rounded-lg">
                <div className="text-xs text-[var(--text-muted)] mb-1">{label}</div>
                <div className="text-lg text-[var(--text-muted)]">—</div>
              </div>
            );
          }
          return (
            <div key={label} className="text-center p-3 bg-[var(--bg-secondary)] rounded-lg">
              <div className="text-xs text-[var(--text-muted)] mb-1">{label}</div>
              <div
                className="text-xl font-medium mb-0.5"
                style={{ color: WUXING_COLORS[p.wuxing_gan] || "inherit" }}
              >
                {p.gan}
              </div>
              <div
                className="text-xl font-medium mb-1"
                style={{ color: WUXING_COLORS[p.wuxing_zhi] || "inherit" }}
              >
                {p.zhi}
              </div>
              <div className="text-xs text-[var(--text-secondary)]">{p.shishen}</div>
              <div className="text-xs text-[var(--text-muted)] mt-1">
                {p.canggan.map((c) => c.gan).join("")}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary row */}
      <div className="flex flex-wrap gap-4 text-sm mb-5 px-1">
        <span>
          用神: <span className="text-[var(--accent)] font-medium">{yongshen?.yongshen || "—"}</span>
        </span>
        {yongshen?.xishen && yongshen.xishen.length > 0 && (
          <span>
            喜神: <span className="text-[var(--success)]">{yongshen.xishen.join(" ")}</span>
          </span>
        )}
        {yongshen?.jishen && yongshen.jishen.length > 0 && (
          <span>
            忌神: <span className="text-[var(--danger)]">{yongshen.jishen.join(" ")}</span>
          </span>
        )}
      </div>

      {/* Element Radar */}
      <div className="flex justify-center">
        <ReactECharts option={radarOption} style={{ width: 280, height: 220 }} />
      </div>
    </div>
  );
}