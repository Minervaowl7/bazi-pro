"use client";

const SHISHEN_GROUPS = [
  { label: "同我", items: ["比肩", "劫财"], wx: "同" },
  { label: "我生", items: ["食神", "伤官"], wx: "生" },
  { label: "我克", items: ["偏财", "正财"], wx: "克" },
  { label: "克我", items: ["七杀", "正官"], wx: "被克" },
  { label: "生我", items: ["偏印", "正印"], wx: "被生" },
];
const GROUP_COLORS = ["var(--el-earth)", "var(--el-wood)", "var(--el-fire)", "var(--el-metal)", "var(--el-water)"];

interface CangganItem { shishen?: string; [key: string]: unknown; }
interface PillarDetail { shishen_gan?: string; shishen_zhi?: string; canggan?: CangganItem[]; [key: string]: unknown; }
interface Props { result: Record<string, unknown>; }

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
    <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
      <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }}>
        <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>十神能量分布</h3>
      </div>
      <div className="p-7 space-y-6">
        {SHISHEN_GROUPS.map((group, gi) => {
          const groupTotal = group.items.reduce((sum, item) => sum + (counts[item] || 0), 0);
          const groupPct = (groupTotal / total) * 100;
          const color = GROUP_COLORS[gi];

          return (
            <div key={group.label}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold" style={{ fontSize: 16, color, fontFamily: "var(--font-serif)" }}>{group.label}</span>
                <span className="tabular-nums font-semibold" style={{ fontSize: 14, color: "var(--color-text-muted)" }}>{groupPct.toFixed(0)}%</span>
              </div>
              <div className="h-9 flex overflow-hidden" style={{ background: "var(--bg-secondary)" }}>
                {group.items.map((item, ii) => {
                  const val = counts[item] || 0;
                  const pct = (val / total) * 100;
                  if (pct === 0) return null;
                  return (
                    <div key={item} className="h-full flex items-center justify-center font-semibold transition-all duration-500" style={{ width: `${pct}%`, background: color, opacity: ii === 0 ? 0.85 : 0.5, color: "var(--bg-primary)", fontSize: pct > 8 ? 14 : 11 }} title={`${item}: ${pct.toFixed(1)}%`}>
                      {pct > 8 ? item : ""}
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-4 mt-2">
                {group.items.map((item) => (
                  <span key={item} style={{ fontSize: 14, color: "var(--color-text-muted)" }}>
                    {item}{" "}
                    <span className="tabular-nums font-medium" style={{ color: "var(--color-text-faint)" }}>{((counts[item]||0)/total*100).toFixed(0)}%</span>
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
