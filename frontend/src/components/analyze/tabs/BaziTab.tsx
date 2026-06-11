"use client";

import { type ReactNode, Component } from "react";
import type { AnalysisResultData } from "@/lib/types";
import BaziChartCard from "@/components/BaziChartCard";
import ChartQuality, { type ChartQualityData } from "@/components/ChartQuality";
import StrengthSlider from "@/components/StrengthSlider";
import ShishenEnergyChart from "@/components/ShishenEnergyChart";
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

const RelationGraph = dynamic(() => import("@/components/RelationGraph").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section className="card">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>关系图谱</h3>
      </div>
      <div className="p-12 text-center text-sm" style={{ color: "var(--text-3)" }}>关系图谱加载中…</div>
    </section>
  ),
});

interface BaziTabProps {
  result: AnalysisResultData;
}

export default function BaziTab({ result }: BaziTabProps) {
  const pattern = result?.pattern;

  return (
    <ResponsiveTabPanel
      desktop={
        <>
          <BaziChartCard result={result} />
          {result?.chart_quality && <ChartQuality data={result.chart_quality as unknown as ChartQualityData} />}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <StrengthSlider strength={result?.strength} dayMaster={result?.validation?.day_master} />
            <ShishenEnergyChart result={result} />
          </div>
          <Safe fallback={
            <section className="card p-10 text-center">
              <span className="text-sm" style={{ color: "var(--text-3)" }}>关系图谱暂不可用</span>
            </section>
          }>
            <RelationGraph result={result} />
          </Safe>
          {pattern?.reason && (
            <section className="card">
              <div className="border-b border-[var(--border)] px-6 py-4">
                <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>格局判定依据</h3>
                {pattern.confidence !== undefined && (
                  <span className="tabular-nums ml-3" style={{ fontSize: 13, color: "var(--text-4)" }}>{(pattern.confidence * 100).toFixed(0)}%</span>
                )}
              </div>
              <div className="p-7">
                <p className="text-[15px] leading-relaxed" style={{ color: "var(--text-2)" }}>{pattern.reason}</p>
                {pattern.confidence !== undefined && (
                  <div className="mt-4 flex items-center gap-3">
                    <div className="flex-1 h-2 overflow-hidden" style={{ background: "var(--surface-2)" }}>
                      <div className="h-full" style={{
                        width: `${Math.min(pattern.confidence * 100, 100)}%`,
                        transition: "width 0.7s",
                        background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                      }} />
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      }
      mobileSections={[
        {
          title: "四柱命盘",
          defaultOpen: true,
          content: (
            <>
              <BaziChartCard result={result} />
              {result?.chart_quality && <ChartQuality data={result.chart_quality as unknown as ChartQualityData} />}
            </>
          ),
        },
        {
          title: "旺衰 & 十神",
          defaultOpen: true,
          content: (
            <>
              <StrengthSlider strength={result?.strength} dayMaster={result?.validation?.day_master} />
              <div className="mt-4"><ShishenEnergyChart result={result} /></div>
            </>
          ),
        },
        {
          title: "关系图谱",
          content: (
            <Safe fallback={<p className="text-sm py-4 text-center" style={{ color: "var(--text-3)" }}>关系图谱暂不可用</p>}>
              <RelationGraph result={result} />
            </Safe>
          ),
        },
        ...(pattern?.reason ? [{
          title: "格局判定依据",
          content: (
            <>
              <p className="text-[14px] leading-relaxed" style={{ color: "var(--text-2)" }}>{pattern.reason}</p>
              {pattern.confidence !== undefined && (
                <div className="mt-3 flex items-center gap-3">
                  <div className="flex-1 h-2 overflow-hidden" style={{ background: "var(--surface-2)" }}>
                    <div className="h-full" style={{
                      width: `${Math.min(pattern.confidence * 100, 100)}%`,
                      transition: "width 0.7s",
                      background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                    }} />
                  </div>
                  <span className="text-xs tabular-nums" style={{ color: "var(--text-4)" }}>{(pattern.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
            </>
          ),
        }] : []),
      ]}
    />
  );
}
