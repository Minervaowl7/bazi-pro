"use client";

const LEVELS = ["极弱", "偏弱", "中和", "偏强", "极强"] as const;

interface Props {
  verdict?: string;
  dayMaster?: string;
  deling?: { status?: string; score?: number };
  dedi?: { score?: number; level?: string };
  deshi?: { score?: number; level?: string };
}

export default function StrengthSlider({ verdict, dayMaster, deling, dedi, deshi }: Props) {
  const idx = LEVELS.indexOf(verdict as typeof LEVELS[number]);
  const position = idx >= 0 ? idx : 2;
  const pct = (position / (LEVELS.length - 1)) * 100;

  return (
    <div
      className="rounded-2xl p-6"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="flex items-center justify-between mb-5">
        <h3
          className="text-sm font-semibold"
          style={{ color: "var(--text-secondary)" }}
        >
          日主强弱
        </h3>
        {dayMaster && (
          <span className="text-sm font-medium" style={{ color: "var(--accent)" }}>
            {dayMaster}
          </span>
        )}
      </div>

      {/* 滑块轨道 */}
      <div className="relative mb-4">
        <div
          className="h-2 rounded-full"
          style={{ background: "var(--bg-secondary)" }}
        />
        {/* 填充条 */}
        <div
          className="absolute top-0 left-0 h-2 rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            background: position <= 1
              ? "var(--water)"
              : position === 2
                ? "var(--accent)"
                : "var(--fire)",
          }}
        />
        {/* 指示点 */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 transition-all duration-700"
          style={{
            left: `${pct}%`,
            transform: `translate(-50%, -50%)`,
            background: "var(--bg-card)",
            borderColor: position <= 1
              ? "var(--water)"
              : position === 2
                ? "var(--accent)"
                : "var(--fire)",
            boxShadow: "0 0 8px rgba(212,165,116,0.3)",
          }}
        />
      </div>

      {/* 刻度标签 */}
      <div className="flex justify-between mb-5">
        {LEVELS.map((level, i) => (
          <span
            key={level}
            className="text-[11px] font-medium"
            style={{
              color: i === position ? "var(--accent)" : "var(--text-muted)",
            }}
          >
            {level}
          </span>
        ))}
      </div>

      {/* 三维得分 */}
      <div className="grid grid-cols-3 gap-3">
        <div
          className="rounded-lg p-3 text-center"
          style={{ background: "var(--bg-secondary)" }}
        >
          <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>
            得令
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {deling?.status || "—"}
          </div>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            {deling?.score !== undefined ? `${deling.score > 0 ? "+" : ""}${deling.score}` : ""}
          </div>
        </div>
        <div
          className="rounded-lg p-3 text-center"
          style={{ background: "var(--bg-secondary)" }}
        >
          <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>
            得地
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {dedi?.level || "—"}
          </div>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            {dedi?.score !== undefined ? `${dedi.score > 0 ? "+" : ""}${dedi.score.toFixed(1)}` : ""}
          </div>
        </div>
        <div
          className="rounded-lg p-3 text-center"
          style={{ background: "var(--bg-secondary)" }}
        >
          <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>
            得势
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {deshi?.level || "—"}
          </div>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            {deshi?.score !== undefined ? `${deshi.score > 0 ? "+" : ""}${deshi.score.toFixed(1)}` : ""}
          </div>
        </div>
      </div>
    </div>
  );
}
