"use client";

import { useState, useCallback } from "react";
import { Badge } from "@/components/ui";

import {
  WUXING_COLORS,
  WUXING_PILL_BG,
  WUXING_PILL_BORDER,
  WUXING_BG,
  GAN_WUXING,
  ZHI_WUXING,
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
  const dayMasterWx = GAN_WUXING[dayMaster] || "";
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
    <div className="animate-fade-in space-y-10">
      {/* 四柱卡片区 */}
      <div
        className="border-b pb-10"
        style={{ borderColor: "var(--color-border)" }}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between mb-6">
          <h2
            className="text-base font-bold"
            style={{ color: "var(--color-scholar-blue)", fontFamily: "var(--font-serif)" }}
          >
            四柱命盘
          </h2>
          <div className="flex items-center gap-3">
            {wangshuai?.verdict && (
              <span
                className="text-[11px] font-bold uppercase tracking-widest"
                style={{ color: "var(--color-text-muted)" }}
              >
                {wangshuai.verdict}
              </span>
            )}
            {dayMaster && (
              <span
                className="text-sm font-bold"
                style={{ color: dayMasterWx ? WUXING_COLORS[dayMasterWx] : "var(--color-text-primary)" }}
              >
                {dayMaster}日主
              </span>
            )}
          </div>
        </div>

        {/* 四柱纵向 grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-0 rounded-xl overflow-hidden border" style={{ borderColor: "var(--color-border)", background: "var(--surface)", boxShadow: "var(--shadow)" }}>
          {pillars.map((p, i) => {
            const isDayPillar = i === 2;
            const gan = p.gan || "";
            const zhi = p.zhi || "";
            const ganWx = p.wuxing_gan || GAN_WUXING[gan] || "";
            const zhiWx = p.wuxing_zhi || ZHI_WUXING[zhi] || "";
            return (
              <div
                key={i}
                className="flex flex-col items-center py-8 px-3 relative"
                style={{
                  borderRight: i < 3 ? "1px solid var(--color-border)" : "none",
                  background: isDayPillar ? "var(--color-bg-panel)" : "transparent",
                }}
              >
                {/* 柱位标签 */}
                <span
                  className="text-[10px] font-bold uppercase tracking-widest mb-4"
                  style={{ color: isDayPillar ? "var(--color-scholar-blue)" : "var(--color-text-muted)" }}
                >
                  {p.position ? `${p.position}柱` : positionLabels[i]}
                </span>

                {/* 十神标签 */}
                <span
                  className="text-[11px] mb-3"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {isDayPillar ? "日主" : p.shishen_gan || p.shishen || "—"}
                </span>

                {/* 天干 */}
                <div
                  className="px-4 py-2 mb-2 border"
                  style={{
                    background: ganWx ? WUXING_PILL_BG[ganWx] : "transparent",
                    borderColor: ganWx ? WUXING_PILL_BORDER[ganWx] : "var(--color-border)",
                  }}
                >
                  <span
                    className="text-3xl font-bold block text-center"
                    style={{ color: ganWx ? WUXING_COLORS[ganWx] : "var(--color-text-primary)" }}
                  >
                    {gan || "—"}
                  </span>
                </div>

                {/* 地支 */}
                <div
                  className="px-4 py-2 mb-4 border"
                  style={{
                    background: zhiWx ? WUXING_PILL_BG[zhiWx] : "transparent",
                    borderColor: zhiWx ? WUXING_PILL_BORDER[zhiWx] : "var(--color-border)",
                  }}
                >
                  <span
                    className="text-3xl font-bold block text-center"
                    style={{ color: zhiWx ? WUXING_COLORS[zhiWx] : "var(--color-text-primary)" }}
                  >
                    {zhi || "—"}
                  </span>
                </div>

                {/* 藏干 */}
                <div className="flex items-center gap-2 mb-2 min-h-[20px] flex-wrap justify-center">
                  {(p.canggan || []).map((cg, j) => {
                    const touchu = isGanTouchu(cg.gan);
                    return (
                      <span
                        key={j}
                        className="text-xs"
                        style={{ color: cg.wuxing ? WUXING_COLORS[cg.wuxing] : "var(--color-text-muted)" }}
                      >
                        {cg.gan}{touchu ? "透" : ""}
                      </span>
                    );
                  })}
                </div>

                {/* 纳音 */}
                {p.nayin && (
                  <span className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
                    {p.nayin}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 五行力量分布 */}
      <div
        className="rounded-xl p-6"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--color-border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <h3
          className="text-sm font-medium mb-6"
          style={{ color: "var(--color-text-muted)" }}
        >
          五行力量分布
        </h3>
        <div className="space-y-4">
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
                  className="flex-1 rounded-full overflow-hidden"
                  style={{ height: 12, background: "var(--bg-secondary)" }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(val, 100)}%`,
                      background: WUXING_COLORS[wx],
                      opacity: 0.8,
                    }}
                  />
                </div>
                <span
                  className="text-xs w-11 text-right tabular-nums font-medium"
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
          className="rounded-xl p-6"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--color-border)",
            boxShadow: "var(--shadow)",
          }}
        >
          <div className="flex items-center justify-between mb-5">
            <h3
              className="text-sm font-medium"
              style={{ color: "var(--text-muted)" }}
            >
              刑冲合害
            </h3>
            {relations.length > 3 && (
              <button
                className="text-xs px-2.5 py-1 rounded-md transition-colors"
                style={{ color: "var(--text-secondary)", background: "var(--bg-hover)" }}
                onClick={() => setExpandedRelations(!expandedRelations)}
              >
                {expandedRelations ? "收起" : `展开全部(${relations.length})`}
              </button>
            )}
          </div>
          <div className="space-y-3">
            {(expandedRelations ? relations : relations.slice(0, 3)).map((r, i) => {
              const rType = r.type || "关系";
              const wuxingVariant = rType === "合" ? "water" : rType === "冲" ? "fire" : rType === "刑" ? "earth" : rType === "害" ? "metal" : "muted";
              return (
                <div key={i} className="flex items-start gap-3">
                  <Badge variant={wuxingVariant as "water" | "fire" | "earth" | "metal" | "muted"}>
                    {rType}
                  </Badge>
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
          className="rounded-2xl p-7"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-medium mb-4"
            style={{ color: "var(--text-muted)" }}
          >
            方局/三合局
          </h3>
          <div className="flex items-center gap-3">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "rgba(251,191,36,0.12)", color: "var(--earth)" }}
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
          className="rounded-2xl p-7"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-medium mb-4"
            style={{ color: "var(--text-muted)" }}
          >
            破格条件
          </h3>
          <div className="space-y-3">
            {breakConditions.map((bc, i) => {
              const severityBg =
                bc.severity === "high"
                  ? "rgba(239,68,68,0.12)"
                  : bc.severity === "medium"
                    ? "rgba(245,158,11,0.12)"
                    : "rgba(92,92,112,0.12)";
              const severityColor =
                bc.severity === "high"
                  ? "var(--danger)"
                  : bc.severity === "medium"
                    ? "var(--warning)"
                    : "var(--text-muted)";
              return (
                <div key={i} className="flex items-start gap-3">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md shrink-0 font-medium"
                    style={{ background: severityBg, color: severityColor }}
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
