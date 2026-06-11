"use client";

import { useMemo } from "react";

/* ── 类型定义 ──────────────────────────────────────────────── */

interface Star {
  name: string;
  type: string;
  brightness?: string | null;
  mutagen?: string | null;
}

interface Palace {
  name: string;
  isBodyPalace: boolean;
  heavenlyStem: string;
  earthlyBranch: string;
  majorStars: Star[];
  minorStars: Star[];
  adjectiveStars: Star[];
  changsheng12: string;
  boshi12: string;
}

interface ZiweiData {
  soul?: string;
  body?: string;
  fiveElementsClass?: string;
  earthlyBranchOfSoulPalace?: string;
  earthlyBranchOfBodyPalace?: string;
  palaces?: Palace[];
  [key: string]: unknown;
}

/* ── 宫位中文映射 ──────────────────────────────────────────── */

const PALACE_ORDER = [
  "命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫",
  "迁移宫", "交友宫", "官禄宫", "田宅宫", "福德宫", "父母宫",
];

const STAR_TYPE_LABELS: Record<string, string> = {
  major: "主星",
  soft: "辅星",
  hard: "煞星",
  adjective: "杂耀",
  flower: "桃花",
};

/* ── 组件 ──────────────────────────────────────────────────── */

interface ZiweiPanelProps {
  data: ZiweiData;
}

export default function ZiweiPanel({ data }: ZiweiPanelProps) {
  const palaces = useMemo(() => {
    if (!data.palaces) return [];
    // 按 PALACE_ORDER 排序
    const sorted = [...data.palaces].sort((a, b) => {
      const ia = PALACE_ORDER.indexOf(a.name);
      const ib = PALACE_ORDER.indexOf(b.name);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });
    return sorted;
  }, [data.palaces]);

  if (!data.palaces || data.palaces.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* 命盘概要 */}
      <div className="flex flex-wrap items-center gap-3 text-sm">
        {data.soul && (
          <span className="rounded-full px-3 py-1 font-medium" style={{ background: "var(--ziwei-purple-bg)", color: "var(--ziwei-purple-text)" }}>
            命主: {String(data.soul)}
          </span>
        )}
        {data.body && (
          <span className="rounded-full px-3 py-1 font-medium" style={{ background: "var(--ziwei-indigo-bg)", color: "var(--ziwei-indigo-text)" }}>
            身主: {String(data.body)}
          </span>
        )}
        {data.fiveElementsClass && (
          <span className="rounded-full px-3 py-1 font-medium" style={{ background: "var(--ziwei-amber-bg)", color: "var(--ziwei-amber-text)" }}>
            {String(data.fiveElementsClass)}
          </span>
        )}
        {data.earthlyBranchOfSoulPalace && (
          <span style={{ color: "var(--text-2)" }}>
            命宫在{String(data.earthlyBranchOfSoulPalace)}
          </span>
        )}
      </div>

      {/* 十二宫表格 */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--border)" }}>
              <th className="px-2 py-1.5 text-left font-medium" style={{ color: "var(--text-2)" }}>宫位</th>
              <th className="px-2 py-1.5 text-left font-medium" style={{ color: "var(--text-2)" }}>干支</th>
              <th className="px-2 py-1.5 text-left font-medium" style={{ color: "var(--text-2)" }}>主星</th>
              <th className="px-2 py-1.5 text-left font-medium" style={{ color: "var(--text-2)" }}>辅星</th>
              <th className="px-2 py-1.5 text-left font-medium" style={{ color: "var(--text-2)" }}>长生</th>
            </tr>
          </thead>
          <tbody>
            {palaces.map((p) => (
              <tr
                key={p.name}
                className="border-b"
                style={{
                  borderColor: "var(--border-subtle)",
                  background: p.isBodyPalace ? "var(--ziwei-indigo-row)" : undefined,
                }}
              >
                <td className="px-2 py-1.5 font-medium" style={{ color: "var(--ink)" }}>
                  {p.name}
                  {p.isBodyPalace && (
                    <span className="ml-1 text-xs" style={{ color: "var(--ziwei-indigo-bright)" }}>(身)</span>
                  )}
                </td>
                <td className="px-2 py-1.5" style={{ color: "var(--text-2)" }}>
                  {p.heavenlyStem}{p.earthlyBranch}
                </td>
                <td className="px-2 py-1.5">
                  <div className="flex flex-wrap gap-1">
                    {(p.majorStars ?? []).map((s) => (
                      <span
                        key={s.name}
                        className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium"
                        style={{ background: "var(--ziwei-purple-bg)", color: "var(--ziwei-purple-text)" }}
                      >
                        {s.name}
                        {s.brightness && (
                          <span className="ml-0.5" style={{ color: "var(--ziwei-purple-bright)" }}>({s.brightness})</span>
                        )}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-2 py-1.5">
                  <div className="flex flex-wrap gap-1">
                    {(p.minorStars ?? []).map((s) => (
                      <span
                        key={s.name}
                        className="inline-flex items-center rounded px-1.5 py-0.5 text-xs"
                        style={{ background: "var(--ziwei-blue-bg)", color: "var(--ziwei-blue-text)" }}
                      >
                        {s.name}
                      </span>
                    ))}
                    {(p.adjectiveStars ?? []).slice(0, 3).map((s) => (
                      <span
                        key={s.name}
                        className="inline-flex items-center rounded px-1.5 py-0.5 text-xs"
                        style={{ background: "var(--surface-2)", color: "var(--text-2)" }}
                      >
                        {s.name}
                      </span>
                    ))}
                    {(p.adjectiveStars ?? []).length > 3 && (
                      <span className="text-xs" style={{ color: "var(--text-3)" }}>+{p.adjectiveStars.length - 3}</span>
                    )}
                  </div>
                </td>
                <td className="px-2 py-1.5" style={{ color: "var(--text-2)" }}>
                  {p.changsheng12}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 图例 */}
      <div className="flex flex-wrap gap-3 text-xs" style={{ color: "var(--text-3)" }}>
        {Object.entries(STAR_TYPE_LABELS).map(([key, label]) => (
          <span key={key}>{label}</span>
        ))}
        <span style={{ color: "var(--ziwei-indigo-bright)" }}>(身) = 身宫</span>
      </div>
    </div>
  );
}
