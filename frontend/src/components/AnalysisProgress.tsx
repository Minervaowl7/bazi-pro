"use client";

import { useAnalysisStore } from "@/stores/analysisStore";
import { useEffect, useState } from "react";

const STEP_LABELS: Record<string, string> = {
  "0": "古籍检索",
  "1": "数据校验",
  "2": "旺衰判定",
  "3": "格局判定",
  "4": "十神推导",
  "4b": "喜用神推导",
  "5": "五行力量",
  "5b": "调候查表",
  "7": "刑冲合害",
  "9": "分析完成",
};

const STEP_ORDER = ["0", "1", "2", "3", "4", "4b", "5", "5b", "7"];

export default function AnalysisProgress() {
  const { progress, status } = useAnalysisStore();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (status !== "streaming" && status !== "submitting") return;
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [status]);

  if (status !== "streaming" && status !== "submitting") return null;

  const latestStep = progress[progress.length - 1];
  const currentStepIdx = latestStep
    ? STEP_ORDER.indexOf(latestStep.step)
    : -1;
  const pct = Math.min(
    ((Math.max(currentStepIdx, 0) + (latestStep?.status === "done" ? 1 : 0.5)) / STEP_ORDER.length) * 100,
    95
  );

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}分${sec}秒` : `${sec}秒`;
  };

  return (
    <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] mb-5">
      <div className="px-6 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full animate-pulse shrink-0 bg-[var(--wx-water)]" />
          <h3 className="text-sm font-medium text-[var(--text-3)]">正在分析</h3>
        </div>
        <span className="text-[10px] font-mono tabular-nums text-[var(--text-3)]">
          {formatTime(elapsed)}
        </span>
      </div>

      <div className="px-6 py-4">
        <div className="w-full rounded-full overflow-hidden mb-4 h-1.5 bg-[var(--surface-2)]">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${pct}%`,
              background: "linear-gradient(90deg, var(--wx-water), var(--wx-wood))",
            }}
          />
        </div>

        {latestStep && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs text-[var(--ink)]">
              {STEP_LABELS[latestStep.step] || latestStep.name || `步骤 ${latestStep.step}`}
            </span>
            {latestStep.status === "running" && (
              <span className="text-[10px] animate-pulse text-[var(--text-3)]">处理中...</span>
            )}
            {latestStep.status === "done" && (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-1.5">
          {STEP_ORDER.map((step) => {
            const stepProgress = progress.find((p) => p.step === step);
            const isDone = stepProgress?.status === "done";
            const isRunning = stepProgress?.status === "running";
            return (
              <span
                key={step}
                className={`px-2.5 py-1 rounded-full text-[10px] font-medium transition-all duration-200 ${
                  isDone ? "" : isRunning ? "animate-pulse" : ""
                }`}
                style={
                  isDone
                    ? { background: "rgba(74,222,128,0.12)", color: "var(--success)" }
                    : isRunning
                      ? { background: "rgba(96,165,250,0.1)", color: "var(--wx-water)" }
                      : { background: "var(--surface-2)", color: "var(--text-3)" }
                }
              >
                {isDone && (
                  <svg className="inline-block mr-1 -mt-px" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                )}
                {STEP_LABELS[step]}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
