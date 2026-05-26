"use client";

interface SchoolPanelProps {
  result: Record<string, unknown>;
}

export default function SchoolPanel({ result }: SchoolPanelProps) {
  const pattern = result.pattern as { pattern?: string; confidence?: number; reason?: string; layer?: number; type?: string } | undefined;
  const yongshen = result.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[]; note?: string; confidence?: number; pattern_basis?: string } | undefined;
  const strength = result.strength as { wangshuai?: { verdict?: string }; deling?: { status?: string; score?: number }; dedi?: { score?: number }; deshi?: { score?: number } } | undefined;
  const relations = result.relations as Array<{ type?: string; elements?: string[]; description?: string }> | undefined;
  const retrieval = result.retrieval as { results?: Array<{ source?: string; text?: string; score?: number }> } | undefined;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-lg font-medium">子平传统 · 分析解读</h2>
        <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-hover)] text-[var(--accent)]">
          子平
        </span>
      </div>

      {/* Pattern */}
      <Section title="格局判定">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-[var(--accent)] font-medium text-base">{pattern?.pattern || "—"}</span>
            {pattern?.confidence != null && (
              <ConfidenceBadge value={pattern.confidence} />
            )}
          </div>
          {pattern?.reason && (
            <p className="text-sm text-[var(--text-secondary)]">{pattern.reason}</p>
          )}
          {pattern?.layer != null && (
            <p className="text-xs text-[var(--text-muted)]">筛查层级: L{pattern.layer} · 类型: {pattern.type || "—"}</p>
          )}
        </div>
      </Section>

      {/* Strength */}
      <Section title="旺衰判定">
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-[var(--bg-secondary)] rounded-lg p-3 text-center">
            <div className="text-xs text-[var(--text-muted)] mb-1">得令</div>
            <div className="text-[var(--text-primary)]">{strength?.deling?.status || "—"}</div>
            <div className="text-xs text-[var(--text-muted)]">分: {strength?.deling?.score ?? "—"}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-3 text-center">
            <div className="text-xs text-[var(--text-muted)] mb-1">得地</div>
            <div className="text-[var(--text-primary)]">{typeof strength?.dedi?.score === "number" ? strength.dedi.score.toFixed(1) : "—"}</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-3 text-center">
            <div className="text-xs text-[var(--text-muted)] mb-1">得势</div>
            <div className="text-[var(--text-primary)]">{typeof strength?.deshi?.score === "number" ? strength.deshi.score.toFixed(1) : "—"}</div>
          </div>
        </div>
        <div className="mt-2 text-sm">
          综合判定: <span className="text-[var(--accent)] font-medium">{strength?.wangshuai?.verdict || "—"}</span>
        </div>
      </Section>

      {/* Yongshen */}
      <Section title="喜用神">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-[var(--accent)] font-medium">用神: {yongshen?.yongshen || "—"}</span>
            {yongshen?.confidence != null && <ConfidenceBadge value={yongshen.confidence} />}
          </div>
          {yongshen?.xishen && yongshen.xishen.length > 0 && (
            <p className="text-sm text-[var(--text-secondary)]">喜神: {yongshen.xishen.join("、")}</p>
          )}
          {yongshen?.jishen && yongshen.jishen.length > 0 && (
            <p className="text-sm text-[var(--text-secondary)]">忌神: {yongshen.jishen.join("、")}</p>
          )}
          {yongshen?.pattern_basis && (
            <p className="text-xs text-[var(--text-muted)]">依据: {yongshen.pattern_basis}</p>
          )}
          {yongshen?.note && (
            <p className="text-xs text-[var(--text-muted)]">{yongshen.note}</p>
          )}
        </div>
      </Section>

      {/* Relations */}
      {relations && relations.length > 0 && (
        <Section title="刑冲合害">
          <div className="space-y-1.5">
            {relations.map((rel, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="px-1.5 py-0.5 text-xs rounded bg-[var(--bg-hover)] text-[var(--warning)]">
                  {rel.type || "关系"}
                </span>
                <span className="text-[var(--text-secondary)]">
                  {rel.elements?.join(" ") || ""} {rel.description || ""}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Classical citations */}
      {retrieval?.results && retrieval.results.length > 0 && (
        <Section title="古籍引证">
          <div className="space-y-2">
            {retrieval.results.slice(0, 3).map((item, i) => (
              <div key={i} className="bg-[var(--bg-secondary)] rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-[var(--accent)]">{item.source || "古籍"}</span>
                  {item.score != null && (
                    <span className="text-xs text-[var(--text-muted)]">相关度: {(item.score * 100).toFixed(0)}%</span>
                  )}
                </div>
                <p className="text-sm text-[var(--text-secondary)] line-clamp-2">{item.text || ""}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4 last:mb-0">
      <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  );
}

function ConfidenceBadge({ value }: { value: number }) {
  let color = "var(--danger)";
  let label = "低";
  if (value >= 0.85) {
    color = "var(--success)";
    label = "高";
  } else if (value >= 0.6) {
    color = "var(--warning)";
    label = "中";
  }
  return (
    <span className="px-1.5 py-0.5 text-xs rounded-full" style={{ backgroundColor: `${color}20`, color }}>
      {label} {(value * 100).toFixed(0)}%
    </span>
  );
}
