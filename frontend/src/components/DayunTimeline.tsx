"use client";

interface DayunStep {
  age_range?: string;
  gan?: string;
  zhi?: string;
  startAge?: number;
  endAge?: number;
}

interface DayunTimelineProps {
  result: Record<string, unknown>;
}

export default function DayunTimeline({ result }: DayunTimelineProps) {
  const validation = result.validation as { bazi?: string } | undefined;
  const birthJson = result.birth_json || result.validation;

  let dayunList: DayunStep[] = [];
  if (result.dayun && Array.isArray(result.dayun)) {
    dayunList = result.dayun as DayunStep[];
  } else if (birthJson && typeof birthJson === "object") {
    const bj = birthJson as Record<string, unknown>;
    if (bj["大运"] && Array.isArray(bj["大运"])) {
      dayunList = bj["大运"] as DayunStep[];
    }
  }

  if (dayunList.length === 0) return null;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <h2 className="text-lg font-medium mb-4">大运时间轴</h2>

      <div className="overflow-x-auto">
        <div className="flex gap-2 min-w-max pb-2">
          {dayunList.map((step, i) => {
            const ganZhi = `${step.gan || ""}${step.zhi || ""}`;
            const ageRange = step.age_range || (step.startAge != null ? `${step.startAge}-${step.endAge}` : `${i * 10 + 3}-${i * 10 + 12}`);

            return (
              <div
                key={i}
                className="flex flex-col items-center px-3 py-2 bg-[var(--bg-secondary)] rounded-lg min-w-[64px] hover:bg-[var(--bg-hover)] transition-colors cursor-default"
              >
                <span className="text-xs text-[var(--text-muted)] mb-1">{ageRange}岁</span>
                <span className="text-base font-medium text-[var(--text-primary)]">{ganZhi || "—"}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
