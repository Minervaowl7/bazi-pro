"use client";

import type { AnalysisResultData } from "@/lib/types";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";

const ZiweiPanel = dynamic(() => import("@/components/ZiweiPanel"), {
  ssr: false,
  loading: () => <div className="p-12 text-center text-sm" style={{ color: "var(--text-3)" }}>紫微命盘加载中…</div>,
});

const ZiweiNarrationPanel = dynamic(() => import("@/components/ZiweiNarrationPanel"), {
  ssr: false,
  loading: () => <div className="p-8 text-center text-sm" style={{ color: "var(--text-3)" }}>紫微简批加载中…</div>,
});

interface ZiweiTabProps {
  result: AnalysisResultData;
}

export default function ZiweiTab({ result }: ZiweiTabProps) {
  const ziwei = result?.ziwei as Record<string, unknown> | undefined;
  const chartData = ziwei?.chart as Record<string, unknown> ?? ziwei;
  const narration = ziwei?.narration as Record<string, string> ?? {};

  if (!result?.ziwei) {
    return (
      <>
        <div className="hidden sm:block">
          <section className="card p-6">
            <p className="text-[15px]" style={{ color: "var(--text-3)" }}>紫微斗数数据不可用（需安装 iztro-py 依赖）</p>
          </section>
        </div>
        <div className="sm:hidden">
          <section className="card p-6">
            <p className="text-[14px]" style={{ color: "var(--text-3)" }}>紫微斗数数据不可用（需安装 iztro-py 依赖）</p>
          </section>
        </div>
      </>
    );
  }

  return (
    <ResponsiveTabPanel
      desktop={
        <>
          <section className="card p-6">
            <div className="border-b border-[var(--border)] pb-3 mb-4">
              <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>紫微斗数命盘</h3>
            </div>
            <ZiweiPanel data={chartData} />
          </section>
          <ZiweiNarrationPanel narration={narration} />
        </>
      }
      mobileSections={[
        {
          title: "紫微斗数命盘",
          defaultOpen: true,
          content: <ZiweiPanel data={chartData} />,
        },
        {
          title: "紫微斗数简批",
          content: <ZiweiNarrationPanel narration={narration} />,
        },
      ]}
    />
  );
}
