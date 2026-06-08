"use client";

import { useState } from "react";

interface Dimension {
  name: string;
  name_en: string;
  score: number;
  max: number;
  detail: string;
}

export interface ChartQualityData {
  total: number;
  total_max: number;
  level: string;
  level_en: string;
  tier: string;
  dimensions: Dimension[];
}

function scoreColor(score: number, max: number): string {
  const ratio = score / max;
  if (ratio >= 0.8) return "var(--wx-wood)";
  if (ratio >= 0.5) return "var(--scholar-blue)";
  if (ratio >= 0.3) return "#e6a817";
  return "var(--danger)";
}

function totalColor(total: number): string {
  if (total >= 80) return "var(--wx-wood)";
  if (total >= 60) return "var(--scholar-blue)";
  if (total >= 40) return "#e6a817";
  return "var(--danger)";
}

interface Props { data: ChartQualityData }

export default function ChartQuality({ data }: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <section style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-sm)", borderRadius: 12, overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "16px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-4)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
          命局层次 <span style={{ fontSize: 11, fontWeight: 400, opacity: 0.6 }}>(Chart Quality)</span>
        </span>
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{
          background: `${totalColor(data.total)}15`,
          color: totalColor(data.total),
          border: `1px solid ${totalColor(data.total)}30`,
        }}>
          {data.level}
        </span>
      </div>

      {/* Level + Scores */}
      <div style={{ padding: "0 28px 20px" }}>
        <div className="flex items-baseline gap-3 mb-5">
          <h3 style={{ fontSize: 22, fontWeight: 700, color: totalColor(data.total), fontFamily: "var(--font-display)" }}>
            {data.level_en}
          </h3>
          <span style={{ fontSize: 13, color: "var(--text-4)" }}>{data.level}</span>
        </div>

        {/* Dimension Bars */}
        <div className="space-y-3.5">
          {data.dimensions.map((d, i) => (
            <div key={i}>
              <div className="flex items-center justify-between mb-1.5">
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-2)" }}>{d.name}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink)", fontFamily: "ui-monospace" }}>
                  {d.score}/{d.max}
                </span>
              </div>
              <div style={{ width: "100%", height: 6, borderRadius: 3, background: "var(--surface-2)", overflow: "hidden" }}>
                <div style={{
                  width: `${(d.score / d.max) * 100}%`,
                  height: "100%",
                  borderRadius: 3,
                  background: scoreColor(d.score, d.max),
                  transition: "width 0.6s cubic-bezier(0.22, 1, 0.36, 1)",
                  transitionDelay: `${i * 0.08}s`,
                }} />
              </div>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="flex items-center justify-between mt-5 pt-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)" }}>总分</span>
          <span style={{ fontSize: 18, fontWeight: 800, color: totalColor(data.total), fontFamily: "var(--font-display)" }}>
            {data.total}/{data.total_max}
          </span>
        </div>

        {/* Toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 mt-4 transition-colors duration-150 hover:text-[var(--scholar-blue)]"
          style={{ fontSize: 13, color: "var(--text-4)", background: "none", border: "none", cursor: "pointer", padding: 0 }}
        >
          {expanded ? '收起详情 ▲' : '查看详情 ▼'}
        </button>

        {/* Details */}
        <div style={{
          maxHeight: expanded ? 600 : 0,
          opacity: expanded ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.35s ease, opacity 0.25s ease",
        }}>
          <div className="mt-5 space-y-4" style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 16 }}>
            {data.dimensions.map((d, i) => (
              <div key={i}>
                <h4 style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)", marginBottom: 4 }}>{d.name}</h4>
                <p style={{ fontSize: 13, color: "var(--text-3)", lineHeight: 1.6 }}>{d.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
