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

interface CangganItem { gan: string; wuxing?: string; shishen?: string; qi?: string; }
interface PillarDetail {
  position?: string; gan?: string; zhi?: string;
  wuxing_gan?: string; wuxing_zhi?: string;
  shishen_gan?: string; shishen_zhi?: string; shishen?: string;
  nayin?: string; changsheng?: string; canggan?: CangganItem[];
}
interface Props { result: Record<string, unknown>; }

export default function BaziChartCard({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const pillars = shishen?.pillars || [];

  const strength = result.strength as { wangshuai?: { verdict?: string } } | undefined;
  const wangshuai = strength?.wangshuai;

  const validation = result.validation as { day_master?: string } | undefined;
  const dayMaster = validation?.day_master || "";
  const dayMasterWx = GAN_WUXING[dayMaster] || "";

  const elements = result.elements as { percent?: Record<string, number> } | undefined;
  const percent = elements?.percent || {};
  const wuxingOrder = ["木", "火", "土", "金", "水"];

  const allTiangan = pillars.map((p) => p.gan || "");
  const isGanTouchu = useCallback((gan: string) => allTiangan.includes(gan), [allTiangan]);

  const relations = result.relations as Array<{ type?: string; elements?: string[]; description?: string }> | undefined;
  const [expandedRelations, setExpandedRelations] = useState(false);

  const pattern = result.pattern as {
    formation?: { has_formation?: boolean; type?: string; branches?: string[]; element?: string };
    break_conditions?: Array<{ type?: string; severity?: string; detail?: string }>;
  } | undefined;
  const formation = pattern?.formation;
  const breakConditions = pattern?.break_conditions;

  return (
    <div className="space-y-8">
      {/* ===== 四柱命盘 ===== */}
      <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
        {/* 头部 */}
        <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "18px 24px" }} className="flex items-center justify-between">
          <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
            四柱命盘 · 命局排盘
          </h2>
          <div className="flex items-center gap-3">
            {wangshuai?.verdict && (
              <span className="px-3 py-1 font-semibold" style={{ fontSize: 14, background: "var(--accent-dim)", color: "var(--color-scholar-blue)" }}>
                {wangshuai.verdict}
              </span>
            )}
            {dayMaster && (
              <span className="font-bold" style={{ fontSize: 16, color: dayMasterWx ? WUXING_COLORS[dayMasterWx] : "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
                日主：{dayMaster}
              </span>
            )}
          </div>
        </div>

        {/* 四柱 */}
        <div className="grid grid-cols-4" style={{ borderTop: "1px solid var(--color-border-subtle)", borderBottom: "1px solid var(--color-border-subtle)" }}>
          {pillars.map((p, i) => {
            const isDayPillar = i === 2;
            const gan = p.gan || "";
            const zhi = p.zhi || "";
            const ganWx = p.wuxing_gan || GAN_WUXING[gan] || "";
            const zhiWx = p.wuxing_zhi || ZHI_WUXING[zhi] || "";

            return (
              <div
                key={i} className="flex flex-col items-center py-8 px-4"
                style={{
                  background: isDayPillar ? "rgba(184,74,60,0.03)" : "transparent",
                  borderRight: i < 3 ? "1px solid var(--color-border-subtle)" : "none",
                }}
              >
                <span className="mb-4 font-semibold tracking-widest" style={{ fontSize: 12, color: isDayPillar ? "var(--color-cinnabar)" : "var(--color-text-faint)", letterSpacing: "0.15em" }}>
                  {p.position ? `${p.position}柱` : ["年柱","月柱","日柱","时柱"][i]}
                </span>

                <span className="mb-2" style={{ fontSize: 15, color: isDayPillar ? "var(--color-cinnabar)" : "var(--color-text-muted)" }}>
                  {isDayPillar ? "日主" : p.shishen_gan || p.shishen || "—"}
                </span>

                {/* 天干 */}
                <div
                  className="flex items-center justify-center mb-2"
                  style={{
                    width: 72, height: 72, background: ganWx ? WUXING_PILL_BG[ganWx] : "var(--bg-secondary)",
                    border: `2px solid ${ganWx ? WUXING_PILL_BORDER[ganWx] : "var(--color-border-strong)"}`,
                  }}
                >
                  <span style={{ fontSize: 36, fontWeight: 700, color: ganWx ? WUXING_COLORS[ganWx] : "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
                    {gan || "—"}
                  </span>
                </div>

                {/* 地支 */}
                <div
                  className="flex items-center justify-center mb-3"
                  style={{
                    width: 72, height: 72, background: zhiWx ? WUXING_PILL_BG[zhiWx] : "var(--bg-secondary)",
                    border: `2px solid ${zhiWx ? WUXING_PILL_BORDER[zhiWx] : "var(--color-border-strong)"}`,
                  }}
                >
                  <span style={{ fontSize: 36, fontWeight: 700, color: zhiWx ? WUXING_COLORS[zhiWx] : "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
                    {zhi || "—"}
                  </span>
                </div>

                {/* 藏干 */}
                <div className="flex items-center gap-2 mb-2 min-h-[22px] flex-wrap justify-center">
                  {(p.canggan || []).map((cg, j) => (
                    <span key={j} style={{ fontSize: 13, color: cg.wuxing ? WUXING_COLORS[cg.wuxing] : "var(--color-text-muted)", fontFamily: "var(--font-serif)" }}>
                      {cg.gan}{isGanTouchu(cg.gan) ? "透" : ""}
                    </span>
                  ))}
                </div>

                {p.nayin && (
                  <span style={{ fontSize: 12, color: "var(--color-text-faint)", fontStyle: "italic", fontFamily: "var(--font-serif)" }}>{p.nayin}</span>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ===== 五行力量 + 刑冲合害 双栏 ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 五行 */}
        <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }}>
            <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>五行力量分布</h3>
          </div>
          <div className="p-7 space-y-5">
            {wuxingOrder.map((wx) => {
              const val = percent[wx] || 0;
              return (
                <div key={wx} className="flex items-center gap-4">
                  <span className="w-8 text-center font-bold shrink-0" style={{ fontSize: 15, color: WUXING_COLORS[wx], background: WUXING_BG[wx], fontFamily: "var(--font-serif)" }}>
                    {wx}
                  </span>
                  <div className="flex-1 h-3 overflow-hidden" style={{ background: "var(--bg-secondary)" }}>
                    <div className="h-full" style={{ width: `${Math.min(val,100)}%`, transition:"width 0.7s", background: WUXING_COLORS[wx] }} />
                  </div>
                  <span className="tabular-nums font-semibold w-10 text-right" style={{ fontSize: 14, color: "var(--color-text-muted)" }}>{val.toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* 刑冲合害 */}
        {relations && relations.length > 0 && (
          <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }} className="flex items-center justify-between">
              <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>刑冲合害</h3>
              {relations.length > 3 && (
                <button onClick={() => setExpandedRelations(!expandedRelations)} className="px-3 py-1 font-medium" style={{ fontSize: 13, color: "var(--color-text-secondary)", background: "var(--bg-secondary)" }}>
                  {expandedRelations ? "收起" : `全部(${relations.length})`}
                </button>
              )}
            </div>
            <div className="p-7 space-y-3.5">
              {(expandedRelations ? relations : relations.slice(0, 3)).map((r, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Badge variant={(r.type === "合" ? "water" : r.type === "冲" ? "fire" : r.type === "刑" ? "earth" : "metal")}>
                    {r.type}
                  </Badge>
                  <span style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>{r.description || (r.elements||[]).join(" ")}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* 方局/三合局 */}
      {formation && formation.has_formation && (
        <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }}>
            <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>方局 / 三合局</h3>
          </div>
          <div className="p-7 flex items-center gap-4">
            <span className="px-4 py-1.5 font-bold" style={{ fontSize: 14, background: "rgba(161,127,64,0.08)", color: "var(--color-gold)", fontFamily: "var(--font-serif)" }}>
              {formation.type || "会局"}
            </span>
            <span className="font-bold" style={{ fontSize: 20, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
              {(formation.branches||[]).join(" ")}
            </span>
            {formation.element && (
              <span className="px-3 py-1 font-semibold" style={{ fontSize: 14, color: WUXING_COLORS[formation.element], background: WUXING_BG[formation.element] }}>
                {formation.element}
              </span>
            )}
          </div>
        </section>
      )}

      {/* 破格条件 */}
      {breakConditions && breakConditions.length > 0 && (
        <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }}>
            <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>破格条件</h3>
          </div>
          <div className="p-7 space-y-4">
            {breakConditions.map((bc, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="px-2.5 py-1 font-bold shrink-0" style={{ fontSize: 13, background: bc.severity === "high" ? "rgba(196,60,44,0.08)" : bc.severity === "medium" ? "rgba(184,146,63,0.08)" : "rgba(168,168,148,0.06)", color: bc.severity === "high" ? "var(--danger)" : bc.severity === "medium" ? "var(--warning)" : "var(--color-text-muted)" }}>
                  {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                </span>
                <div>
                  <div className="font-semibold mb-0.5" style={{ fontSize: 15, color: "var(--color-text-primary)" }}>{bc.type}</div>
                  {bc.detail && <div style={{ fontSize: 13, color: "var(--color-text-muted)" }}>{bc.detail}</div>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
