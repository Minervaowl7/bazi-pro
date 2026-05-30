"use client";

interface Props {
  schoolAnalyses: Record<string, unknown>;
}

const SCHOOL_META: Record<string, { label: string; icon: string; color: string }> = {
  ziping: { label: "传统子平法", icon: "☯", color: "var(--accent)" },
  mangpai: { label: "盲派", icon: "👁", color: "#a855f7" },
  xinpai: { label: "新派", icon: "✧", color: "#22c55e" },
};

function ZipingColumn({ data }: { data: Record<string, unknown> }) {
  const pattern = data.pattern as { pattern?: string; confidence?: number; reason?: string } | undefined;
  const wangshuai = data.wangshuai as { verdict?: string } | undefined;
  const yongshen = data.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[] } | undefined;
  const breakConditions = data.break_conditions as Array<{ type?: string; severity?: string; detail?: string }> | undefined;
  const tiaohou = data.tiaohou as { has_tiaohou?: boolean; tiaohou_gan?: string[] } | undefined;

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>旺衰</div>
        <div className="text-sm font-semibold" style={{ color: "var(--accent)" }}>
          {wangshuai?.verdict || "—"}
        </div>
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>格局</div>
        <div className="text-sm font-semibold" style={{ color: "var(--accent)" }}>
          {pattern?.pattern || "—"}
        </div>
        {pattern?.confidence !== undefined && (
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 rounded-full" style={{ height: 4, background: "var(--bg-hover)" }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(pattern.confidence * 100, 100)}%`,
                  background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                }}
              />
            </div>
            <span className="text-[10px] tabular-nums" style={{ color: "var(--text-muted)" }}>
              {(pattern.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>用神</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用</span>
            <span className="text-sm">{yongshen?.yongshen || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.10)", color: "var(--success)", opacity: 0.8 }}>喜</span>
            <span className="text-sm">{(yongshen?.xishen || []).join(" ") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌</span>
            <span className="text-sm">{(yongshen?.jishen || []).join(" ") || "—"}</span>
          </div>
        </div>
      </div>

      {tiaohou?.has_tiaohou && (
        <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
          <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>调候</div>
          <div className="text-sm" style={{ color: "var(--warning)" }}>
            {(tiaohou.tiaohou_gan || []).join(" ")}
          </div>
        </div>
      )}

      {breakConditions && breakConditions.length > 0 && (
        <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
          <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>破格条件</div>
          <div className="space-y-1.5">
            {breakConditions.map((bc, i) => (
              <div key={i} className="flex items-start gap-1.5">
                <span
                  className="text-[10px] px-1 py-0.5 rounded shrink-0 font-medium"
                  style={{
                    background: bc.severity === "high" ? "rgba(248,113,113,0.15)" : "rgba(251,191,36,0.15)",
                    color: bc.severity === "high" ? "var(--danger)" : "var(--warning)",
                  }}
                >
                  {bc.type}
                </span>
                {bc.detail && (
                  <span className="text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    {bc.detail}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MangpaiColumn({ data }: { data: Record<string, unknown> }) {
  const binzhu = data.binzhu as { interpretations?: Array<{ type?: string; meaning?: string }> } | undefined;
  const tiyong = data.tiyong as { ti?: Array<{ shishen?: string; gan?: string }>; yong?: Array<{ shishen?: string; gan?: string }>; ti_strength?: number; yong_strength?: number } | undefined;
  const gongli = data.gongli as { level?: string; score?: number; analysis?: string } | undefined;
  const zuogong = data.zuogong as Record<string, Array<{ type?: string; description?: string }>> | undefined;
  const summary = data.summary as string | undefined;

  const allGong: Array<{ type?: string; description?: string }> = [];
  if (zuogong) {
    for (const gongList of Object.values(zuogong)) {
      if (Array.isArray(gongList)) allGong.push(...gongList);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>宾主</div>
        {(binzhu?.interpretations || []).length > 0 ? (
          <div className="space-y-1.5">
            {(binzhu?.interpretations || []).map((interp, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
                  {interp.type}
                </span>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{interp.meaning}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm" style={{ color: "var(--text-muted)" }}>宾主无明显交战</div>
        )}
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>体用</div>
        <div className="flex items-center gap-3 text-sm">
          <span>
            体 <span className="font-semibold" style={{ color: "#a855f7" }}>{(tiyong?.ti || []).length}</span>
          </span>
          <span style={{ color: "var(--text-muted)" }}>·</span>
          <span>
            用 <span className="font-semibold" style={{ color: "#a855f7" }}>{(tiyong?.yong || []).length}</span>
          </span>
        </div>
        <div className="mt-2 flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>体力 {tiyong?.ti_strength?.toFixed(1) || 0}</span>
          <span>·</span>
          <span>用力 {tiyong?.yong_strength?.toFixed(1) || 0}</span>
        </div>
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>做功</div>
        {allGong.length > 0 ? (
          <div className="space-y-1.5">
            {allGong.slice(0, 5).map((g, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
                  {g.type}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{g.description}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm" style={{ color: "var(--text-muted)" }}>暂无有效做功</div>
        )}
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>功力</div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold" style={{ color: "#a855f7" }}>
            {gongli?.level || "—"}
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {gongli?.score ?? "—"}分
          </span>
        </div>
        {gongli?.analysis && (
          <div className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>{gongli.analysis}</div>
        )}
      </div>

      {summary && (
        <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
          <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>总评</div>
          <div className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{summary}</div>
        </div>
      )}
    </div>
  );
}

function XinpaiColumn({ data }: { data: Record<string, unknown> }) {
  const yongJi = data.yong_ji as { sheng_fu?: string; yongshen?: string[]; yongshen_name?: string[]; jishen_name?: string[]; reason?: string } | undefined;
  const kongwang = data.kongwang as { kongwang_zhi?: string[]; affected?: Array<{ position?: string; zhi?: string }> } | undefined;
  const fanduan = data.fanduan as { conditions?: Array<{ type?: string; description?: string; action?: string }>; total_conditions?: number } | undefined;
  const summary = data.summary as { yongshen?: string; jishen?: string; kongwang?: string; fanduan_count?: number; advice?: string } | undefined;

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>身扶判定</div>
        <div className="text-sm font-semibold" style={{ color: "#22c55e" }}>
          {yongJi?.sheng_fu || "—"}
        </div>
        {yongJi?.reason && (
          <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>{yongJi.reason}</div>
        )}
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>用忌神</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用</span>
            <span className="text-sm">{(yongJi?.yongshen_name || []).join("、") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌</span>
            <span className="text-sm">{(yongJi?.jishen_name || []).join("、") || "—"}</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
        <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>空亡</div>
        {(kongwang?.kongwang_zhi || []).length > 0 ? (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              {(kongwang?.kongwang_zhi || []).map((zhi) => (
                <span
                  key={zhi}
                  className="text-sm font-semibold px-2 py-0.5 rounded-md"
                  style={{ background: "rgba(34,197,94,0.12)", color: "#22c55e" }}
                >
                  {zhi}
                </span>
              ))}
            </div>
            {(kongwang?.affected || []).length > 0 && (
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                影响柱位：{(kongwang?.affected || []).map((a) => a.position).join("、")}
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm" style={{ color: "var(--text-muted)" }}>无空亡</div>
        )}
      </div>

      {fanduan && (fanduan.total_conditions || 0) > 0 && (
        <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
          <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>反断条件</div>
          <div className="space-y-1.5">
            {(fanduan.conditions || []).map((c, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(34,197,94,0.15)", color: "#22c55e" }}>
                  {c.action}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{c.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary && (
        <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)" }}>
          <div className="text-xs font-medium mb-2" style={{ color: "var(--text-muted)" }}>总评</div>
          <div className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {summary.advice}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SchoolComparePanel({ schoolAnalyses }: Props) {
  const zipingData = schoolAnalyses.ziping as Record<string, unknown> | undefined;
  const mangpaiData = schoolAnalyses.mangpai as Record<string, unknown> | undefined;
  const xinpaiData = schoolAnalyses.xinpai as Record<string, unknown> | undefined;

  const columns = [
    { key: "ziping", data: zipingData, Component: ZipingColumn },
    { key: "mangpai", data: mangpaiData, Component: MangpaiColumn },
    { key: "xinpai", data: xinpaiData, Component: XinpaiColumn },
  ].filter((col): col is typeof col & { data: Record<string, unknown> } => col.data?.status === "completed");

  if (columns.length === 0) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          暂无流派对比数据
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <h2 className="text-lg font-semibold" style={{ color: "var(--accent)" }}>
          全流派对比
        </h2>
        <span
          className="text-xs px-2.5 py-1 rounded-full font-medium"
          style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
        >
          {columns.length} 派
        </span>
      </div>

      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <div
          className="grid"
          style={{ gridTemplateColumns: `repeat(${columns.length}, 1fr)` }}
        >
          {columns.map((col, i) => {
            const meta = SCHOOL_META[col.key];
            return (
              <div
                key={col.key}
                style={{
                  borderRight: i < columns.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <div
                  className="px-4 py-3.5 flex items-center gap-2.5 relative"
                  style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-hover)" }}
                >
                  <span
                    className="absolute top-0 left-0 right-0 h-[2px]"
                    style={{ background: meta.color }}
                  />
                  <span
                    className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
                    style={{ background: `${meta.color}20`, color: meta.color }}
                  >
                    {meta.icon}
                  </span>
                  <span className="text-sm font-semibold" style={{ color: meta.color }}>
                    {meta.label}
                  </span>
                </div>
                <div className="p-4">
                  <col.Component data={col.data} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
