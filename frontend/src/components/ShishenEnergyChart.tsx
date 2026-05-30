"use client";

const SHISHEN_GROUPS = [
  { label: "同我", items: ["比肩", "劫财"], wx: "同" },
  { label: "我生", items: ["食神", "伤官"], wx: "生" },
  { label: "我克", items: ["偏财", "正财"], wx: "克" },
  { label: "克我", items: ["七杀", "正官"], wx: "被克" },
  { label: "生我", items: ["偏印", "正印"], wx: "被生" },
];

const GROUP_COLORS = ["var(--earth)", "var(--wood)", "var(--fire)", "var(--metal)", "var(--water)"];

interface CangganItem {
  shishen?: string;
  [key: string]: unknown;
}

interface PillarDetail {
  shishen_gan?: string;
  shishen_zhi?: string;
  canggan?: CangganItem[];
  [key: string]: unknown;
}

interface Props {
  result: Record<string, unknown>;
}

export default function ShishenEnergyChart({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const pillars = shishen?.pillars || [];

  if (pillars.length === 0) return null;

  const counts: Record<string, number> = {};
  for (const p of pillars) {
    if (p.shishen_gan) counts[p.shishen_gan] = (counts[p.shishen_gan] || 0) + 1;
    if (p.shishen_zhi) counts[p.shishen_zhi] = (counts[p.shishen_zhi] || 0) + 1;
    for (const cg of p.canggan || []) {
      if (cg.shishen) counts[cg.shishen] = (counts[cg.shishen] || 0) + 0.5;
    }
  }

  const total = Math.max(1, Object.values(counts).reduce((a, b) => a + b, 0));

  return (
    <div
      className="rounded-2xl p-6"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <h3
        className="text-sm font-semibold mb-5"
        style={{ color: "var(--text-secondary)" }}
      >
        十神能量分布
      </h3>
      <div className="space-y-4">
        {SHISHEN_GROUPS.map((group, gi) => {
          const groupTotal = group.items.reduce((sum, item) => sum + (counts[item] || 0), 0);
          const groupPct = (groupTotal / total) * 100;
          const color = GROUP_COLORS[gi];

          return (
            <div key={group.label}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium" style={{ color }}>
                  {group.label}
                </span>
                <span className="text-[11px] tabular-nums" style={{ color: "var(--text-muted)" }}>
                  {groupPct.toFixed(0)}%
                </span>
              </div>
              <div
                className="h-5 rounded-md overflow-hidden flex"
                style={{ background: "var(--bg-secondary)" }}
              >
                {group.items.map((item, ii) => {
                  const val = counts[item] || 0;
                  const pct = (val / total) * 100;
                  if (pct === 0) return null;
                  return (
                    <div
                      key={item}
                      className="h-full flex items-center justify-center text-[9px] font-medium transition-all duration-500"
                      style={{
                        width: `${pct}%`,
                        background: color,
                        opacity: ii === 0 ? 0.85 : 0.6,
                        color: "var(--bg-primary)",
                      }}
                      title={`${item}: ${pct.toFixed(1)}%`}
                    >
                      {pct > 8 ? item : ""}
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-3 mt-1">
                {group.items.map((item) => (
                  <span key={item} className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                    {item} {((counts[item] || 0) / total * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
