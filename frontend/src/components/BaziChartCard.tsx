"use client";

import { useState, useCallback } from "react";

import {
  WUXING_COLORS,
  WUXING_BG,
  RELATION_COLORS,
} from "@/lib/constants";

interface CangganItem {
  gan: string;
  wuxing?: string;
  shishen?: string;
  qi?: string;
}

interface PillarDetail {
  position?: string;
  gan?: string;
  zhi?: string;
  wuxing_gan?: string;
  wuxing_zhi?: string;
  shishen_gan?: string;
  shishen_zhi?: string;
  shishen?: string;
  nayin?: string;
  changsheng?: string;
  canggan?: CangganItem[];
}

interface Props {
  result: Record<string, unknown>;
}

export default function BaziChartCard({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const pillars = shishen?.pillars || [];

  const strength = result.strength as {
    wangshuai?: { verdict?: string; is_weak?: boolean; is_strong?: boolean };
  } | undefined;
  const wangshuai = strength?.wangshuai;

  const validation = result.validation as {
    day_master?: string;
    bazi?: string;
    gender?: string;
  } | undefined;
  const dayMaster = validation?.day_master || "";
  const elements = result.elements as { percent?: Record<string, number> } | undefined;
  const relations = result.relations as Array<{
    type?: string;
    elements?: string[];
    description?: string;
  }> | undefined;

  const pattern = result.pattern as {
    pattern?: string;
    confidence?: number;
    formation?: {
      has_formation?: boolean;
      type?: string;
      branches?: string[];
      element?: string;
    };
    break_conditions?: Array<{
      type?: string;
      severity?: string;
      detail?: string;
    }>;
  } | undefined;

  const formation = pattern?.formation;
  const breakConditions = pattern?.break_conditions;

  const percent = elements?.percent || {};
  const wuxingOrder = ["木", "火", "土", "金", "水"];

  const allTiangan = pillars.map((p) => p.gan || "");

  const isGanTouchu = useCallback(
    (gan: string) => allTiangan.includes(gan),
    [allTiangan]
  );

  const [expandedRelations, setExpandedRelations] = useState(false);

  const positionLabels = ["年柱", "月柱", "日柱", "时柱"];

  return (
    <div className="animate-fade-in space-y-6">
      {/* 四柱卡片区 */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)" }}
        >
          <h2
            className="text-base font-semibold tracking-wide"
            style={{ color: "var(--accent)" }}
          >
            四柱命盘
          </h2>
          <div className="flex items-center gap-3">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "var(--accent-dim)", color: "var(--accent)", border: "1px solid var(--border-accent)" }}
            >
              {wangshuai?.verdict || "—"}
            </span>
            <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              {dayMaster}日主
            </span>
          </div>
        </div>

        {/* 四柱纵向卡片 grid */}
        <div className="grid grid-cols-4 gap-0" style={{ borderBottom: "1px solid var(--border)" }}>
          {pillars.map((p, i) => {
            const isDayPillar = i === 2;
            const gan = p.gan || "";
            const zhi = p.zhi || "";
            return (
              <div
                key={i}
                className="flex flex-col items-center py-5 px-2 relative"
                style={{
                  borderRight: i < 3 ? "1px solid var(--border-subtle)" : "none",
                  background: isDayPillar ? "var(--accent-glow)" : "transparent",
                }}
              >
                {/* 日主 badge */}
                {isDayPillar && (
                  <span
                    className="absolute top-2 right-2 text-[10px] px-1.5 py-0.5 rounded font-bold"
                    style={{ background: "var(--day-master-bg)", color: "var(--day-master-text)" }}
                  >
                    日主
                  </span>
                )}

                {/* 十神 */}
                <span className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                  {isDayPillar ? "日主" : p.shishen_gan || p.shishen || "—"}
                </span>

                {/* 天干 */}
                <span
                  className="text-2xl font-bold px-3 py-1.5 rounded-xl mb-1"
                  style={{
                    color: p.wuxing_gan ? WUXING_COLORS[p.wuxing_gan] : "inherit",
                    background: p.wuxing_gan ? WUXING_BG[p.wuxing_gan] : "transparent",
                  }}
                >
                  {gan || "—"}
                </span>

                {/* 分割线 */}
                <div
                  className="w-8 my-2"
                  style={{ borderTop: "1px dashed var(--border)" }}
                />

                {/* 地支 */}
                <span
                  className="text-2xl font-bold px-3 py-1.5 rounded-xl mb-2"
                  style={{
                    color: p.wuxing_zhi ? WUXING_COLORS[p.wuxing_zhi] : "inherit",
                    background: p.wuxing_zhi ? WUXING_BG[p.wuxing_zhi] : "transparent",
                  }}
                >
                  {zhi || "—"}
                </span>

                {/* 藏干 */}
                <div className="flex flex-col items-center gap-0.5 mb-2 min-h-[40px]">
                  {(p.canggan || []).map((cg, j) => {
                    const touchu = isGanTouchu(cg.gan);
                    return (
                      <span
                        key={j}
                        className="text-xs inline-flex items-center gap-0.5"
                        style={{ color: cg.wuxing ? WUXING_COLORS[cg.wuxing] : "inherit" }}
                      >
                        {cg.gan}
                        <span
                          className="text-[9px] px-1 rounded"
                          style={{
                            background: touchu ? "rgba(34,197,94,0.2)" : "rgba(128,128,128,0.12)",
                            color: touchu ? "#22c55e" : "var(--text-muted)",
                          }}
                        >
                          {touchu ? "透" : cg.qi === "本气" ? "本" : cg.qi === "中气" ? "中" : "余"}
                        </span>
                      </span>
                    );
                  })}
                </div>

                {/* 纳音 */}
                {p.nayin && (
                  <span className="text-[11px] mb-1" style={{ color: "var(--text-muted)" }}>
                    {p.nayin}
                  </span>
                )}

                {/* 长生 */}
                {p.changsheng && (
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
                  >
                    {p.changsheng}
                  </span>
                )}

                {/* 柱位标签 */}
                <span
                  className="text-[11px] mt-2 font-medium"
                  style={{ color: isDayPillar ? "var(--accent)" : "var(--text-muted)" }}
                >
                  {p.position ? `${p.position}柱` : positionLabels[i]}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 五行力量分布 */}
      <div
        className="rounded-2xl p-6"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <h3
          className="text-sm font-semibold mb-5"
          style={{ color: "var(--text-secondary)" }}
        >
          五行力量分布
        </h3>
        <div className="space-y-3">
          {wuxingOrder.map((wx) => {
            const val = percent[wx] || 0;
            return (
              <div key={wx} className="flex items-center gap-3">
                <span
                  className="text-xs font-medium w-7 text-center rounded-md px-1.5 py-0.5"
                  style={{ color: WUXING_COLORS[wx], background: WUXING_BG[wx] }}
                >
                  {wx}
                </span>
                <div
                  className="flex-1 rounded-full"
                  style={{ height: 10, background: "var(--bg-secondary)" }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(val, 100)}%`,
                      background: WUXING_COLORS[wx],
                      opacity: 0.85,
                    }}
                  />
                </div>
                <span
                  className="text-xs w-11 text-right tabular-nums"
                  style={{ color: "var(--text-muted)" }}
                >
                  {val.toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 刑冲合害 */}
      {relations && relations.length > 0 && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-secondary)" }}
            >
              刑冲合害
            </h3>
            {relations.length > 3 && (
              <button
                className="text-xs px-2 py-0.5 rounded"
                style={{ color: "var(--accent)", background: "var(--accent-dim)" }}
                onClick={() => setExpandedRelations(!expandedRelations)}
              >
                {expandedRelations ? "收起" : `展开全部(${relations.length})`}
              </button>
            )}
          </div>
          <div className="space-y-2.5">
            {(expandedRelations ? relations : relations.slice(0, 3)).map((r, i) => {
              const rColor = RELATION_COLORS[r.type || ""] || "var(--accent)";
              return (
                <div key={i} className="flex items-start gap-2.5">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md shrink-0"
                    style={{
                      background: `${rColor}20`,
                      color: rColor,
                    }}
                  >
                    {r.type || "关系"}
                  </span>
                  <span
                    className="text-sm leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {r.description || (r.elements || []).join(" ")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 方局/三合局 */}
      {formation && formation.has_formation && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            方局/三合局
          </h3>
          <div className="flex items-center gap-3">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "rgba(251,191,36,0.15)", color: "var(--warning)" }}
            >
              {formation.type || "会局"}
            </span>
            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              {(formation.branches || []).join(" ")}
            </span>
            {formation.element && (
              <span
                className="text-xs px-2 py-0.5 rounded-md"
                style={{
                  color: WUXING_COLORS[formation.element],
                  background: WUXING_BG[formation.element],
                }}
              >
                {formation.element}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 破格条件 */}
      {breakConditions && breakConditions.length > 0 && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            破格条件
          </h3>
          <div className="space-y-2.5">
            {breakConditions.map((bc, i) => {
              const severityColor =
                bc.severity === "high"
                  ? "var(--danger)"
                  : bc.severity === "medium"
                    ? "var(--warning)"
                    : "var(--text-muted)";
              return (
                <div key={i} className="flex items-start gap-2.5">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md shrink-0 font-medium"
                    style={{ background: `${severityColor}20`, color: severityColor }}
                  >
                    {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                  </span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {bc.type}
                    </span>
                    {bc.detail && (
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {bc.detail}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
