"use client";

import type { AnalysisResultData } from "@/lib/types";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";

function PanelSkeleton() {
  return (
    <section className="card animate-pulse">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
      </div>
      <div className="p-6 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  );
}

const DimensionAnalysisPanel = dynamic(() => import("@/components/DimensionAnalysisPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton />,
});

interface DeepTabProps {
  result: AnalysisResultData;
  narration?: Record<string, unknown>;
}

const DIMENSIONS = [
  { key: "marriage", label: "婚姻感情", dataField: "marriage_analysis" as const },
  { key: "health", label: "健康养生", dataField: "health_analysis" as const },
  { key: "wealth", label: "财富事业", dataField: "wealth_analysis" as const },
  { key: "family", label: "家庭六亲", dataField: "family_analysis" as const },
] as const;

export default function DeepTab({ result, narration }: DeepTabProps) {
  return (
    <ResponsiveTabPanel
      desktopClassName="space-y-8"
      desktop={
        <>
          {DIMENSIONS.map((d) => (
            <DimensionAnalysisPanel
              key={d.key}
              dimension={d.key}
              data={(result?.[d.dataField] as Record<string, unknown>) || {}}
              narration={typeof narration?.[d.key] === "string" ? narration[d.key] as string : ""}
            />
          ))}
        </>
      }
      mobileSections={DIMENSIONS.map((d) => ({
        title: d.label,
        defaultOpen: d.key === "marriage",
        content: (
          <DimensionAnalysisPanel
            dimension={d.key}
            data={(result?.[d.dataField] as Record<string, unknown>) || {}}
            narration={typeof narration?.[d.key] === "string" ? narration[d.key] as string : ""}
          />
        ),
      }))}
    />
  );
}
