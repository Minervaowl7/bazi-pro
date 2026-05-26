"use client";

import { useAnalysisStore, type ProgressStep } from "@/stores/analysisStore";

const STEP_LABELS: Record<string, string> = {
  "0": "古籍检索",
  "1": "数据校验",
  "2": "旺衰判定",
  "3": "格局判定",
  "4": "十神推导",
  "4b": "喜用神推导",
  "5": "五行力量",
  "7": "刑冲合害",
  "9": "分析完成",
};

export default function AnalysisProgress() {
  const { progress, status } = useAnalysisStore();

  if (status !== "streaming" && status !== "submitting") return null;

  const latestStep = progress[progress.length - 1];
  const completedSteps = progress.filter((s) => s.status === "done");
  const totalSteps = 8;
  const pct = Math.min((completedSteps.length / totalSteps) * 100, 100);

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-[var(--text-secondary)]">分析进度</h3>
        <span className="text-xs text-[var(--text-muted)]">
          {completedSteps.length}/{totalSteps}
        </span>
      </div>

      <div className="w-full h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-[var(--accent)] rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      {latestStep && (
        <div className="flex items-center gap-2">
          {latestStep.status === "running" && (
            <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
          )}
          {latestStep.status === "done" && (
            <div className="w-2 h-2 rounded-full bg-[var(--success)]" />
          )}
          <span className="text-sm text-[var(--text-secondary)]">
            {STEP_LABELS[latestStep.step] || latestStep.name || `步骤 ${latestStep.step}`}
            {latestStep.status === "running" ? "..." : ""}
          </span>
        </div>
      )}

      <div className="mt-3 space-y-1">
        {progress.map((step: ProgressStep, i: number) => (
          <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <span className={step.status === "done" ? "text-[var(--success)]" : "text-[var(--accent)]"}>
              {step.status === "done" ? "✓" : "●"}
            </span>
            <span>{STEP_LABELS[step.step] || step.name || `步骤 ${step.step}`}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
