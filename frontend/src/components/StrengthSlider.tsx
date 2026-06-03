"use client";

const LEVELS = ["极弱", "身弱", "中和", "偏旺", "极旺"] as const;

function verdictToPosition(verdict?: string): number {
  if (!verdict) return 2;
  if (verdict === "极弱") return 0;
  if (verdict === "身弱" || verdict === "中和偏弱") return 1;
  if (verdict === "中和") return 2;
  if (verdict === "偏旺" || verdict === "中和偏旺" || verdict === "身旺") return 3;
  if (verdict === "极旺") return 4;
  if (verdict.includes("弱")) return 1;
  if (verdict.includes("旺") || verdict.includes("强")) return 3;
  return 2;
}

interface Props {
  verdict?: string;
  dayMaster?: string;
  deling?: { status?: string; score?: number };
  dedi?: { score?: number; level?: string };
  deshi?: { score?: number; level?: string };
}

export default function StrengthSlider({ verdict, dayMaster, deling, dedi, deshi }: Props) {
  const position = verdictToPosition(verdict);
  const pct = (position / (LEVELS.length - 1)) * 100;
  const isWeak = position <= 1;
  const isStrong = position >= 3;
  const trackColor = isWeak ? "var(--el-water)" : isStrong ? "var(--el-fire)" : "var(--color-text-muted)";

  return (
    <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)" }}>
      <div style={{ borderBottom: "2px solid var(--color-border-strong)", padding: "16px 24px" }} className="flex items-center justify-between">
        <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>日主强弱</h3>
        {dayMaster && (
          <span className="font-bold" style={{ fontSize: 17, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{dayMaster}</span>
        )}
      </div>

      <div className="p-7">
        {/* 滑轨 */}
        <div className="relative mb-6">
          <div style={{ height: 4, background: "var(--bg-secondary)" }} />
          <div className="absolute top-0 left-0 transition-all duration-700" style={{ width: `${pct}%`, height: 4, background: trackColor }} />

          {/* 指示器 */}
          <div className="absolute top-1/2" style={{ left: `${pct}%`, transform: "translate(-50%,-50%)" }}>
            <div style={{ width: 20, height: 20, background: "var(--surface)", border: `3px solid ${trackColor}`, boxShadow: `0 0 0 4px ${trackColor}15` }} />
          </div>
        </div>

        {/* 刻度 */}
        <div className="flex justify-between mb-6">
          {LEVELS.map((l, i) => (
            <span key={l} className="font-medium" style={{ fontSize: 14, color: i === position ? trackColor : "var(--color-text-faint)", fontWeight: i === position ? 700 : 400, fontFamily: "var(--font-serif)" }}>
              {l}
            </span>
          ))}
        </div>

        {/* 判定标签 */}
        {verdict && (
          <div className="text-center mb-7">
            <span className="inline-block px-5 py-1.5 font-bold" style={{ fontSize: 15, background: isWeak ? "rgba(53,94,133,0.08)" : isStrong ? "rgba(196,60,44,0.08)" : "var(--bg-secondary)", color: isWeak ? "var(--el-water)" : isStrong ? "var(--el-fire)" : "var(--color-text-secondary)" }}>
              {verdict}
            </span>
          </div>
        )}

        {/* 得令/得地/得势 */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "得令", data: deling },
            { label: "得地", data: dedi },
            { label: "得势", data: deshi },
          ].map((item) => {
            const d = item.data as Record<string, unknown> | undefined;
            const display = (d?.status as string | undefined) || (d?.level as string | undefined) || "—";
            const scoreDisplay = typeof item.data?.score === "number"
              ? `${item.data.score > 0 ? "+" : ""}${Number.isInteger(item.data.score) ? item.data.score : item.data.score.toFixed(1)}`
              : "";

            return (
              <div key={item.label} className="text-center p-5" style={{ background: "var(--bg-secondary)" }}>
                <div className="mb-2 font-semibold uppercase tracking-wider" style={{ fontSize: 12, color: "var(--color-text-faint)", letterSpacing: "0.08em" }}>{item.label}</div>
                <div className="font-bold mb-1" style={{ fontSize: 18, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{display}</div>
                {scoreDisplay && <div style={{ fontSize: 14, color: "var(--color-text-muted)" }}>{scoreDisplay}</div>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
