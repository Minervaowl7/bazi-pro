"use client";

import { useState, useRef, useLayoutEffect } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { WUXING_COLORS, WUXING_BG, GAN_WUXING, ZHI_WUXING, RELATION_COLORS } from "@/lib/constants";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";

const TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
const DIZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];
const SHENGXIAO = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"];
const ZHI_CHONG: Record<string,string> = { 子:"午",午:"子",丑:"未",未:"丑",寅:"申",申:"寅",卯:"酉",酉:"卯",辰:"戌",戌:"辰",巳:"亥",亥:"巳" };
const ZHI_HE: Record<string,string> = { 子:"丑",丑:"子",寅:"亥",亥:"寅",卯:"戌",戌:"卯",辰:"酉",酉:"辰",巳:"申",申:"巳",午:"未",未:"午" };
const ZHI_XING: Record<string,string[]> = { 子:["卯"],卯:["子"],寅:["巳","申"],巳:["寅","申"],申:["寅","巳"],丑:["未","戌"],未:["丑","戌"],戌:["丑","未"],辰:["辰"],午:["午"],酉:["酉"],亥:["亥"] };
const ZHI_HAI: Record<string,string> = { 子:"未",未:"子",丑:"午",午:"丑",寅:"巳",巳:"寅",卯:"辰",辰:"卯",申:"亥",亥:"申",酉:"戌",戌:"酉" };
const GAN_HE: Record<string,string> = { 甲:"己",己:"甲",乙:"庚",庚:"乙",丙:"辛",辛:"丙",丁:"壬",壬:"丁",戊:"癸",癸:"戊" };
const GAN_CHONG: Record<string,string> = { 甲:"庚",庚:"甲",乙:"辛",辛:"乙",丙:"壬",壬:"丙",丁:"癸",癸:"丁" };

interface LiunianRelation { type: string; desc: string; }
function calcLiunianRelations(lnGan:string, lnZhi:string, natalGans:string[], natalZhis:string[]): LiunianRelation[] {
  const positions = ["年","月","日","时"];
  const rels: LiunianRelation[] = [];
  for (let i=0;i<natalZhis.length;i++) {
    if (ZHI_CHONG[lnZhi]===natalZhis[i]) rels.push({type:"冲",desc:`${lnZhi}冲${positions[i]}${natalZhis[i]}`});
    if (ZHI_HE[lnZhi]===natalZhis[i]) rels.push({type:"合",desc:`${lnZhi}合${positions[i]}${natalZhis[i]}`});
    if ((ZHI_XING[lnZhi]||[]).includes(natalZhis[i])) rels.push({type:"刑",desc:`${lnZhi}刑${positions[i]}${natalZhis[i]}`});
    if (ZHI_HAI[lnZhi]===natalZhis[i]) rels.push({type:"害",desc:`${lnZhi}害${positions[i]}${natalZhis[i]}`});
  }
  for (let i=0;i<natalGans.length;i++) {
    if (GAN_HE[lnGan]===natalGans[i]) rels.push({type:"合",desc:`${lnGan}合${positions[i]}${natalGans[i]}`});
    if (GAN_CHONG[lnGan]===natalGans[i]) rels.push({type:"冲",desc:`${lnGan}冲${positions[i]}${natalGans[i]}`});
  }
  return rels;
}
function getYearGanzhi(year:number) {
  const ganIdx=((year-4)%10+10)%10, zhiIdx=((year-4)%12+12)%12;
  return {gan:TIANGAN[ganIdx],zhi:DIZHI[zhiIdx],shengxiao:SHENGXIAO[zhiIdx]};
}

interface DayunStep { gan?:string; zhi?:string; age_range?:string; start_age?:number; gan_wuxing?:string; zhi_wuxing?:string; shishen_gan?:string; [key:string]:unknown; }
interface Props { result: Record<string,unknown>; }

export default function DayunTimeline({ result }: Props) {
  const dayun = (result.dayun as DayunStep[]|undefined) || (result.paipan_dayun as DayunStep[]|undefined);
  const [expandedIdx,setExpandedIdx]=useState<number|null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const currentBadgeRef = useRef<HTMLSpanElement>(null);
  const expandCtx = useRef<gsap.Context | null>(null);

  const prefersReducedMotion = usePrefersReducedMotion();

  useGSAP(() => {
    if (prefersReducedMotion) {
      gsap.set(containerRef.current, { autoAlpha: 1 });
      return;
    }

    const tl = gsap.timeline();

    tl.from(containerRef.current, {
      y: 30, autoAlpha: 0, duration: 0.7, ease: "power3.out",
    });

    // 大运行交错入场
    const rows = containerRef.current?.querySelectorAll("[data-dayun-row]");
    if (rows && rows.length > 0) {
      tl.from(rows, {
        x: -16, autoAlpha: 0, stagger: 0.06, duration: 0.4, ease: "power2.out",
      }, "-=0.3");
    }

    if (currentBadgeRef.current) {
      gsap.to(currentBadgeRef.current, {
        scale: 1.06, duration: 1.2, repeat: -1, yoyo: true, ease: "sine.inOut",
      });
    }
  }, { scope: containerRef });

  const contextSafe = useGSAP({ scope: containerRef }).contextSafe;

  useLayoutEffect(() => {
    if (expandCtx.current) {
      expandCtx.current.revert();
      expandCtx.current = null;
    }

    const grid = containerRef.current?.querySelector(".liunian-grid");
    if (!grid) return;

    if (prefersReducedMotion) {
      gsap.set(grid, { autoAlpha: 1 });
      return;
    }

    expandCtx.current = gsap.context(() => {
      gsap.set(grid, { height: 0, autoAlpha: 0 });
      gsap.to(grid, { height: "auto", autoAlpha: 1, duration: 0.4, ease: "power2.out" });
    });

    return () => {
      if (expandCtx.current) {
        expandCtx.current.revert();
        expandCtx.current = null;
      }
    };
  }, [expandedIdx, prefersReducedMotion]);

  if (!dayun||dayun.length===0) return null;

  const birthYear=Number(result.birth_year)||0;
  const currentYear=new Date().getFullYear();
  const currentAge=birthYear?currentYear-birthYear:0;

  const shishen=result.shishen as {pillars?:Array<{gan?:string;zhi?:string}>}|undefined;
  const natalGans=(shishen?.pillars||[]).map((p)=>p.gan||"").filter(Boolean);
  const natalZhis=(shishen?.pillars||[]).map((p)=>p.zhi||"").filter(Boolean);

  const handleDayunClick = contextSafe((i: number) => {
    setExpandedIdx(prev => prev === i ? null : i);
  });

  return (
    <section
      ref={containerRef}
      className="card"
      style={{ opacity: prefersReducedMotion ? 1 : 0 }}
    >
      <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>大运流年</h3>
        <span className="text-[13px]" style={{ color: "var(--text-4)" }}>共{dayun.length}步大运</span>
      </div>

      <div style={{ borderTop: "1px solid var(--border-subtle)", position: "relative" }}>
        {/* 左侧垂直时间线 */}
        <div style={{
          position: "absolute",
          left: 72,
          top: 0,
          bottom: 0,
          width: 1,
          background: "rgba(180,160,120,0.12)",
        }} />

        {dayun.map((d, i) => {
          const gan = String(d.gan || ""), zhi = String(d.zhi || "");
          const ganWx = d.gan_wuxing as string | undefined;
          const zhiWx = d.zhi_wuxing as string | undefined;
          const ganColor = ganWx ? WUXING_COLORS[ganWx] : "var(--ink)";
          const zhiColor = zhiWx ? WUXING_COLORS[zhiWx] : "var(--ink)";
          const ageRange = String(d.age_range || "");
          const startAge = Number(d.start_age || 0), endAge = startAge + 9;
          const isCurrent = currentAge >= startAge && currentAge <= endAge && startAge > 0;
          const isExpanded = expandedIdx === i;
          const startYear = birthYear ? birthYear + startAge : 0;

          return (
            <div key={i} className={i < dayun.length - 1 ? "border-b border-[var(--border-subtle)]" : ""}>
              <button
                data-dayun-row
                aria-expanded={isExpanded}
                className="dayun-row w-full flex items-center pr-6 py-3.5 hover-row relative"
                style={{
                  background: isCurrent ? "linear-gradient(135deg, rgba(201,100,66,0.06), rgba(180,154,92,0.06))" : "transparent",
                }}
                onClick={() => handleDayunClick(i)}
              >
                {/* 圆点装饰 */}
                <div className="absolute left-[68px] top-1/2 -translate-x-1/2 -translate-y-1/2 w-[9px] h-[9px] rounded-full z-[1]" style={{
                  background: isCurrent ? "var(--cinnabar)" : "var(--surface)",
                  border: `2px solid ${isCurrent ? "var(--cinnabar)" : "var(--gold)"}`,
                }} />

                {/* 年龄标签 */}
                <span className="shrink-0" style={{ width: 40, textAlign: "right", fontSize: 12, color: "var(--text-4)", fontVariantNumeric: "tabular-nums" }}>
                  {ageRange || `${startAge}`}
                </span>

                {/* 间距 */}
                <span style={{ width: 32 }} />

                {/* 干支 */}
                <span className="font-bold shrink-0" style={{ width: 64, textAlign: "center", fontSize: 20, fontFamily: "var(--font-display)" }}>
                  <span style={{ color: ganColor }}>{gan}</span>
                  <span style={{ color: zhiColor }}>{zhi}</span>
                </span>

                {/* 年份范围 */}
                {startYear > 0 && (
                  <span className="shrink-0 tabular-nums" style={{ fontSize: 12, color: "var(--text-4)", marginLeft: 12 }}>
                    {startYear}-{startYear + 9}
                  </span>
                )}

                {/* 五行 badge */}
                <div className="flex gap-1.5 ml-auto shrink-0">
                  {ganWx && <span className="px-2 py-0.5 font-medium" style={{ fontSize: 11, color: ganColor, background: WUXING_BG[ganWx], borderRadius: 9999 }}>{ganWx}</span>}
                  {zhiWx && <span className="px-2 py-0.5 font-medium" style={{ fontSize: 11, color: zhiColor, background: WUXING_BG[zhiWx], borderRadius: 9999 }}>{zhiWx}</span>}
                </div>

                {/* 当前大运徽章 */}
                {isCurrent && (
                  <span ref={currentBadgeRef} className="font-bold shrink-0 px-2.5 py-0.5" style={{
                    fontSize: 11,
                    background: "linear-gradient(135deg, rgba(201,100,66,0.12), rgba(180,154,92,0.12))",
                    color: "var(--cinnabar)",
                    borderRadius: 9999,
                    border: "1px solid rgba(201,100,66,0.25)",
                    boxShadow: "0 0 8px rgba(201,100,66,0.1)",
                    transformOrigin: "center center",
                    display: "inline-block",
                    marginLeft: 8,
                  }}>
                    当前
                  </span>
                )}

                {/* 展开箭头 */}
                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="shrink-0 transition-transform duration-200" style={{ color: "var(--text-4)", transform: isExpanded ? "rotate(180deg)" : "rotate(0)", marginLeft: 8 }}>
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {/* 流年展开详情 */}
              {isExpanded && (
                <div className="liunian-grid grid grid-cols-1 sm:grid-cols-2 gap-0.5 p-6 md:p-7" style={{ background: "var(--surface-2)", overflow: "hidden" }}>
                  {Array.from({ length: 10 }, (_, j) => {
                    const year = startYear > 0 ? startYear + j : 0, age = startAge + j;
                    const { gan: lnGan, zhi: lnZhi, shengxiao } = year > 0 ? getYearGanzhi(year) : { gan: "—", zhi: "", shengxiao: "" };
                    const lnGanWx = GAN_WUXING[lnGan] || "";
                    const lnGanColor = lnGanWx ? WUXING_COLORS[lnGanWx] : "var(--ink)";
                    const lnZhiWx = ZHI_WUXING[lnZhi] || "";
                    const lnZhiColor = lnZhiWx ? WUXING_COLORS[lnZhiWx] : "var(--text-3)";
                    const isThisYear = year > 0 && year === currentYear;
                    const rels = (lnGan && lnZhi && natalGans.length >= 4) ? calcLiunianRelations(lnGan, lnZhi, natalGans, natalZhis) : [];
                    return (
                      <div key={j} className="flex items-center gap-3 px-4 py-2.5" style={{
                        fontSize: 13,
                        background: isThisYear ? "rgba(184,74,60,0.04)" : undefined,
                        border: isThisYear ? "1px solid rgba(184,74,60,0.10)" : "1px solid transparent",
                      }}>
                        <span className="tabular-nums w-11 shrink-0" style={{ color: "var(--text-4)" }}>{year > 0 ? year : `${age}岁`}</span>
                        <span className="font-semibold" style={{ fontFamily: "var(--font-display)", fontSize: 15 }}>
                          <span style={{ color: lnGanColor }}>{lnGan}</span>
                          <span style={{ color: lnZhiColor, marginLeft: 3 }}>{lnZhi}</span>
                        </span>
                        <span style={{ color: "var(--text-4)" }}>{shengxiao}</span>
                        {rels.length > 0 && (
                          <span className="flex gap-1 ml-auto">
                            {rels.slice(0, 3).map((r, ri) => {
                              const bgMap: Record<string, string> = { "冲": "rgba(196,60,44,0.08)", "合": "rgba(53,94,133,0.08)", "刑": "rgba(148,102,54,0.07)", "害": "rgba(184,146,63,0.06)" };
                              return <span key={ri} className="px-2 py-0.5 font-semibold" style={{ fontSize: 11, color: RELATION_COLORS[r.type] || "#a0a0b8", background: bgMap[r.type] || "rgba(160,160,184,0.07)", borderRadius: 9999 }} title={r.desc}>{r.type}</span>;
                            })}
                          </span>
                        )}
                        <span className="ml-auto tabular-nums shrink-0" style={{ color: "var(--text-4)" }}>{year > 0 ? `${age}岁` : ""}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
