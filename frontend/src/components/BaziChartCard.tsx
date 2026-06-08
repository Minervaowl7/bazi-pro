"use client";

import { useState, useCallback, useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";

import {
  WUXING_COLORS,
  WUXING_GRADIENT_BG,
  WUXING_BAR_GRADIENT,
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
  const containerRef = useRef<HTMLDivElement>(null);
  const dayunRef = useRef<HTMLSpanElement>(null);
  const pillarRefs = useRef<(HTMLDivElement | null)[]>([]);

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

  useGSAP(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      gsap.set("[data-chart-header]", { autoAlpha: 1 });
      pillarRefs.current.forEach((el) => { if (el) gsap.set(el, { autoAlpha: 1 }); });
      gsap.set("[data-nayin]", { autoAlpha: 1 });
      if (dayunRef.current) gsap.set(dayunRef.current, { autoAlpha: 1 });
      return;
    }

    const tl = gsap.timeline({ delay: 0.15 });

    tl.from("[data-chart-header]", {
      y: -20, autoAlpha: 0, duration: 0.5, ease: "power2.out",
    });

    tl.from(pillarRefs.current, {
      y: 40, autoAlpha: 0, scale: 0.95, stagger: 0.12, duration: 0.7, ease: "back.out(1.4)",
    }, "-=0.2");

    tl.from("[data-nayin]", {
      autoAlpha: 0, y: 10, stagger: 0.08, duration: 0.4, ease: "power2.out",
    }, "-=0.3");

    if (dayunRef.current) {
      tl.from(dayunRef.current, {
        scale: 2.5, autoAlpha: 0, rotation: -15, duration: 0.5, ease: "back.out(2)",
      }, "-=0.2");
    }
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="space-y-8">
      {/* ===== 四柱命盘 ===== */}
      <section className="card">
        {/* 头部 */}
        <div data-chart-header className="relative border-b border-[var(--border)] px-7 py-[18px]">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold" style={{ fontFamily: "var(--font-display)" }}>
              四柱命盘
            </h2>
            <div className="flex items-center gap-3">
              {dayMaster && (
                <span className="font-bold" style={{ fontSize: 16, color: dayMasterWx ? WUXING_COLORS[dayMasterWx] : "var(--ink)", fontFamily: "var(--font-display)" }}>
                  日主：{dayMaster}
                </span>
              )}
              {wangshuai?.verdict && (
                <span
                  ref={dayunRef}
                  className="inline-flex items-center justify-center px-3 py-0.5 font-semibold"
                  style={{
                    fontSize: 12,
                    background: "var(--cinnabar-light)",
                    color: "var(--cinnabar)",
                    borderRadius: 9999,
                    border: "1px solid rgba(201,100,66,0.2)",
                    letterSpacing: "0.04em",
                    visibility: "hidden",
                  }}
                >
                  {wangshuai.verdict}
                </span>
              )}
            </div>
          </div>
          {/* 标题下方金色装饰线 */}
          <div style={{ position: "absolute", bottom: 0, left: 28, width: 40, height: 1, background: "linear-gradient(90deg, var(--gold), transparent)" }} />
        </div>

        {/* 四柱 */}
        <div className="grid grid-cols-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          {pillars.map((p, i) => {
            const isDayPillar = i === 2;
            const gan = p.gan || "";
            const zhi = p.zhi || "";
            const ganWx = p.wuxing_gan || GAN_WUXING[gan] || "";
            const zhiWx = p.wuxing_zhi || ZHI_WUXING[zhi] || "";

            return (
              <div
                key={i}
                ref={(el) => { pillarRefs.current[i] = el; }}
                className="flex flex-col items-center py-8 px-4"
                style={{
                  borderRight: i < 3 ? "1px solid var(--border-subtle)" : "none",
                  visibility: "hidden",
                }}
              >
                <span className="mb-4 font-semibold" style={{ fontSize: 11, color: isDayPillar ? "var(--cinnabar)" : "var(--text-4)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  {p.position ? `${p.position}柱` : ["年柱","月柱","日柱","时柱"][i]}
                </span>

                <span className="mb-2" style={{ fontSize: 15, color: isDayPillar ? "var(--cinnabar)" : "var(--text-3)" }}>
                  {isDayPillar ? "日主" : p.shishen_gan || p.shishen || "—"}
                </span>

                {/* 天干 */}
                <div
                  className="flex items-center justify-center mb-2 transition-transform duration-200"
                  style={{
                    width: 68, height: 68,
                    background: ganWx ? WUXING_GRADIENT_BG[ganWx] : "var(--surface-2)",
                    border: `1.5px solid ${ganWx ? `rgba(${ganWx === "木" ? "58,125,92" : ganWx === "火" ? "201,100,66" : ganWx === "土" ? "139,106,58" : ganWx === "金" ? "197,165,90" : "46,92,138"},0.18)` : "var(--border-strong)"}`,
                    borderRadius: 10,
                    boxShadow: isDayPillar ? "0 0 0 2px rgba(201,100,66,0.1), 0 2px 8px rgba(201,100,66,0.1)" : "none",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.06)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
                >
                  <span style={{ fontSize: 30, fontWeight: 700, color: ganWx ? WUXING_COLORS[ganWx] : "var(--ink)", fontFamily: "var(--font-display)" }}>
                    {gan || "—"}
                  </span>
                </div>

                {/* 渐变分隔线 */}
                <div style={{ width: 24, height: 1, background: "linear-gradient(90deg, transparent, var(--border-strong), transparent)", margin: "6px 0" }} />

                {/* 地支 */}
                <div
                  className="flex items-center justify-center mb-3 transition-transform duration-200"
                  style={{
                    width: 68, height: 68,
                    background: zhiWx ? WUXING_GRADIENT_BG[zhiWx] : "var(--surface-2)",
                    border: `1.5px solid ${zhiWx ? `rgba(${zhiWx === "木" ? "58,125,92" : zhiWx === "火" ? "201,100,66" : zhiWx === "土" ? "139,106,58" : zhiWx === "金" ? "197,165,90" : "46,92,138"},0.18)` : "var(--border-strong)"}`,
                    borderRadius: 10,
                    boxShadow: isDayPillar ? "0 0 0 2px rgba(201,100,66,0.1), 0 2px 8px rgba(201,100,66,0.1)" : "none",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.06)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
                >
                  <span style={{ fontSize: 30, fontWeight: 700, color: zhiWx ? WUXING_COLORS[zhiWx] : "var(--ink)", fontFamily: "var(--font-display)" }}>
                    {zhi || "—"}
                  </span>
                </div>

                {/* 藏干 */}
                <div className="flex items-center gap-1.5 mb-2 min-h-[20px] flex-wrap justify-center">
                  {(p.canggan || []).map((cg, j) => {
                    const cgWx = cg.wuxing || "";
                    const isTouchu = isGanTouchu(cg.gan);
                    return (
                      <span key={j} className="px-1.5 py-0.5 rounded" style={{
                        fontSize: 11,
                        fontWeight: 500,
                        color: cgWx ? WUXING_COLORS[cgWx] : "var(--text-3)",
                        background: cgWx ? WUXING_BG[cgWx] : "transparent",
                        fontFamily: "var(--font-display)",
                      }}>
                        {isTouchu ? "透" : "藏"}{cg.gan}
                      </span>
                    );
                  })}
                </div>

                {p.nayin && (
                  <span data-nayin style={{ fontSize: 10, color: "var(--text-4)", fontStyle: "italic", fontFamily: "var(--font-display)", letterSpacing: "0.03em", visibility: "hidden" }}>{p.nayin}</span>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ===== 五行力量 + 刑冲合害 双栏 ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 五行 */}
        <section className="card">
          <div className="border-b border-[var(--border)] px-6 py-4">
            <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>五行力量分布</h3>
          </div>
          <div className="p-7 space-y-5">
            {wuxingOrder.map((wx) => {
              const val = percent[wx] || 0;
              return (
                <div key={wx} className="flex items-center gap-4">
                  <span className="w-8 text-center font-bold shrink-0" style={{ fontSize: 14, color: WUXING_COLORS[wx], fontFamily: "var(--font-display)" }}>
                    {wx}
                  </span>
                  <div className="flex-1 overflow-hidden" style={{ height: 6, borderRadius: 3, background: "var(--surface-2)" }}>
                    <div className="h-full" style={{ width: `${Math.min(val,100)}%`, transition:"width 0.7s", borderRadius: 3, background: WUXING_BAR_GRADIENT[wx] || WUXING_COLORS[wx] }} />
                  </div>
                  <span className="tabular-nums font-semibold w-10 text-right" style={{ fontSize: 12, color: "var(--text-3)" }}>{val.toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* 刑冲合害 */}
        {relations && relations.length > 0 && (
          <section className="card">
            <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
              <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>刑冲合害</h3>
              {relations.length > 3 && (
                <button onClick={() => setExpandedRelations(!expandedRelations)} className="px-3 py-1 font-medium" style={{ fontSize: 13, color: "var(--text-2)", background: "var(--surface-2)", borderRadius: 6 }}>
                  {expandedRelations ? "收起" : `全部(${relations.length})`}
                </button>
              )}
            </div>
            <div className="p-7 space-y-3.5">
              {(expandedRelations ? relations : relations.slice(0, 3)).map((r, i) => {
                const typeColor = r.type === "合" ? "var(--wx-wood)" : r.type === "冲" ? "var(--wx-fire)" : r.type === "刑" ? "var(--wx-metal)" : "var(--wx-earth)";
                return (
                  <div key={i} className="flex items-start gap-3">
                    <span className="shrink-0 px-2.5 py-0.5 font-semibold" style={{
                      fontSize: 12,
                      color: typeColor,
                      background: `${typeColor}11`,
                      border: `1px solid ${typeColor}22`,
                      borderRadius: 9999,
                    }}>
                      {r.type}
                    </span>
                    <span style={{ fontSize: 14, color: "var(--text-2)" }}>{r.description || (r.elements||[]).join(" ")}</span>
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </div>

      {/* 方局/三合局 */}
      {formation && formation.has_formation && (
        <section className="card">
          <div className="border-b border-[var(--border)] px-6 py-4">
            <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>方局 / 三合局</h3>
          </div>
          <div className="p-7 flex items-center gap-4">
            <span className="px-4 py-1.5 font-bold" style={{ fontSize: 14, background: "rgba(161,127,64,0.08)", color: "var(--gold)", borderRadius: 6, fontFamily: "var(--font-display)" }}>
              {formation.type || "会局"}
            </span>
            <span className="font-bold" style={{ fontSize: 20, color: "var(--ink)", fontFamily: "var(--font-display)" }}>
              {(formation.branches||[]).join(" ")}
            </span>
            {formation.element && (
              <span className="px-3 py-1 font-semibold" style={{ fontSize: 14, color: WUXING_COLORS[formation.element], background: WUXING_BG[formation.element], borderRadius: 6 }}>
                {formation.element}
              </span>
            )}
          </div>
        </section>
      )}

      {/* 破格条件 */}
      {breakConditions && breakConditions.length > 0 && (
        <section className="card">
          <div className="border-b border-[var(--border)] px-6 py-4">
            <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>破格条件</h3>
          </div>
          <div className="p-7 space-y-4">
            {breakConditions.map((bc, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="px-2.5 py-1 font-bold shrink-0" style={{ fontSize: 13, borderRadius: 6, background: bc.severity === "high" ? "rgba(196,60,44,0.08)" : bc.severity === "medium" ? "rgba(184,146,63,0.08)" : "rgba(168,168,148,0.06)", color: bc.severity === "high" ? "var(--danger)" : bc.severity === "medium" ? "var(--warning)" : "var(--text-3)" }}>
                  {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                </span>
                <div>
                  <div className="font-semibold mb-0.5" style={{ fontSize: 15, color: "var(--ink)" }}>{bc.type}</div>
                  {bc.detail && <div style={{ fontSize: 13, color: "var(--text-3)" }}>{bc.detail}</div>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 神煞 */}
      <ShenShaInline result={result} />
    </div>
  );
}


function ShenShaInline({ result }: { result: Record<string, unknown> }) {
  const shensha = result.shensha as Array<{ name: string; position: string; type: string; desc?: string }> | undefined;
  const [activeItem, setActiveItem] = useState<{ name: string; position: string } | null>(null);

  if (!shensha || shensha.length === 0) return null;

  const TYPE_ORDER = ["吉", "凶", "中"];
  const TYPE_LABELS: Record<string, string> = { "吉": "吉神", "凶": "凶煞", "中": "中性" };
  const grouped: Record<string, typeof shensha> = {};
  for (const t of TYPE_ORDER) {
    const items = shensha.filter(s => s.type === t);
    if (items.length > 0) grouped[t] = items;
  }

  const TYPE_COLORS: Record<string, { dot: string; bg: string; text: string; border: string }> = {
    吉: { dot: "var(--wx-wood)", bg: "rgba(58,125,92,0.06)", text: "var(--wx-wood)", border: "rgba(58,125,92,0.16)" },
    凶: { dot: "var(--wx-fire)", bg: "rgba(196,82,58,0.06)", text: "var(--wx-fire)", border: "rgba(196,82,58,0.16)" },
    中: { dot: "var(--wx-earth)", bg: "rgba(197,165,90,0.06)", text: "var(--wx-earth)", border: "rgba(197,165,90,0.14)" },
  };

  return (
    <section className="card relative" style={{ zIndex: activeItem ? 10 : 1 }}>
      <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>神煞</h3>
        <span className="text-[13px]" style={{ color: "var(--text-4)" }}>{shensha.length}个</span>
      </div>
      <div className="p-6 space-y-5">
        {Object.entries(grouped).map(([type, items]) => {
          const colors = TYPE_COLORS[type] || TYPE_COLORS["中"];
          return (
            <div key={type}>
              <div className="flex items-center gap-2 mb-3">
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.dot, flexShrink: 0 }} />
                <span className="font-semibold" style={{ fontSize: 13, color: "var(--ink)" }}>{TYPE_LABELS[type] || type}</span>
                <span style={{ fontSize: 11, color: "var(--text-4)" }}>{items.length}个</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {items.map((item, i) => {
                  const isActive = activeItem?.name === item.name && activeItem?.position === item.position;
                  return (
                    <div key={i} style={{ position: "relative" }}>
                      <button
                        onClick={() => setActiveItem(isActive ? null : { name: item.name, position: item.position })}
                        className="px-3 py-1.5 transition-all duration-200"
                        style={{
                          fontSize: 13,
                          fontWeight: 500,
                          fontFamily: "var(--font-display)",
                          background: isActive ? colors.bg.replace("0.06", "0.15") : colors.bg,
                          color: colors.text,
                          border: `1px solid ${isActive ? colors.text : colors.border}`,
                          borderRadius: 9999,
                          cursor: "pointer",
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.04)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
                      >
                        {item.name}
                      </button>

                      {isActive && item.desc && (
                        <div
                          style={{
                            position: "absolute",
                            bottom: "calc(100% + 8px)",
                            left: "50%",
                            transform: "translateX(-50%)",
                            width: 280,
                            padding: "12px 14px",
                            background: "var(--surface)",
                            border: "1px solid var(--border-strong)",
                            borderRadius: 10,
                            boxShadow: "var(--shadow-lg)",
                            zIndex: 50,
                            animation: "fadeIn 0.15s ease",
                          }}
                        >
                          <div style={{ position: "absolute", bottom: -6, left: "50%", transform: "translateX(-50%) rotate(45deg)", width: 10, height: 10, background: "var(--surface)", borderRight: "1px solid var(--border-strong)", borderBottom: "1px solid var(--border-strong)" }} />
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="font-bold" style={{ fontSize: 14, color: colors.text, fontFamily: "var(--font-display)" }}>{item.name}</span>
                            <span style={{ fontSize: 11, color: "var(--text-4)" }}>{item.position}柱</span>
                            <button
                              onClick={(e) => { e.stopPropagation(); setActiveItem(null); }}
                              className="ml-auto"
                              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-4)", fontSize: 16, padding: 2, lineHeight: 1 }}
                            >
                              ×
                            </button>
                          </div>
                          <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--text-2)" }}>
                            {item.desc || SHENSHA_FALLBACK_DESC[item.name] || "暂无详细说明"}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

const SHENSHA_FALLBACK_DESC: Record<string, string> = {
  "天乙贵人": "《三命通会》：天乙者，乃天上之神，其神最尊贵。所至之处，一切凶煞隐然而避。逢凶化吉，遇难呈祥，主贵人相助。",
  "文昌贵人": "《三命通会》：文昌入命，主聪明过人，气质雅秀。主聪明好学，利考试、文艺、学术。",
  "驿马": "《三命通会》：驿马者，主奔波流动。马头带剑，威震边疆。利出行、迁移、变动。",
  "桃花":"《渊海子平》：墙内桃花主夫妻恩爱，墙外桃花主人缘广博。主人缘、异性缘，亦主才艺风流。",
  "华盖": "《三命通会》：华盖者，喻如宝盖。此星主孤高，多主聪明好学，近佛近道。利宗教、艺术、学术。",
  "将星": "《三命通会》：将星文武两相宜，禄重权高足可知。主权威领导，利掌权、管理。",
  "禄神": "《渊海子平》：禄，爵禄也。主衣食丰足，自力更生之福。",
  "羊刃": "《渊海子平》：禄前一位为羊刃。主刚强果断，过旺则主灾伤刑克。身旺逢刃则凶，身弱逢刃则吉。",
  "金舆": "《三命通会》：金舆者，金车之象。主出行安逸，利车马交通。",
  "天德贵人": "《三命通会》：天德者，福德之神。主逢凶化吉，一生少灾。",
  "月德贵人": "《三命通会》：月德者，月之德神。主仁慈宽厚，遇事有贵人扶持。",
  "孤辰": "《渊海子平》：孤辰入命，主孤独。男命尤忌，主离祖别亲。",
  "寡宿": "《渊海子平》：寡宿入命，主孤寡。女命尤忌，主婚姻不顺。",
  "太极贵人": "《三命通会》：太极者，太初也。主聪慧好学，近道近佛，利玄学研究。",
  "魁罡": "《渊海子平》：魁罡者，刚烈之神。主性格刚毅，聪明果断，有领导才能。",
  "劫煞": "《三命通会》：劫煞者，三合局之煞位。主破财、官非、意外灾祸，宜守不宜攻。",
  "灾煞": "《三命通会》：灾煞者，劫煞之对冲。主疾病、灾厄、口舌是非。",
  "亡神": "《三命通会》：亡神者，机谋深远之神。主机谋深远，善于策划，亦主暗损。",
  "天罗地网": "《渊海子平》：天罗地网，主做事多阻碍牵绊。宜谨慎行事，稳中求进。",
  "红鸾": "《三命通会》：红鸾者，主婚恋之喜。利婚嫁、感情。",
  "天喜": "《三命通会》：天喜者，主喜庆之事。利婚嫁、添丁。",
  "咸池": "《三命通会》：咸池者，日出之地。主情欲、风流、人缘。",
  "童子煞": "《渊海子平》：童子入命，主性情灵巧，亦主多病多灾，不利婚姻。",
  "十恶大败": "《三命通会》：十恶大败日，主祖业难守，败散家财，宜白手起家。",
  "披麻": "《渊海子平》：披麻者，丧吊煞之一。主孝服、丧事、不利亲友。",
};
