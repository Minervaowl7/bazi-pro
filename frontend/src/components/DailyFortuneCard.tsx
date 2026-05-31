"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

interface DailyFortune {
  date: string;
  gan_zhi: string;
  overall_level: string;
  dimensions: Record<string, { score: number; level: string }>;
}

const LEVEL_COLORS: Record<string, string> = {
  "大吉": "var(--el-wood)",
  "吉": "var(--el-wood)",
  "中吉": "var(--color-scholar-blue)",
  "平": "var(--color-text-muted)",
  "小凶": "var(--el-fire)",
  "凶": "var(--el-fire)",
};

interface Props {
  analysisId: string;
}

export default function DailyFortuneCard({ analysisId }: Props) {
  const [fortune, setFortune] = useState<DailyFortune | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v2/fortune/daily/${analysisId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.date) setFortune(data);
      })
      .catch(() => {});
  }, [analysisId]);

  if (!fortune) return null;

  const levelColor = LEVEL_COLORS[fortune.overall_level] || "var(--color-text-muted)";

  return (
    <div
      className="rounded-xl p-5"
      style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow)" }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium" style={{ color: "var(--color-text-muted)" }}>
          今日运势
        </h3>
        <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
          {fortune.gan_zhi}日
        </span>
      </div>

      <div className="text-center mb-4">
        <span className="text-2xl font-bold" style={{ color: levelColor }}>
          {fortune.overall_level}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {Object.entries(fortune.dimensions).filter(([k]) => k !== "整体").slice(0, 6).map(([dim, data]) => (
          <div key={dim} className="text-center py-2">
            <div className="text-[10px] mb-1" style={{ color: "var(--color-text-muted)" }}>{dim}</div>
            <div className="text-xs font-medium" style={{ color: LEVEL_COLORS[data.level] || "var(--color-text-muted)" }}>
              {data.level}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
