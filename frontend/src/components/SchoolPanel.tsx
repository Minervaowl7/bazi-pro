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

function SectionCard({ sectionKey, content, index }: { sectionKey: string; content: string; index: number }) {
  const meta = SECTION_TITLES[sectionKey];
  if (!meta || !content) return null;

  return (
    <div
      className="rounded-r-xl p-6 animate-fade-in"
      style={{
        background: "var(--bg-card)",
        borderLeft: "2px solid var(--accent)",
        animationDelay: `${index * 80}ms`,
      }}
    >
      <div className="flex items-center gap-2.5 mb-4">
        <span className="text-base">{meta.icon}</span>
        <h3
          className="text-base font-semibold"
          style={{ color: "var(--accent)" }}
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

export default function SchoolPanel({ narration }: Props) {
  if (!narration) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          暂无解读内容
        </p>
      </div>
    );
  }

  const sections = Object.entries(SECTION_TITLES).map(([key]) => {
    const content = narration[key] as string | undefined;
    return { key, content: content || "" };
  }).filter(s => s.content);

  if (sections.length === 0) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          暂无解读内容
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <h2
          className="text-lg font-semibold"
          style={{ color: "var(--accent)" }}
        >
          命理解读
        </h2>
        <span
          className="text-xs px-2.5 py-1 rounded-full font-medium"
          style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
        >
          {sections.length} 维度
        </span>
      </div>
      <div className="space-y-4">
        {sections.map((s, i) => (
          <SectionCard key={s.key} sectionKey={s.key} content={s.content} index={i} />
        ))}
      </div>
    </div>
  );
}
