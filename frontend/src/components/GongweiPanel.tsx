"use client";

interface Props {
  result: Record<string, unknown>;
}

export default function GongweiPanel({ result }: Props) {
  const gongwei = result.gongwei as Record<string, string> | undefined;

  if (!gongwei || Object.keys(gongwei).length === 0) return null;

  const items = Object.entries(gongwei);

  return (
    <div
      className="rounded-2xl p-6"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <h3
        className="text-sm font-semibold mb-4"
        style={{ color: "var(--text-secondary)" }}
      >
        宫位信息
      </h3>
      <div className="grid grid-cols-3 gap-3">
        {items.map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl p-3 text-center"
            style={{ background: "var(--bg-hover)" }}
          >
            <div className="text-[10px] mb-1.5" style={{ color: "var(--text-muted)" }}>
              {label}
            </div>
            <div className="text-lg font-bold" style={{ color: "var(--accent)" }}>
              {value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
