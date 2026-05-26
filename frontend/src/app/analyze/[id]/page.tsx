"use client";

import { useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";
import AnalysisProgress from "@/components/AnalysisProgress";
import BaziChartCard from "@/components/BaziChartCard";
import SchoolPanel from "@/components/SchoolPanel";
import DayunTimeline from "@/components/DayunTimeline";
import HistorySidebar from "@/components/HistorySidebar";
import Link from "next/link";

export default function AnalyzePage() {
  const params = useParams();
  const analysisId = params.id as string;
  const { status, result, error, analysisId: storeAnalysisId, fetchResult, reset } = useAnalysisStore();
  const prevIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!analysisId) return;
    if (analysisId !== prevIdRef.current) {
      prevIdRef.current = analysisId;
      if (analysisId !== storeAnalysisId) {
        reset();
        fetchResult(analysisId);
      }
    } else if (status === "idle") {
      fetchResult(analysisId);
    }
  }, [analysisId, status, storeAnalysisId, fetchResult, reset]);

  const analysisResult = result?.result as Record<string, unknown> | undefined;

  return (
    <div className="flex flex-1 min-h-screen">
      <HistorySidebar />

      <main className="flex-1 p-6 overflow-y-auto max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/"
            className="text-sm text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors"
          >
            ← 返回首页
          </Link>
          <span className="text-xs text-[var(--text-muted)] font-mono">{analysisId}</span>
        </div>

        <AnalysisProgress />

        {status === "failed" && (
          <div className="bg-[var(--bg-card)] border border-[var(--danger)] rounded-xl p-5 mb-6">
            <h3 className="text-[var(--danger)] font-medium mb-2">分析失败</h3>
            <p className="text-sm text-[var(--text-secondary)]">{error || "未知错误"}</p>
          </div>
        )}

        {status === "completed" && analysisResult && (
          <>
            <BaziChartCard result={analysisResult} />
            <SchoolPanel result={analysisResult} />
            <DayunTimeline result={analysisResult} />
          </>
        )}

        {status === "completed" && !analysisResult && result?.status === "completed" && (
          <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5">
            <p className="text-[var(--text-secondary)]">分析已完成，但无详细结果数据。</p>
          </div>
        )}
      </main>
    </div>
  );
}
