"use client";

interface Narration {
  overview?: string;
  strength?: string;
  pattern?: string;
  yongshen?: string;
  tiaohou?: string;
  elements?: string;
  relations?: string;
  personality?: string;
  career?: string;
  citations?: Array<{ source: string; text: string; relevance?: string }>;
}

interface SchoolPanelProps {
  result: Record<string, unknown>;
  narration?: Narration;
}

export default function SchoolPanel({ result, narration }: SchoolPanelProps) {
  const pattern = result.pattern as { pattern?: string; confidence?: number } | undefined;
  const retrieval = result.retrieval as { results?: Array<{ source?: string; text?: string; score?: number }> } | undefined;

  if (narration && narration.overview) {
    return <NarratedPanel narration={narration} retrieval={retrieval} pattern={pattern} />;
  }

  return <RawDataPanel result={result} />;
}

function NarratedPanel({
  narration,
  retrieval,
  pattern,
}: {
  narration: Narration;
  retrieval?: { results?: Array<{ source?: string; text?: string; score?: number }> };
  pattern?: { pattern?: string; confidence?: number };
}) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-lg font-medium">命理解读</h2>
        {pattern?.confidence != null && (
          <ConfidenceBadge value={pattern.confidence} />
        )}
      </div>

      {narration.overview && (
        <div className="mb-4 p-3 bg-[var(--bg-secondary)] rounded-lg border-l-2 border-[var(--accent)]">
          <p className="text-sm text-[var(--text-primary)] leading-relaxed">{narration.overview}</p>
        </div>
      )}

      {narration.strength && (
        <NarrationSection title="旺衰判定" text={narration.strength} />
      )}

      {narration.pattern && (
        <NarrationSection title="格局判定" text={narration.pattern} />
      )}

      {narration.yongshen && (
        <NarrationSection title="喜用神" text={narration.yongshen} />
      )}

      {narration.tiaohou && (
        <NarrationSection title="调候分析" text={narration.tiaohou} />
      )}

      {narration.elements && (
        <NarrationSection title="五行力量" text={narration.elements} mono />
      )}

      {narration.relations && (
        <NarrationSection title="刑冲合害" text={narration.relations} />
      )}

      {narration.personality && (
        <NarrationSection title="性格特质" text={narration.personality} />
      )}

      {narration.career && (
        <NarrationSection title="事业方向" text={narration.career} />
      )}

      {/* Classical citations */}
      {narration.citations && narration.citations.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2">古籍引证</h3>
          <div className="space-y-2">
            {narration.citations.map((cite, i) => (
              <div key={i} className="bg-[var(--bg-secondary)] rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-[var(--accent)]">{cite.source}</span>
                  {cite.relevance && (
                    <span className="text-xs text-[var(--text-muted)]">相关度 {cite.relevance}</span>
                  )}
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{cite.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback: show retrieval results if no narrator citations */}
      {(!narration.citations || narration.citations.length === 0) &&
        retrieval?.results && retrieval.results.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2">古籍引证</h3>
          <div className="space-y-2">
            {retrieval.results.slice(0, 3).map((item, i) => (
              <div key={i} className="bg-[var(--bg-secondary)] rounded-lg p-3">
                <span className="text-xs text-[var(--accent)]">{item.source || "古籍"}</span>
                <p className="text-sm text-[var(--text-secondary)] mt-1 leading-relaxed">{item.text || ""}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function NarrationSection({ title, text, mono }: { title: string; text: string; mono?: boolean }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2">{title}</h3>
      <div className={`text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line ${mono ? "font-mono text-xs" : ""}`}>
        {text}
      </div>
    </div>
  );
}

function RawDataPanel({ result }: { result: Record<string, unknown> }) {
  const pattern = result.pattern as { pattern?: string; confidence?: number; reason?: string } | undefined;
  const yongshen = result.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[] } | undefined;
  const strength = result.strength as { wangshuai?: { verdict?: string } } | undefined;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <h2 className="text-lg font-medium mb-4">分析结果</h2>
      <div className="space-y-3 text-sm text-[var(--text-secondary)]">
        {strength?.wangshuai?.verdict && <p>旺衰: {strength.wangshuai.verdict}</p>}
        {pattern?.pattern && <p>格局: {pattern.pattern}</p>}
        {pattern?.reason && <p className="text-xs text-[var(--text-muted)]">{pattern.reason}</p>}
        {yongshen?.yongshen && <p>用神: {yongshen.yongshen}</p>}
        {yongshen?.xishen && <p>喜神: {yongshen.xishen.join("、")}</p>}
        {yongshen?.jishen && <p>忌神: {yongshen.jishen.join("、")}</p>}
      </div>
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
      置信度{label}
    </span>
  );
}
