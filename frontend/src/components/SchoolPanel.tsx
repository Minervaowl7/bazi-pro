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
    <section style={{
      background: "var(--surface)",
      border: "1px solid var(--color-border)",
      width: "100%",
      maxWidth: 860,
      marginLeft: "auto",
      marginRight: "auto",
    }}>
      <div style={{
        borderBottom: "1px solid var(--color-border-subtle)",
        padding: "18px 32px",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <span aria-hidden="true" style={{ fontSize: 16, opacity: 0.7 }}>{meta.icon}</span>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)", letterSpacing: "0.02em" }}>
          {meta.label}
        </h3>
      </div>
      <div style={{ padding: "24px 32px" }}>
        {lines.map((line, i) => (
          <p key={i} style={{
            fontSize: 15,
            lineHeight: 2,
            color: "var(--color-text-secondary)",
            marginBottom: i < lines.length - 1 ? 8 : 0,
          }}>{line}</p>
        ))}
      </div>
    </section>
  );
}

function SchoolSectionCard({ title, icon, color, children }: {
  title: string; icon: string; color: string; children: React.ReactNode;
}) {
  return (
    <section style={{
      background: "var(--surface)",
      border: "1px solid var(--color-border)",
      borderLeft: `3px solid ${color}`,
      width: "100%",
      maxWidth: 860,
      marginLeft: "auto",
      marginRight: "auto",
    }}>
      <div style={{
        borderBottom: "1px solid var(--color-border-subtle)",
        padding: "18px 32px",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <span aria-hidden="true" style={{ fontSize: 16, opacity: 0.7 }}>{icon}</span>
        <h3 style={{ fontSize: 16, fontWeight: 600, color, fontFamily: "var(--font-serif)", letterSpacing: "0.02em" }}>
          {title}
        </h3>
      </div>
      <div style={{ padding: "22px 32px" }}>
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
        const color = wx ? WUXING_COLORS[wx] : "var(--color-text-primary)";
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
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <SchoolSectionCard title="子平格局判定" icon="🏛" color="var(--el-water)">
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: "var(--el-water)", fontFamily: "var(--font-serif)" }}>{pattern?.pattern || "—"}</span>
            {pattern?.confidence !== undefined && (
              <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
                <div style={{ flex: 1, height: 6, background: "var(--bg-secondary)", overflow: "hidden" }}>
                  <div style={{
                    width: `${Math.min(pattern.confidence * 100, 100)}%`,
                    height: "100%",
                    background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                  }} />
                </div>
                <span style={{ fontSize: 14, color: "var(--color-text-muted)", fontVariantNumeric: "tabular-nums" }}>
                  {(pattern.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
          {pattern?.reason && (
            <p style={{ fontSize: 15, lineHeight: 1.85, color: "var(--color-text-secondary)" }}>{pattern.reason}</p>
          )}
          {wangshuai?.verdict && (
            <p style={{ fontSize: 15 }}>旺衰：<span style={{ fontWeight: 700, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{wangshuai.verdict}</span></p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="子平用神（破格调整后）" icon="✦" color="var(--el-water)">
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 13, padding: "4px 12px", background: "rgba(45,125,91,0.10)", color: "var(--success)" }}>用神</span>
            <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-serif)" }}><WuxingSpan text={yongshen?.yongshen || "—"} /></span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 13, padding: "4px 12px", background: "rgba(53,94,133,0.08)", color: "var(--el-water)" }}>喜神</span>
            <span style={{ fontSize: 17, color: "var(--color-text-secondary)" }}><WuxingSpan text={(yongshen?.xishen || []).join("、") || "—"} /></span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 13, padding: "4px 12px", background: "rgba(196,60,44,0.08)", color: "var(--danger)" }}>忌神</span>
            <span style={{ fontSize: 17, color: "var(--color-text-secondary)" }}><WuxingSpan text={(yongshen?.jishen || []).join("、") || "—"} /></span>
          </div>
          {yongshen?.trace?.reason && (
            <p style={{ fontSize: 14, color: "var(--color-text-muted)", marginTop: 4 }}>推导：{yongshen.trace.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      {breakConditions.length > 0 && (
        <SchoolSectionCard title="破格条件" icon="⚠" color="var(--warning)">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {breakConditions.map((bc, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{
                  fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px",
                  background: bc.severity === "high" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: bc.severity === "high" ? "var(--danger)" : "var(--warning)",
                }}>
                  {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                </span>
                <div>
                  <span style={{ fontWeight: 600, fontSize: 15, color: "var(--color-text-primary)" }}>{bc.type}</span>
                  {bc.detail && <span style={{ fontSize: 14, color: "var(--color-text-muted)", marginLeft: 8 }}>{bc.detail}</span>}
                </div>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（子平法）" icon="🌊" color="var(--el-water)">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ flexShrink: 0, width: 28, fontSize: 13, color: "var(--color-text-faint)", fontVariantNumeric: "tabular-nums" }}>{d.step}</span>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 17, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{d.gan}{d.zhi}</span>
                <span style={{
                  fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px",
                  background: d.verdict === "吉" ? "rgba(45,125,91,0.10)" : d.verdict === "凶" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>{d.detail}</span>
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
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <SchoolSectionCard title="宾主分析" icon="👥" color="#a855f7">
        {(binzhu?.interpretations || []).length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {(binzhu?.interpretations || []).map((interp, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px", background: "rgba(168,85,247,0.10)", color: "#a855f7" }}>
                  {interp.type}
                </span>
                <span style={{ fontSize: 15, color: "var(--color-text-secondary)", lineHeight: 1.75 }}>{interp.meaning}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: 15, color: "var(--color-text-muted)" }}>宾主无明显交战</p>
        )}
      </SchoolSectionCard>

      <SchoolSectionCard title="体用分析" icon="⚖" color="#a855f7">
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20, fontSize: 16 }}>
            <span>体 <span style={{ fontWeight: 700, color: "#a855f7", fontFamily: "var(--font-serif)", fontSize: 18 }}>{(tiyong?.ti || []).map(t => t.gan).join(" ") || "无"}</span></span>
            <span style={{ color: "var(--color-text-faint)" }}>vs</span>
            <span>用 <span style={{ fontWeight: 700, color: "#a855f7", fontFamily: "var(--font-serif)", fontSize: 18 }}>{(tiyong?.yong || []).map(t => t.gan).join(" ") || "无"}</span></span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 14, color: "var(--color-text-muted)" }}>
            <span>体力 {tiyong?.ti_strength?.toFixed(1) || 0}</span>
            <span>·</span>
            <span>用力 {tiyong?.yong_strength?.toFixed(1) || 0}</span>
          </div>
        </div>
      </SchoolSectionCard>

      {allGong.length > 0 && (
        <SchoolSectionCard title="做功分析" icon="⚙" color="#a855f7">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {allGong.slice(0, 6).map((g, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px", background: "rgba(168,85,247,0.10)", color: "#a855f7" }}>
                  {g.type}
                </span>
                <span style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>{g.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="功力评定" icon="📊" color="#a855f7">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 20, color: "#a855f7", fontFamily: "var(--font-serif)" }}>{gongli?.level || "—"}</span>
            <span style={{ fontSize: 14, color: "var(--color-text-muted)" }}>{gongli?.score ?? "—"}分</span>
          </div>
          {gongli?.analysis && (
            <p style={{ fontSize: 15, lineHeight: 1.85, color: "var(--color-text-secondary)" }}>{gongli.analysis}</p>
          )}
        </div>
      </SchoolSectionCard>

      {yingqi && (yingqi.triggers || []).length > 0 && (
        <SchoolSectionCard title="应期提示" icon="🕐" color="#a855f7">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {(yingqi.triggers || []).map((t, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px", background: "rgba(168,85,247,0.10)", color: "#a855f7" }}>
                  {t.type}
                </span>
                <span style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>{t.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary && (
        <SchoolSectionCard title="盲派总评" icon="👁" color="#a855f7">
          <p style={{ fontSize: 15, lineHeight: 2, color: "var(--color-text-secondary)" }}>{summary}</p>
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
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <SchoolSectionCard title="身扶判定" icon="⚖" color="#22c55e">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <span style={{ fontWeight: 700, fontSize: 20, color: "#22c55e", fontFamily: "var(--font-serif)" }}>{yongJi?.sheng_fu || "—"}</span>
          {yongJi?.reason && (
            <p style={{ fontSize: 14, color: "var(--color-text-muted)" }}>{yongJi.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="新派用忌神" icon="✦" color="#22c55e">
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 13, padding: "4px 12px", background: "rgba(45,125,91,0.10)", color: "var(--success)" }}>用神</span>
            <span style={{ fontSize: 17, fontWeight: 700, fontFamily: "var(--font-serif)" }}><WuxingSpan text={(yongJi?.yongshen_name || []).join("、") || "—"} /></span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontWeight: 700, fontSize: 13, padding: "4px 12px", background: "rgba(196,60,44,0.08)", color: "var(--danger)" }}>忌神</span>
            <span style={{ fontSize: 17, color: "var(--color-text-secondary)" }}><WuxingSpan text={(yongJi?.jishen_name || []).join("、") || "—"} /></span>
          </div>
        </div>
      </SchoolSectionCard>

      {baishen && baishen.replacements && Object.keys(baishen.replacements).length > 0 && (
        <SchoolSectionCard title="百神论替换" icon="🔄" color="#22c55e">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {Object.entries(baishen.replacements).map(([key, val], i) => {
              const v = val as { original?: string; replacement?: string; reason?: string };
              return (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                  <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px", background: "rgba(34,197,94,0.10)", color: "#22c55e" }}>
                    {v.original || key}
                  </span>
                  <span style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>→ {v.replacement}{v.reason ? `（${v.reason}）` : ""}</span>
                </div>
              );
            })}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="空亡论" icon="◯" color="#22c55e">
        {(kongwang?.kongwang_zhi || []).length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {(kongwang?.kongwang_zhi || []).map((zhi) => (
                <span key={zhi} style={{ fontWeight: 700, padding: "4px 14px", fontSize: 15, background: "rgba(34,197,94,0.08)", color: "#22c55e", fontFamily: "var(--font-serif)" }}>
                  {zhi}
                </span>
              ))}
            </div>
            {(kongwang?.affected || []).length > 0 && (
              <p style={{ fontSize: 14, color: "var(--color-text-muted)" }}>
                影响柱位：{(kongwang?.affected || []).map(a => a.position).join("、")}
              </p>
            )}
          </div>
        ) : (
          <p style={{ fontSize: 15, color: "var(--color-text-muted)" }}>无空亡</p>
        )}
      </SchoolSectionCard>

      {fanduan && (fanduan.total_conditions || 0) > 0 && (
        <SchoolSectionCard title="反断论" icon="↕" color="#22c55e">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {(fanduan.conditions || []).map((c, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px", background: "rgba(34,197,94,0.10)", color: "#22c55e" }}>
                  {c.action}
                </span>
                <span style={{ fontSize: 15, color: "var(--color-text-secondary)" }}>{c.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（新派）" icon="🌊" color="#22c55e">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ flexShrink: 0, width: 28, fontSize: 13, color: "var(--color-text-faint)", fontVariantNumeric: "tabular-nums" }}>{d.step}</span>
                <span style={{ fontWeight: 700, flexShrink: 0, fontSize: 17, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{d.gan}{d.zhi}</span>
                <span style={{
                  fontWeight: 700, flexShrink: 0, fontSize: 13, padding: "3px 10px",
                  background: d.verdict === "吉" ? "rgba(45,125,91,0.10)" : d.verdict === "凶" ? "rgba(196,60,44,0.08)" : "rgba(184,146,63,0.08)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>{d.detail}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary?.advice && (
        <SchoolSectionCard title="新派总评" icon="✧" color="#22c55e">
          <p style={{ fontSize: 15, lineHeight: 2, color: "var(--color-text-secondary)" }}>{summary.advice}</p>
        </SchoolSectionCard>
      )}
    </div>
  );
}

export default function SchoolPanel({ result, narration }: Props) {
  const school = (result.school as string) || "ziping";
  const schoolAnalysis = result.school_analysis as Record<string, unknown> | undefined;
  const schoolAnalyses = result.school_analyses as Record<string, unknown> | undefined;

  const currentSchoolData = schoolAnalyses?.[school] as Record<string, unknown> | undefined || schoolAnalysis;

  const hasSchoolData = currentSchoolData && currentSchoolData.status === "completed";

  const sections = Object.entries(SECTION_TITLES).map(([key]) => {
    const content = narration?.[key] as string | undefined;
    return { key, content: content || "" };
  }).filter(s => s.content);

  const SCHOOL_META: Record<string, { label: string; icon: string; color: string }> = {
    ziping: { label: "传统子平法", icon: "☯", color: "var(--el-water)" },
    mangpai: { label: "盲派", icon: "👁", color: "#a855f7" },
    xinpai: { label: "新派", icon: "✧", color: "#22c55e" },
  };

  const schoolMeta = SCHOOL_META[school] || SCHOOL_META.ziping;

  return (
    <div style={{ width: "100%" }}>
      <div style={{
        maxWidth: 860,
        marginLeft: "auto",
        marginRight: "auto",
        marginBottom: 32,
        display: "flex",
        alignItems: "center",
        gap: 12,
        flexWrap: "wrap",
      }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
          命理解读
        </h2>
        <span style={{ fontWeight: 600, fontSize: 13, padding: "4px 12px", background: "var(--bg-secondary)", color: "var(--color-text-secondary)" }}>
          {sections.length} 维度
        </span>
        {hasSchoolData && (
          <span style={{ fontWeight: 600, fontSize: 13, padding: "4px 12px", background: `${schoolMeta.color}12`, color: schoolMeta.color }}>
            {schoolMeta.icon} {schoolMeta.label}
          </span>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
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
