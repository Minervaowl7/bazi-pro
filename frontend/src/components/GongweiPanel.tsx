"use client";

interface Props { result: Record<string,unknown>; }

export default function GongweiPanel({ result }: Props) {
  const gongwei = result.gongwei as Record<string, string> | undefined;
  if (!gongwei || Object.keys(gongwei).length === 0) return null;

  const items = Object.entries(gongwei);

  return (
    <section className="card">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>宫位信息</h3>
      </div>
      <div className="p-7 grid grid-cols-2 sm:grid-cols-3 gap-5">
        {items.map(([label, value]) => (
          <div key={label} className="text-center p-5 rounded-xl" style={{ background: "var(--surface-2)" }}>
            <div className="mb-2 font-semibold text-xs uppercase tracking-[0.08em]" style={{ color: "var(--text-4)" }}>{label}</div>
            <div className="font-bold text-[22px]" style={{ fontFamily: "var(--font-display)" }}>{value}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
