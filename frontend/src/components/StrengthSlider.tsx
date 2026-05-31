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

  return (
    <div
      className="rounded-2xl p-7"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="flex items-center justify-between mb-5">
        <h3
          className="text-sm font-medium"
          style={{ color: "var(--text-muted)" }}
        >
          日主强弱
        </h3>
        {dayMaster && (
          <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
            {dayMaster}
          </span>
        )}
      </div>

      {/* 滑块轨道 */}
      <div className="relative mb-4">
        <div
          className="h-3 rounded-full"
          style={{ background: "var(--bg-secondary)" }}
        />
        {/* 填充条 */}
        <div
          className="absolute top-0 left-0 h-3 rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            background: position <= 1
              ? "var(--water)"
              : position === 2
                ? "var(--text-muted)"
                : "var(--fire)",
          }}
        />
        {/* 指示点 */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full border-2 transition-all duration-700"
          style={{
            left: `${pct}%`,
            transform: `translate(-50%, -50%)`,
            background: "var(--bg-card)",
            borderColor: position <= 1
              ? "var(--water)"
              : position === 2
                ? "var(--text-muted)"
                : "var(--fire)",
            boxShadow: "0 0 8px rgba(0,0,0,0.3)",
          }}
        />
      </div>

      {/* 刻度标签 */}
      <div className="flex justify-between mb-2">
        {LEVELS.map((level, i) => (
          <span
            key={level}
            className="text-[11px] font-medium"
            style={{
              color: i === position
                ? (position <= 1 ? "var(--water)" : position >= 3 ? "var(--fire)" : "var(--text-primary)")
                : "var(--text-muted)",
            }}
          >
            {level}
          </span>
        ))}
      </div>
      {verdict && (
        <div className="text-center mb-5">
          <span className="text-xs px-2.5 py-1 rounded-full font-medium"
            style={{
              background: position <= 1 ? "rgba(96,165,250,0.1)" : position >= 3 ? "rgba(251,113,133,0.1)" : "var(--bg-hover)",
              color: position <= 1 ? "var(--water)" : position >= 3 ? "var(--fire)" : "var(--text-secondary)",
            }}>
            {verdict}
          </span>
        </div>
      )}

      {/* 三维得分 */}
      <div className="grid grid-cols-3 gap-3">
        <div
          className="rounded-xl p-4 text-center"
          style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)" }}
        >
          <div className="text-[10px] mb-1.5" style={{ color: "var(--text-muted)" }}>
            得令
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {deling?.status || "—"}
          </div>
          <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            {deling?.score !== undefined ? `${deling.score > 0 ? "+" : ""}${deling.score}` : ""}
          </div>
        </div>
        <div
          className="rounded-xl p-4 text-center"
          style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)" }}
        >
          <div className="text-[10px] mb-1.5" style={{ color: "var(--text-muted)" }}>
            得地
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {dedi?.level || "—"}
          </div>
          <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            {dedi?.score !== undefined ? `${dedi.score > 0 ? "+" : ""}${dedi.score.toFixed(1)}` : ""}
          </div>
        </div>
        <div
          className="rounded-xl p-4 text-center"
          style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)" }}
        >
          <div className="text-[10px] mb-1.5" style={{ color: "var(--text-muted)" }}>
            得势
          </div>
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {deshi?.level || "—"}
          </div>
          <div className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
            {deshi?.score !== undefined ? `${deshi.score > 0 ? "+" : ""}${deshi.score.toFixed(1)}` : ""}
          </div>
        </div>
      </div>
    </div>
  );
}
