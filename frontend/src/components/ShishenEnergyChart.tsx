"use client";

import { GAN_WUXING, WUXING_COLORS } from "@/lib/constants";

const SHISHEN_GROUPS = [
  { label: "同我", items: ["比肩", "劫财"] },
  { label: "我生", items: ["食神", "伤官"] },
  { label: "我克", items: ["偏财", "正财"] },
  { label: "克我", items: ["七杀", "正官"] },
  { label: "生我", items: ["偏印", "正印"] },
];

const SHENG_MAP: Record<string, string> = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
const KE_MAP: Record<string, string> = { 木: "土", 火: "金", 土: "水", 金: "木", 水: "火" };

function getShishenColor(dayMasterWx: string, groupLabel: string): string {
  if (!dayMasterWx) return "var(--text-3)";
  switch (groupLabel) {
    case "同我": return WUXING_COLORS[dayMasterWx] || "var(--text-3)";
    case "我生": return WUXING_COLORS[SHENG_MAP[dayMasterWx]] || "var(--text-3)";
    case "我克": return WUXING_COLORS[KE_MAP[dayMasterWx]] || "var(--text-3)";
    case "克我": {
      for (const [k, v] of Object.entries(KE_MAP)) { if (v === dayMasterWx) return WUXING_COLORS[k] || "var(--text-3)"; }
      return "var(--text-3)";
    }
    case "生我": {
      for (const [k, v] of Object.entries(SHENG_MAP)) { if (v === dayMasterWx) return WUXING_COLORS[k] || "var(--text-3)"; }
      return "var(--text-3)";
    }
    default: return "var(--text-3)";
  }
}

interface CangganItem { shishen?: string; [key: string]: unknown; }
interface PillarDetail { shishen_gan?: string; shishen_zhi?: string; canggan?: CangganItem[]; [key: string]: unknown; }
interface Props { result: Record<string, unknown>; }

export default function ShishenEnergyChart({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const pillars = shishen?.pillars || [];
  if (pillars.length === 0) return null;

  const validation = result.validation as { day_master?: string } | undefined;
  const dayMaster = validation?.day_master || (result.day_master as string) || "";
  const dayMasterWx = GAN_WUXING[dayMaster] || "";

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
    <section className="card">
      <div className="border-b-2 border-[var(--border-strong)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>十神能量分布</h3>
      </div>
      <div className="p-7 space-y-6">
        {SHISHEN_GROUPS.map((group) => {
          const groupTotal = group.items.reduce((sum, item) => sum + (counts[item] || 0), 0);
          const groupPct = (groupTotal / total) * 100;
          const color = getShishenColor(dayMasterWx, group.label);

          return (
            <div key={group.label}>
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-base" style={{ color, fontFamily: "var(--font-display)" }}>{group.label}</span>
                <span className="tabular-nums font-semibold text-sm" style={{ color: "var(--text-3)" }}>{groupPct.toFixed(0)}%</span>
              </div>
              <div className="h-9 flex overflow-hidden" style={{ background: "var(--surface-2)" }}>
                {group.items.map((item, ii) => {
                  const val = counts[item] || 0;
                  const pct = (val / total) * 100;
                  if (pct === 0) return null;
                  return (
                    <div key={item} className="h-full flex items-center justify-center font-semibold transition-all duration-500" style={{ width: `${pct}%`, background: color, opacity: ii === 0 ? 0.85 : 0.5, color: "var(--bg)", fontSize: pct > 8 ? 14 : 11 }} title={`${item}: ${pct.toFixed(1)}%`}>
                      {pct > 8 ? item : ""}
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-4 mt-2">
                {group.items.map((item) => (
                  <span key={item} className="text-sm" style={{ color: "var(--text-3)" }}>
                    {item}{" "}
                    <span className="tabular-nums font-medium" style={{ color: "var(--text-4)" }}>{((counts[item]||0)/total*100).toFixed(0)}%</span>
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
