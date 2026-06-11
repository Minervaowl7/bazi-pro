"use client";

import { Component, type ReactNode } from "react";
import type { AnalysisResultData } from "@/lib/types";
import DailyFortuneCard from "@/components/DailyFortuneCard";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";

interface FallbackProps { children: ReactNode; fallback?: ReactNode; }
class ErrorBoundary extends Component<FallbackProps, { hasError: boolean; error?: Error }> {
  constructor(props: FallbackProps) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) { console.error("[ErrorBoundary]", error, info.componentStack); }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <section className="card p-8 text-center" style={{ margin: "2rem auto", maxWidth: 600 }}>
          <h3 style={{ color: "var(--danger)", marginBottom: 8 }}>渲染出错</h3>
          <p style={{ color: "var(--text-2)", fontSize: 14 }}>{this.state.error?.message || "未知错误"}</p>
          <button onClick={() => this.setState({ hasError: false, error: undefined })}
            style={{ marginTop: 16, padding: "8px 20px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface)", cursor: "pointer", color: "var(--ink)" }}>
            重试
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
function Safe({ children, fallback }: FallbackProps) { return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>; }

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
