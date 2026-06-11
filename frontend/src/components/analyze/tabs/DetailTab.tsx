"use client";

import type { AnalysisResultData } from "@/lib/types";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";

function PanelSkeleton({ title }: { title?: string }) {
  return (
    <section className="card animate-pulse">
      {title && (
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
        </div>
      )}
      <div className="p-6 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  );
}

const GongweiPanel = dynamic(() => import("@/components/GongweiPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="宫位分析" />,
});

const ShenShaPanel = dynamic(() => import("@/components/ShenShaPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="神煞查盘" />,
});

interface DetailTabProps {
  result: AnalysisResultData;
}

export default function DetailTab({ result }: DetailTabProps) {
  return (
    <ResponsiveTabPanel
      desktop={
        <>
          <GongweiPanel result={result} />
          <ShenShaPanel result={result} />
        </>
      }
      mobileSections={[
        {
          title: "宫位分析",
          defaultOpen: true,
          content: <GongweiPanel result={result} />,
        },
        {
          title: "神煞查盘",
          defaultOpen: true,
          content: <ShenShaPanel result={result} />,
        },
      ]}
    />
  );
}
