"use client";

import type { AnalysisResultData } from "@/lib/types";
import DailyFortuneCard from "@/components/DailyFortuneCard";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";
import { Safe } from "@/components/ui/ErrorBoundary";

const DayunTimeline = dynamic(() => import("@/components/DayunTimeline"), {
  ssr: false,
  loading: () => (
    <section className="card animate-pulse">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
      </div>
      <div className="p-6 space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  ),
});

const LifeKlineChart = dynamic(() => import("@/components/LifeKlineChart").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section className="card">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>人生 K 线</h3>
      </div>
      <div className="p-12 text-center text-sm" style={{ color: "var(--text-3)" }}>K线图加载中…</div>
    </section>
  ),
});

interface DayunTabProps {
  result: AnalysisResultData;
  analysisId: string;
  ziweiParams?: { solar_date: string; hour: number; gender: number };
}

export default function DayunTab({ result, analysisId, ziweiParams }: DayunTabProps) {
  return (
    <ResponsiveTabPanel
      desktop={
        <>
          <DayunTimeline result={result} ziweiParams={ziweiParams} />
          <Safe fallback={<section className="card p-10 text-center"><span className="text-sm" style={{ color: "var(--text-3)" }}>K线图暂不可用</span></section>}>
            <LifeKlineChart analysisId={analysisId} />
          </Safe>
          <DailyFortuneCard analysisId={analysisId} />
        </>
      }
      mobileSections={[
        {
          title: "大运流年",
          defaultOpen: true,
          content: <DayunTimeline result={result} ziweiParams={ziweiParams} />,
        },
        {
          title: "人生 K 线",
          content: (
            <Safe fallback={<p className="text-sm py-4 text-center" style={{ color: "var(--text-3)" }}>K线图暂不可用</p>}>
              <LifeKlineChart analysisId={analysisId} />
            </Safe>
          ),
        },
        {
          title: "今日运势",
          content: <DailyFortuneCard analysisId={analysisId} />,
        },
      ]}
    />
  );
}
