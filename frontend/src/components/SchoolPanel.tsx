"use client";

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

const SCHOOL_META: Record<string, { label: string; icon: string; color: string }> = {
  ziping: { label: "传统子平法", icon: "☯", color: "var(--water)" },
  mangpai: { label: "盲派", icon: "👁", color: "#a855f7" },
  xinpai: { label: "新派", icon: "✧", color: "#22c55e" },
};

function SectionCard({ sectionKey, content, index }: { sectionKey: string; content: string; index: number }) {
  const meta = SECTION_TITLES[sectionKey];
  if (!meta || !content) return null;

  return (
    <div
      className="rounded-xl p-6 animate-fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        animationDelay: `${index * 60}ms`,
      }}
    >
      <div className="flex items-center gap-2.5 mb-4">
        <span className="text-base">{meta.icon}</span>
        <h3
          className="text-sm font-medium"
          style={{ color: "var(--text-primary)" }}
        >
          {meta.label}
        </h3>
      </div>
      <div
        className="text-sm leading-relaxed whitespace-pre-wrap space-y-3"
        style={{ color: "var(--text-secondary)" }}
      >
        {content.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function SchoolSectionCard({ title, icon, color, children, index }: {
  title: string; icon: string; color: string; children: React.ReactNode; index: number;
}) {
  return (
    <div
      className="rounded-xl p-6 animate-fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderLeft: `3px solid ${color}`,
        animationDelay: `${index * 60}ms`,
      }}
    >
      <div className="flex items-center gap-2.5 mb-4">
        <span className="text-base">{icon}</span>
        <h3 className="text-sm font-medium" style={{ color }}>
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

function ZipingSchoolView({ data, baseIndex }: { data: Record<string, unknown>; baseIndex: number }) {
  const pattern = data.pattern as { pattern?: string; confidence?: number; reason?: string; break_conditions?: Array<{ type?: string; severity?: string; detail?: string }> } | undefined;
  const wangshuai = data.wangshuai as { verdict?: string } | undefined;
  const yongshen = data.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[]; trace?: { method?: string; reason?: string } } | undefined;
  const breakConditions = pattern?.break_conditions || (data.break_conditions as Array<{ type?: string; severity?: string; detail?: string }> | undefined) || [];
  const dayunVerdict = data.dayun_verdict as Array<{ step?: number; gan?: string; zhi?: string; shishen?: string; verdict?: string; detail?: string }> | undefined;

  return (
    <>
      <SchoolSectionCard title="子平格局判定" icon="🏛" color="var(--water)" index={baseIndex}>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold" style={{ color: "var(--water)" }}>{pattern?.pattern || "—"}</span>
            {pattern?.confidence !== undefined && (
              <div className="flex items-center gap-2 flex-1">
                <div className="flex-1 rounded-full" style={{ height: 4, background: "var(--bg-hover)" }}>
                  <div className="h-full rounded-full" style={{
                    width: `${Math.min(pattern.confidence * 100, 100)}%`,
                    background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                  }} />
                </div>
                <span className="text-[10px] tabular-nums" style={{ color: "var(--text-muted)" }}>
                  {(pattern.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
          {pattern?.reason && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>{pattern.reason}</p>
          )}
          {wangshuai?.verdict && (
            <p className="text-sm">旺衰：<span className="font-semibold" style={{ color: "var(--text-primary)" }}>{wangshuai.verdict}</span></p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="子平用神（破格调整后）" icon="✦" color="var(--water)" index={baseIndex + 1}>
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用神</span>
            <span className="text-sm font-semibold">{yongshen?.yongshen || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.10)", color: "var(--success)", opacity: 0.8 }}>喜神</span>
            <span className="text-sm">{(yongshen?.xishen || []).join("、") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌神</span>
            <span className="text-sm">{(yongshen?.jishen || []).join("、") || "—"}</span>
          </div>
          {yongshen?.trace?.reason && (
            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>推导：{yongshen.trace.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      {breakConditions.length > 0 && (
        <SchoolSectionCard title="破格条件" icon="⚠" color="var(--warning)" index={baseIndex + 2}>
          <div className="space-y-2">
            {breakConditions.map((bc, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded shrink-0 font-medium" style={{
                  background: bc.severity === "high" ? "rgba(248,113,113,0.15)" : "rgba(251,191,36,0.15)",
                  color: bc.severity === "high" ? "var(--danger)" : "var(--warning)",
                }}>
                  {bc.type}
                </span>
                {bc.detail && <span className="text-xs" style={{ color: "var(--text-muted)" }}>{bc.detail}</span>}
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（子平法）" icon="🌊" color="var(--water)" index={baseIndex + 3}>
          <div className="space-y-1.5">
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="font-mono text-xs w-8 shrink-0" style={{ color: "var(--text-muted)" }}>{d.step}</span>
                <span className="font-semibold w-6 shrink-0">{d.gan}{d.zhi}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{
                  background: d.verdict === "吉" ? "rgba(74,222,128,0.15)" : d.verdict === "凶" ? "rgba(248,113,113,0.15)" : "rgba(251,191,36,0.15)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>{d.detail}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}
    </>
  );
}

function MangpaiSchoolView({ data, baseIndex }: { data: Record<string, unknown>; baseIndex: number }) {
  const binzhu = data.binzhu as { interpretations?: Array<{ type?: string; meaning?: string }> } | undefined;
  const tiyong = data.tiyong as { ti?: Array<{ shishen?: string; gan?: string }>; yong?: Array<{ shishen?: string; gan?: string }>; ti_strength?: number; yong_strength?: number } | undefined;
  const gongli = data.gongli as { level?: string; score?: number; analysis?: string } | undefined;
  const zuogong = data.zuogong as Record<string, Array<{ type?: string; description?: string }>> | undefined;
  const summary = data.summary as string | undefined;
  const yingqi = data.yingqi as { triggers?: Array<{ type?: string; description?: string }> } | undefined;

  const allGong: Array<{ type?: string; description?: string }> = [];
  if (zuogong) {
    for (const gongList of Object.values(zuogong)) {
      if (Array.isArray(gongList)) allGong.push(...gongList);
    }
  }

  return (
    <>
      <SchoolSectionCard title="宾主分析" icon="👥" color="#a855f7" index={baseIndex}>
        {(binzhu?.interpretations || []).length > 0 ? (
          <div className="space-y-2">
            {(binzhu?.interpretations || []).map((interp, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
                  {interp.type}
                </span>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{interp.meaning}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>宾主无明显交战</p>
        )}
      </SchoolSectionCard>

      <SchoolSectionCard title="体用分析" icon="⚖" color="#a855f7" index={baseIndex + 1}>
        <div className="space-y-2">
          <div className="flex items-center gap-4 text-sm">
            <span>体 <span className="font-semibold" style={{ color: "#a855f7" }}>{(tiyong?.ti || []).map(t => t.gan).join(" ") || "无"}</span></span>
            <span style={{ color: "var(--text-muted)" }}>vs</span>
            <span>用 <span className="font-semibold" style={{ color: "#a855f7" }}>{(tiyong?.yong || []).map(t => t.gan).join(" ") || "无"}</span></span>
          </div>
          <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
            <span>体力 {tiyong?.ti_strength?.toFixed(1) || 0}</span>
            <span>·</span>
            <span>用力 {tiyong?.yong_strength?.toFixed(1) || 0}</span>
          </div>
        </div>
      </SchoolSectionCard>

      {allGong.length > 0 && (
        <SchoolSectionCard title="做功分析" icon="⚙" color="#a855f7" index={baseIndex + 2}>
          <div className="space-y-2">
            {allGong.slice(0, 6).map((g, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
                  {g.type}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{g.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="功力评定" icon="📊" color="#a855f7" index={baseIndex + 3}>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: "#a855f7" }}>{gongli?.level || "—"}</span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>{gongli?.score ?? "—"}分</span>
          </div>
          {gongli?.analysis && (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>{gongli.analysis}</p>
          )}
        </div>
      </SchoolSectionCard>

      {yingqi && (yingqi.triggers || []).length > 0 && (
        <SchoolSectionCard title="应期提示" icon="🕐" color="#a855f7" index={baseIndex + 4}>
          <div className="space-y-1.5">
            {(yingqi.triggers || []).map((t, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
                  {t.type}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{t.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary && (
        <SchoolSectionCard title="盲派总评" icon="👁" color="#a855f7" index={baseIndex + 5}>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{summary}</p>
        </SchoolSectionCard>
      )}
    </>
  );
}

function XinpaiSchoolView({ data, baseIndex }: { data: Record<string, unknown>; baseIndex: number }) {
  const yongJi = data.yong_ji as { sheng_fu?: string; yongshen?: string[]; yongshen_name?: string[]; jishen_name?: string[]; reason?: string } | undefined;
  const kongwang = data.kongwang as { kongwang_zhi?: string[]; affected?: Array<{ position?: string; zhi?: string }> } | undefined;
  const baishen = data.baishen as { replacements?: Record<string, { original?: string; replacement?: string; reason?: string }> } | undefined;
  const fanduan = data.fanduan as { conditions?: Array<{ type?: string; description?: string; action?: string }>; total_conditions?: number } | undefined;
  const summary = data.summary as { yongshen?: string; jishen?: string; kongwang?: string; fanduan_count?: number; advice?: string } | undefined;
  const dayunVerdict = data.dayun_verdict as Array<{ step?: number; gan?: string; zhi?: string; verdict?: string; detail?: string }> | undefined;

  return (
    <>
      <SchoolSectionCard title="身扶判定" icon="⚖" color="#22c55e" index={baseIndex}>
        <div className="space-y-2">
          <span className="text-sm font-semibold" style={{ color: "#22c55e" }}>{yongJi?.sheng_fu || "—"}</span>
          {yongJi?.reason && (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>{yongJi.reason}</p>
          )}
        </div>
      </SchoolSectionCard>

      <SchoolSectionCard title="新派用忌神" icon="✦" color="#22c55e" index={baseIndex + 1}>
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用神</span>
            <span className="text-sm font-semibold">{(yongJi?.yongshen_name || []).join("、") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌神</span>
            <span className="text-sm">{(yongJi?.jishen_name || []).join("、") || "—"}</span>
          </div>
        </div>
      </SchoolSectionCard>

      {baishen && baishen.replacements && Object.keys(baishen.replacements).length > 0 && (
        <SchoolSectionCard title="百神论替换" icon="🔄" color="#22c55e" index={baseIndex + 2}>
          <div className="space-y-2">
            {Object.entries(baishen.replacements).map(([key, val], i) => {
              const v = val as { original?: string; replacement?: string; reason?: string };
              return (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{ background: "rgba(34,197,94,0.15)", color: "#22c55e" }}>
                    {v.original || key}
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>→ {v.replacement}{v.reason ? `（${v.reason}）` : ""}</span>
                </div>
              );
            })}
          </div>
        </SchoolSectionCard>
      )}

      <SchoolSectionCard title="空亡论" icon="◯" color="#22c55e" index={baseIndex + 3}>
        {(kongwang?.kongwang_zhi || []).length > 0 ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {(kongwang?.kongwang_zhi || []).map((zhi) => (
                <span key={zhi} className="text-sm font-semibold px-2 py-0.5 rounded-md" style={{ background: "rgba(34,197,94,0.12)", color: "#22c55e" }}>
                  {zhi}
                </span>
              ))}
            </div>
            {(kongwang?.affected || []).length > 0 && (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                影响柱位：{(kongwang?.affected || []).map(a => a.position).join("、")}
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>无空亡</p>
        )}
      </SchoolSectionCard>

      {fanduan && (fanduan.total_conditions || 0) > 0 && (
        <SchoolSectionCard title="反断论" icon="↕" color="#22c55e" index={baseIndex + 4}>
          <div className="space-y-2">
            {(fanduan.conditions || []).map((c, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{ background: "rgba(34,197,94,0.15)", color: "#22c55e" }}>
                  {c.action}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{c.description}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {dayunVerdict && dayunVerdict.length > 0 && (
        <SchoolSectionCard title="大运吉凶（新派）" icon="🌊" color="#22c55e" index={baseIndex + 5}>
          <div className="space-y-1.5">
            {dayunVerdict.slice(0, 8).map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="font-mono text-xs w-8 shrink-0" style={{ color: "var(--text-muted)" }}>{d.step}</span>
                <span className="font-semibold w-6 shrink-0">{d.gan}{d.zhi}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0" style={{
                  background: d.verdict === "吉" ? "rgba(74,222,128,0.15)" : d.verdict === "凶" ? "rgba(248,113,113,0.15)" : "rgba(251,191,36,0.15)",
                  color: d.verdict === "吉" ? "var(--success)" : d.verdict === "凶" ? "var(--danger)" : "var(--warning)",
                }}>{d.verdict}</span>
                <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>{d.detail}</span>
              </div>
            ))}
          </div>
        </SchoolSectionCard>
      )}

      {summary?.advice && (
        <SchoolSectionCard title="新派总评" icon="✧" color="#22c55e" index={baseIndex + 6}>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{summary.advice}</p>
        </SchoolSectionCard>
      )}
    </>
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

  const schoolMeta = SCHOOL_META[school] || SCHOOL_META.ziping;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 mb-2">
        <h2 className="text-base font-medium" style={{ color: "var(--text-primary)" }}>
          命理解读
        </h2>
        <span className="text-xs px-2.5 py-1 rounded-full font-medium" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
          {sections.length} 维度
        </span>
        {hasSchoolData && (
          <span className="text-xs px-2.5 py-1 rounded-full font-medium" style={{ background: `${schoolMeta.color}15`, color: schoolMeta.color }}>
            {schoolMeta.icon} {schoolMeta.label}
          </span>
        )}
      </div>

      <div className="space-y-5">
        {sections.map((s, i) => (
          <SectionCard key={s.key} sectionKey={s.key} content={s.content} index={i} />
        ))}

        {hasSchoolData && school === "ziping" && (
          <ZipingSchoolView data={currentSchoolData} baseIndex={sections.length} />
        )}
        {hasSchoolData && school === "mangpai" && (
          <MangpaiSchoolView data={currentSchoolData} baseIndex={sections.length} />
        )}
        {hasSchoolData && school === "xinpai" && (
          <XinpaiSchoolView data={currentSchoolData} baseIndex={sections.length} />
        )}
      </div>
    </div>
  );
}
