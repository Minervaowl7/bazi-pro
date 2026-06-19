"use client";

interface Props {
  schoolAnalyses: Record<string, unknown>;
}

const SCHOOL_META: Record<string, { label: string; icon: string; color: string; bg: string }> = {
  ziping: { label: "传统子平法", icon: "☯", color: "var(--school-ziping)", bg: "color-mix(in srgb, var(--school-ziping) 12%, transparent)" },
  mangpai: { label: "盲派", icon: "👁", color: "var(--school-mangpai)", bg: "color-mix(in srgb, var(--school-mangpai) 12%, transparent)" },
  xinpai: { label: "新派", icon: "✧", color: "var(--school-xinpai)", bg: "color-mix(in srgb, var(--school-xinpai) 12%, transparent)" },
};

function ZipingColumn({ data }: { data: Record<string, unknown> }) {
  const pattern = data.pattern as { pattern?: string; confidence?: number; reason?: string } | undefined;
  const wangshuai = data.wangshuai as { verdict?: string } | undefined;
  const yongshen = data.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[] } | undefined;
  const breakConditions = data.break_conditions as Array<{ type?: string; severity?: string; detail?: string }> | undefined;
  const tiaohou = data.tiaohou as { has_tiaohou?: boolean; tiaohou_gan?: string[] } | undefined;

  return (
    <div className="space-y-4">
      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">旺衰</div>
        <div className="text-xs font-semibold text-[var(--ink)]">
          {wangshuai?.verdict || "—"}
        </div>
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">格局</div>
        <div className="text-xs font-semibold text-[var(--ink)]">
          {pattern?.pattern || "—"}
        </div>
        {pattern?.confidence !== undefined && (
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 rounded-full" style={{ height: 4, background: "var(--surface-2)" }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(pattern.confidence * 100, 100)}%`,
                  background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                }}
              />
            </div>
            <span className="text-[10px] tabular-nums text-[var(--text-3)]">
              {(pattern.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">用神</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用</span>
            <span className="text-xs">{yongshen?.yongshen || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.10)", color: "var(--success)", opacity: 0.8 }}>喜</span>
            <span className="text-xs">{(yongshen?.xishen || []).join(" ") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌</span>
            <span className="text-xs">{(yongshen?.jishen || []).join(" ") || "—"}</span>
          </div>
        </div>
      </div>

      {tiaohou?.has_tiaohou && (
        <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
          <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">调候</div>
          <div className="text-xs" style={{ color: "var(--warning)" }}>
            {(tiaohou.tiaohou_gan || []).join(" ")}
          </div>
        </div>
      )}

      {breakConditions && breakConditions.length > 0 && (
        <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
          <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">破格条件</div>
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
                  <span className="text-[10px] leading-relaxed text-[var(--text-3)]">
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
  const zuokong = data.zuokong as Record<string, Array<{ type?: string; description?: string }>> | undefined;
  const summary = data.summary as string | undefined;

  const allGong: Array<{ type?: string; description?: string }> = [];
  if (zuokong) {
    for (const gongList of Object.values(zuokong)) {
      if (Array.isArray(gongList)) allGong.push(...gongList);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">宾主</div>
        {(binzhu?.interpretations || []).length > 0 ? (
          <div className="space-y-1.5">
            {(binzhu?.interpretations || []).map((interp, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "color-mix(in srgb, var(--school-mangpai) 15%, transparent)", color: "var(--school-mangpai)" }}>
                  {interp.type}
                </span>
                <span className="text-xs text-[var(--text-2)]">{interp.meaning}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-[var(--text-3)]">宾主无明显交战</div>
        )}
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">体用</div>
        <div className="flex items-center gap-3 text-xs">
          <span>
            体 <span className="font-semibold" style={{ color: "var(--school-mangpai)" }}>{(tiyong?.ti || []).length}</span>
          </span>
          <span className="text-[var(--text-3)]">·</span>
          <span>
            用 <span className="font-semibold" style={{ color: "var(--school-mangpai)" }}>{(tiyong?.yong || []).length}</span>
          </span>
        </div>
        <div className="mt-2 flex items-center gap-2 text-[10px] text-[var(--text-3)]">
          <span>体力 {tiyong?.ti_strength?.toFixed(1) || 0}</span>
          <span>·</span>
          <span>用力 {tiyong?.yong_strength?.toFixed(1) || 0}</span>
        </div>
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">做功</div>
        {allGong.length > 0 ? (
          <div className="space-y-1.5">
            {allGong.slice(0, 5).map((g, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "color-mix(in srgb, var(--school-mangpai) 15%, transparent)", color: "var(--school-mangpai)" }}>
                  {g.type}
                </span>
                <span className="text-[10px] text-[var(--text-2)]">{g.description}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-[var(--text-3)]">暂无有效做功</div>
        )}
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">功力</div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold" style={{ color: "var(--school-mangpai)" }}>
            {gongli?.level || "—"}
          </span>
          <span className="text-[10px] text-[var(--text-3)]">
            {gongli?.score ?? "—"}分
          </span>
        </div>
        {gongli?.analysis && (
          <div className="mt-1.5 text-[10px] text-[var(--text-3)]">{gongli.analysis}</div>
        )}
      </div>

      {summary && (
        <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
          <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">总评</div>
          <div className="text-xs leading-relaxed text-[var(--text-2)]">{summary}</div>
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
      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">身扶判定</div>
        <div className="text-xs font-semibold" style={{ color: "var(--school-xinpai)" }}>
          {yongJi?.sheng_fu || "—"}
        </div>
        {yongJi?.reason && (
          <div className="mt-1 text-[10px] text-[var(--text-3)]">{yongJi.reason}</div>
        )}
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">用忌神</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(74,222,128,0.15)", color: "var(--success)" }}>用</span>
            <span className="text-xs">{(yongJi?.yongshen_name || []).join("、") || "—"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "rgba(248,113,113,0.15)", color: "var(--danger)" }}>忌</span>
            <span className="text-xs">{(yongJi?.jishen_name || []).join("、") || "—"}</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
        <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">空亡</div>
        {(kongwang?.kongwang_zhi || []).length > 0 ? (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              {(kongwang?.kongwang_zhi || []).map((zhi) => (
                <span
                  key={zhi}
                  className="text-xs font-semibold px-2 py-0.5 rounded-md"
                  style={{ background: "color-mix(in srgb, var(--school-xinpai) 12%, transparent)", color: "var(--school-xinpai)" }}
                >
                  {zhi}
                </span>
              ))}
            </div>
            {(kongwang?.affected || []).length > 0 && (
              <div className="text-[10px] text-[var(--text-3)]">
                影响柱位：{(kongwang?.affected || []).map((a) => a.position).join("、")}
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-[var(--text-3)]">无空亡</div>
        )}
      </div>

      {fanduan && (fanduan.total_conditions || 0) > 0 && (
        <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
          <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">反断条件</div>
          <div className="space-y-1.5">
            {(fanduan.conditions || []).map((c, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: "color-mix(in srgb, var(--school-xinpai) 15%, transparent)", color: "var(--school-xinpai)" }}>
                  {c.action}
                </span>
                <span className="text-[10px] text-[var(--text-2)]">{c.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary && (
        <div className="rounded-xl px-6 py-4 bg-[var(--surface-2)]">
          <div className="text-[10px] font-medium mb-2 text-[var(--text-3)]">总评</div>
          <div className="text-xs leading-relaxed text-[var(--text-2)]">
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
      <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-8 text-center">
        <p className="text-xs text-[var(--text-3)]">
          暂无流派对比数据
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <h2 className="text-base font-medium text-[var(--ink)]">
          全流派对比
        </h2>
        <span
          className="text-[10px] px-2.5 py-1 rounded-full font-medium"
          style={{ background: "var(--surface-2)", color: "var(--text-2)" }}
        >
          {columns.length} 派
        </span>
      </div>

      <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] overflow-hidden">
        <div
          className="grid overflow-x-auto"
          style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(200px, 1fr))` }}
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
                <div className="px-6 py-4 flex items-center gap-2.5 relative border-b border-[var(--border-subtle)] bg-[var(--surface-2)]">
                  <span
                    className="absolute top-0 left-0 right-0 h-[2px]"
                    style={{ background: meta.color }}
                  />
                  <span
                    className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
                    style={{ background: meta.bg, color: meta.color }}
                  >
                    {meta.icon}
                  </span>
                  <span className="text-xs font-semibold" style={{ color: meta.color }}>
                    {meta.label}
                  </span>
                </div>
                <div className="px-6 py-4">
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
