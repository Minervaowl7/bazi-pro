"use client";

import { WUXING_COLORS } from "@/lib/constants";

interface Props {
  result: Record<string, unknown>;
  narration?: Record<string, unknown>;
}

const SECTION_TITLES: Record<string, { label: string; icon: string }> = {
  overview: { label: "命盘综述", icon: "☯" },
  strength: { label: "旺衰分析", icon: "⚖" },
  pattern: { label: "格局判定", icon: "🏛" },
  yongshen: { label: "喜用神", icon: "✦" },
  tiaohou: { label: "调候分析", icon: "🌤" },
  elements: { label: "五行力量", icon: "◉" },
  relations: { label: "刑冲合害", icon: "⚡" },
  personality: { label: "性情推断", icon: "🎭" },
  career: { label: "事业方向", icon: "🔭" },
};

function SectionCard({ sectionKey, content }: { sectionKey: string; content: string }) {
  const meta = SECTION_TITLES[sectionKey];
  if (!meta || !content) return null;

  const lines = content.split("\n").filter((l) => l.trim());

  return (
    <section className="card w-full max-w-[860px] mx-auto">
      <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] px-8 py-[18px]">
        <span aria-hidden="true" className="text-base opacity-70">{meta.icon}</span>
        <h3 className="text-base font-semibold tracking-wide" style={{ fontFamily: "var(--font-display)" }}>{meta.label}</h3>
      </div>
      <div className="px-8 py-6">
        {lines.map((line, i) => (
          <p key={i} className="text-[15px] leading-loose" style={{ color: "var(--text-2)", marginBottom: i < lines.length - 1 ? 8 : 0 }}>{line}</p>
        ))}
      </div>
    </section>
  );
}

function SchoolSectionCard({ title, icon, color, children }: {
  title: string; icon: string; color: string; children: React.ReactNode;
}) {
  return (
    <section className="card w-full max-w-[860px] mx-auto" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] px-8 py-[18px]">
        <span aria-hidden="true" className="text-base opacity-70">{icon}</span>
        <h3 className="text-base font-semibold tracking-wide" style={{ color, fontFamily: "var(--font-display)" }}>{title}</h3>
      </div>
      <div className="px-8 py-[22px]">
        {children}
      </div>
    </section>
  );
}

function WuxingSpan({ text }: { text: string }) {
  return (
    <>
      {text.split("").map((ch, i) => {
        const wx = ["金", "木", "水", "火", "土"].includes(ch) ? ch : "";
        const color = wx ? WUXING_COLORS[wx] : "var(--ink)";
        return <span key={i} style={{ color }}>{ch}</span>;
      })}
    </>
  );
}

function ZipingSchoolView({ data }: { data: Record<string, unknown> }) {
  const pattern = data.pattern as { pattern?: string; confidence?: number; reason?: string; break_conditions?: Array<{ type?: string; severity?: string; detail?: string }> } | undefined;
  const wangshuai = data.wangshuai as { verdict?: string } | undefined;
  const yongshen = data.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[]; trace?: { method?: string; reason?: string } } | undefined;
  const breakConditions = pattern?.break_conditions || (data.break_conditions as Array<{ type?: string; severity?: string; detail?: string }> | undefined) || [];
  const dayunVerdict = data.dayun_verdict as Array<{ step?: number; gan?: string; zhi?: string; shishen?: string; verdict?: string; detail?: string }> | undefined;

  return (
    <div className="flex flex-col gap-5">
      <SchoolSectionCard title="子平格局判定" icon="🏛" color="var(--wx-water)">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <span className="text-xl font-bold" style={{ color: "var(--wx-water)", fontFamily: "var(--font-display)" }}>{pattern?.pattern || "—"}</span>
            {pattern?.confidence !== undefined && (
              <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
                <div style={{ flex: 1, height: 6, background: "var(--surface-2)", overflow: "hidden" }}>
                  <div style={{
                    width: `${Math.min(pattern.confidence * 100, 100)}%`,
                    height: "100%",
                    background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                  }} />
                </div>
                <span style={{ fontSize: 14, color: "var(--text-3)", fontVariantNumeric: "tabular-nums" }}>
                  {(pattern.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
          {pattern?.reason && (
            <p style={{ fontSize: 15, lineHeight: 1.85, color: "var(--text-2)" }}>{pattern.reason}</p>
          )}
          {wangshuai?.verdict && (
            <p style={{ fontSize: 15 }}>旺衰：<span style={{ fontWeight: 700, color: "var(--ink)", fontFamily: "var(--font-display)" }}>{wangshuai.verdict}</span></p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="子平用神（破格调整后）" icon="✦" color="var(--wx-water)">
        <div className="flex flex-col gap-3.5">
          <div className="flex items-center gap-3">
            <span className="font-bold text-[13px] px-3 py-1 rounded" style={{ background: "rgba(45,125,91,0.10)", color: "var(--success)" }}>用神</span>
            <span className="text-lg font-bold" style={{ fontFamily: "var(--font-display)" }}><WuxingSpan text={yongshen?.yongshen || "—"} /></span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-bold text-[13px] px-3 py-1 rounded" style={{ background: "rgba(53,94,133,0.08)", color: "var(--wx-water)" }}>喜神</span>
            <span className="text-[17px]" style={{ color: "var(--text-2)" }}><WuxingSpan text={(yongshen?.xishen || []).join("、") || "—"} /></span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-bold text-[13px] px-3 py-1 rounded" style={{ background: "rgba(196,60,44,0.08)", color: "var(--danger)" }}>忌神</span>
            <span className="text-[17px]" style={{ color: "var(--text-2)" }}><WuxingSpan text={(yongshen?.jishen || []).join("、") || "—"} /></span>
          </div>
          {yongshen?.trace?.reason && (
            <p className="text-sm mt-1" style={{ color: "var(--text-3)" }}>推导：{yongshen.trace.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      {breakConditions.length > 0 && (
        <SchoolSectionCard title="破格条件" icon="⚠" color="var(--warning)">
          <div className="flex flex-col gap-3">
            {breakConditions.map((bc, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{
                  background: bc.severity === "high" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: bc.severity === "high" ? "var(--danger)" : "var(--warning)",
                }}>
                  {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                </span>
                <div>
                  <span style={{ fontWeight: 600, fontSize: 15, color: "var(--ink)" }}>{bc.type}</span>
                  {bc.detail && <span style={{ fontSize: 14, color: "var(--text-3)", marginLeft: 8 }}>{bc.detail}</span>}
                </div>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（子平法）" icon="🌊" color="var(--wx-water)">
          <div className="flex flex-col gap-2.5">
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="shrink-0 w-7 text-[13px] tabular-nums" style={{ color: "var(--text-4)" }}>{d.step}</span>
                <span className="font-bold shrink-0 text-[17px]" style={{ fontFamily: "var(--font-display)" }}>{d.gan}{d.zhi}</span>
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{
                  background: d.verdict === "吉" ? "rgba(45,125,91,0.10)" : d.verdict === "凶" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span className="text-sm" style={{ color: "var(--text-2)" }}>{d.detail}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}
    </div>
  );
}

function MangpaiSchoolView({ data }: { data: Record<string, unknown> }) {
  const binzhu = data.binzhu as { interpretations?: Array<{ type?: string; meaning?: string }> } | undefined;
  const tiyong = data.tiyong as { ti?: Array<{ shishen?: string; gan?: string }>; yong?: Array<{ shishen?: string; gan?: string }>; ti_strength?: number; yong_strength?: number } | undefined;
  const gongli = data.gongli as { level?: string; score?: number; analysis?: string } | undefined;
  const zuokong = data.zuokong as Record<string, Array<{ type?: string; description?: string }>> | undefined;
  const summary = data.summary as string | undefined;
  const yingqi = data.yingqi as { triggers?: Array<{ type?: string; description?: string }> } | undefined;

  const allGong: Array<{ type?: string; description?: string }> = [];
  if (zuokong) {
    for (const gongList of Object.values(zuokong)) {
      if (Array.isArray(gongList)) allGong.push(...gongList);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <SchoolSectionCard title="宾主分析" icon="👥" color="var(--school-mangpai)">
        {(binzhu?.interpretations || []).length > 0 ? (
          <div className="flex flex-col gap-3">
            {(binzhu?.interpretations || []).map((interp, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{ background: "color-mix(in srgb, var(--school-mangpai) 10%, transparent)", color: "var(--school-mangpai)" }}>
                  {interp.type}
                </span>
                <span className="text-[15px] leading-[1.75]" style={{ color: "var(--text-2)" }}>{interp.meaning}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[15px]" style={{ color: "var(--text-3)" }}>宾主无明显交战</p>
        )}
      </SchoolSectionCard>

      <SchoolSectionCard title="体用分析" icon="⚖" color="var(--school-mangpai)">
        <div className="flex flex-col gap-3.5">
          <div className="flex items-center gap-5 text-base">
            <span>体 <span style={{ fontWeight: 700, color: "var(--school-mangpai)", fontFamily: "var(--font-display)", fontSize: 18 }}>{(tiyong?.ti || []).map(t => t.gan).join(" ") || "无"}</span></span>
            <span style={{ color: "var(--text-4)" }}>vs</span>
            <span>用 <span style={{ fontWeight: 700, color: "var(--school-mangpai)", fontFamily: "var(--font-display)", fontSize: 18 }}>{(tiyong?.yong || []).map(t => t.gan).join(" ") || "无"}</span></span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 14, color: "var(--text-3)" }}>
            <span>体力 {tiyong?.ti_strength?.toFixed(1) || 0}</span>
            <span>·</span>
            <span>用力 {tiyong?.yong_strength?.toFixed(1) || 0}</span>
          </div>
        </div>
      </SchoolSectionCard>

      {allGong.length > 0 && (
        <SchoolSectionCard title="做功分析" icon="⚙" color="var(--school-mangpai)">
          <div className="flex flex-col gap-3">
            {allGong.slice(0, 6).map((g, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{ background: "color-mix(in srgb, var(--school-mangpai) 10%, transparent)", color: "var(--school-mangpai)" }}>
                  {g.type}
                </span>
                <span className="text-[15px]" style={{ color: "var(--text-2)" }}>{g.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="功力评定" icon="📊" color="var(--school-mangpai)">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold" style={{ color: "var(--school-mangpai)", fontFamily: "var(--font-display)" }}>{gongli?.level || "—"}</span>
            <span className="text-sm" style={{ color: "var(--text-3)" }}>{gongli?.score ?? "—"}分</span>
          </div>
          {gongli?.analysis && (
            <p className="text-[15px] leading-[1.85]" style={{ color: "var(--text-2)" }}>{gongli.analysis}</p>
          )}
        </div>
      </SchoolSectionCard>

      {yingqi && (yingqi.triggers || []).length > 0 && (
        <SchoolSectionCard title="应期提示" icon="🕐" color="var(--school-mangpai)">
          <div className="flex flex-col gap-3">
            {(yingqi.triggers || []).map((t, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{ background: "color-mix(in srgb, var(--school-mangpai) 10%, transparent)", color: "var(--school-mangpai)" }}>
                  {t.type}
                </span>
                <span className="text-[15px]" style={{ color: "var(--text-2)" }}>{t.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary && (
        <SchoolSectionCard title="盲派总评" icon="👁" color="var(--school-mangpai)">
          <p className="text-[15px] leading-loose" style={{ color: "var(--text-2)" }}>{summary}</p>
        </SchoolSectionCard>
      )}
    </div>
  );
}

function XinpaiSchoolView({ data }: { data: Record<string, unknown> }) {
  const yongJi = data.yong_ji as { sheng_fu?: string; yongshen?: string[]; yongshen_name?: string[]; jishen_name?: string[]; reason?: string } | undefined;
  const kongwang = data.kongwang as { kongwang_zhi?: string[]; affected?: Array<{ position?: string; zhi?: string }> } | undefined;
  const baishen = data.baishen as { replacements?: Record<string, { original?: string; replacement?: string; reason?: string }> } | undefined;
  const fanduan = data.fanduan as { conditions?: Array<{ type?: string; description?: string; action?: string }>; total_conditions?: number } | undefined;
  const summary = data.summary as { yongshen?: string; jishen?: string; kongwang?: string; fanduan_count?: number; advice?: string } | undefined;
  const dayunVerdict = data.dayun_verdict as Array<{ step?: number; gan?: string; zhi?: string; verdict?: string; detail?: string }> | undefined;

  return (
    <div className="flex flex-col gap-5">
      <SchoolSectionCard title="身扶判定" icon="⚖" color="var(--school-xinpai)">
        <div className="flex flex-col gap-3">
          <span style={{ fontWeight: 700, fontSize: 20, color: "var(--school-xinpai)", fontFamily: "var(--font-display)" }}>{yongJi?.sheng_fu || "—"}</span>
          {yongJi?.reason && (
            <p style={{ fontSize: 14, color: "var(--text-3)" }}>{yongJi.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="新派用忌神" icon="✦" color="var(--school-xinpai)">
        <div className="flex flex-col gap-3.5">
          <div className="flex items-center gap-3">
            <span className="font-bold text-[13px] px-3 py-1 rounded" style={{ background: "rgba(45,125,91,0.10)", color: "var(--success)" }}>用神</span>
            <span className="text-[17px] font-bold" style={{ fontFamily: "var(--font-display)" }}><WuxingSpan text={(yongJi?.yongshen_name || []).join("、") || "—"} /></span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-bold text-[13px] px-3 py-1 rounded" style={{ background: "rgba(196,60,44,0.08)", color: "var(--danger)" }}>忌神</span>
            <span className="text-[17px]" style={{ color: "var(--text-2)" }}><WuxingSpan text={(yongJi?.jishen_name || []).join("、") || "—"} /></span>
          </div>
        </div>
      </SchoolSectionCard>

      {baishen && baishen.replacements && Object.keys(baishen.replacements).length > 0 && (
        <SchoolSectionCard title="百神论替换" icon="🔄" color="var(--school-xinpai)">
          <div className="flex flex-col gap-3">
            {Object.entries(baishen.replacements).map(([key, val], i) => {
              const v = val as { original?: string; replacement?: string; reason?: string };
              return (
                <div key={i} className="flex items-start gap-3">
                  <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{ background: "color-mix(in srgb, var(--school-xinpai) 10%, transparent)", color: "var(--school-xinpai)" }}>
                    {v.original || key}
                  </span>
                  <span className="text-[15px]" style={{ color: "var(--text-2)" }}>→ {v.replacement}{v.reason ? `（${v.reason}）` : ""}</span>
                </div>
              );
            })}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="空亡论" icon="◯" color="var(--school-xinpai)">
        {(kongwang?.kongwang_zhi || []).length > 0 ? (
          <div className="flex flex-col gap-3.5">
            <div className="flex flex-wrap gap-2.5">
              {(kongwang?.kongwang_zhi || []).map((zhi) => (
                <span key={zhi} className="font-bold px-3.5 py-1 text-[15px] rounded" style={{ background: "color-mix(in srgb, var(--school-xinpai) 8%, transparent)", color: "var(--school-xinpai)", fontFamily: "var(--font-display)" }}>
                  {zhi}
                </span>
              ))}
            </div>
            {(kongwang?.affected || []).length > 0 && (
              <p className="text-sm" style={{ color: "var(--text-3)" }}>
                影响柱位：{(kongwang?.affected || []).map(a => a.position).join("、")}
              </p>
            )}
          </div>
        ) : (
          <p style={{ fontSize: 15, color: "var(--text-3)" }}>无空亡</p>
        )}
      </SchoolSectionCard>

      {fanduan && (fanduan.total_conditions || 0) > 0 && (
        <SchoolSectionCard title="反断论" icon="↕" color="var(--school-xinpai)">
          <div className="flex flex-col gap-3">
            {(fanduan.conditions || []).map((c, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{ background: "color-mix(in srgb, var(--school-xinpai) 10%, transparent)", color: "var(--school-xinpai)" }}>
                  {c.action}
                </span>
                <span className="text-[15px]" style={{ color: "var(--text-2)" }}>{c.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（新派）" icon="🌊" color="var(--school-xinpai)">
          <div className="flex flex-col gap-2.5">
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="shrink-0 w-7 text-[13px] tabular-nums" style={{ color: "var(--text-4)" }}>{d.step}</span>
                <span className="font-bold shrink-0 text-[17px]" style={{ fontFamily: "var(--font-display)" }}>{d.gan}{d.zhi}</span>
                <span className="font-bold shrink-0 text-[13px] px-2.5 py-[3px] rounded" style={{
                  background: d.verdict === "吉" ? "rgba(45,125,91,0.10)" : d.verdict === "凶" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span className="text-sm" style={{ color: "var(--text-2)" }}>{d.detail}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary?.advice && (
        <SchoolSectionCard title="新派总评" icon="✧" color="var(--school-xinpai)">
          <p className="text-[15px] leading-loose" style={{ color: "var(--text-2)" }}>{summary.advice}</p>
        </SchoolSectionCard>
      )}
    </div>
  );
}

export default function SchoolPanel({ result, narration }: Props) {
  const school = (result.school as string) || "ziping";
  const schoolAnalysis = result.school_analysis as Record<string, unknown> | undefined;
  const schoolAnalyses = result.school_analyses as Record<string, unknown> | undefined;

  const currentSchoolData = (schoolAnalyses?.[school] as Record<string, unknown> | undefined) ?? schoolAnalysis;

  const hasSchoolData = currentSchoolData && currentSchoolData.status === "completed";

  const sections = Object.entries(SECTION_TITLES).map(([key]) => {
    const content = narration?.[key] as string | undefined;
    return { key, content: content || "" };
  }).filter(s => s.content);

  const SCHOOL_META: Record<string, { label: string; icon: string; color: string }> = {
    ziping: { label: "传统子平法", icon: "☯", color: "var(--wx-water)" },
    mangpai: { label: "盲派", icon: "👁", color: "var(--school-mangpai)" },
    xinpai: { label: "新派", icon: "✧", color: "var(--school-xinpai)" },
  };

  const schoolMeta = SCHOOL_META[school] || SCHOOL_META.ziping;

  return (
    <div className="w-full">
      <div className="max-w-[860px] mx-auto mb-8 flex items-center gap-3 flex-wrap">
        <h2 className="text-xl font-bold" style={{ fontFamily: "var(--font-display)" }}>命理解读</h2>
        <span className="font-semibold text-[13px] px-3 py-1 rounded" style={{ background: "var(--surface-2)", color: "var(--text-2)" }}>
          {sections.length} 维度
        </span>
        {hasSchoolData && (
          <span className="font-semibold text-[13px] px-3 py-1 rounded" style={{ background: `color-mix(in srgb, ${schoolMeta.color} 7%, transparent)`, color: schoolMeta.color }}>
            {schoolMeta.icon} {schoolMeta.label}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-6">
        {sections.map((s) => (
          <SectionCard key={s.key} sectionKey={s.key} content={s.content} />
        ))}

        {hasSchoolData && school === "ziping" && (
          <ZipingSchoolView data={currentSchoolData} />
        )}
        {hasSchoolData && school === "mangpai" && (
          <MangpaiSchoolView data={currentSchoolData} />
        )}
        {hasSchoolData && school === "xinpai" && (
          <XinpaiSchoolView data={currentSchoolData} />
        )}
      </div>
    </div>
  );
}
