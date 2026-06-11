"use client";

import type { AnalysisResultData } from "@/lib/types";
import dynamic from "next/dynamic";
import ResponsiveTabPanel from "@/components/analyze/ResponsiveTabPanel";

function PanelSkeleton({ title, lines = 3 }: { title?: string; lines?: number }) {
  return (
    <section className="card animate-pulse">
      {title && (
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
        </div>
      )}
      <div className="p-6 space-y-3">
        {Array.from({ length: lines }, (_, i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  );
}

const SchoolPanel = dynamic(() => import("@/components/SchoolPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="流派解读" />,
});

const SchoolComparePanel = dynamic(() => import("@/components/SchoolComparePanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="流派对比" lines={5} />,
});

const LlmOverview = dynamic(() => import("@/components/LlmOverview"), {
  ssr: false,
  loading: () => <PanelSkeleton title="AI 总览" lines={4} />,
});

interface AnalysisTabProps {
  result: AnalysisResultData;
  narration?: Record<string, unknown>;
  isCompareMode: boolean;
  schoolAnalyses?: Record<string, unknown>;
}

export default function AnalysisTab({ result, narration, isCompareMode, schoolAnalyses }: AnalysisTabProps) {
  const hasLlmOverview = !!result?.llm_overview;

  const schoolContent = isCompareMode && schoolAnalyses
    ? <SchoolComparePanel schoolAnalyses={schoolAnalyses} />
    : <SchoolPanel result={result} narration={narration} />;

  return (
    <ResponsiveTabPanel
      desktopClassName=""
      desktop={
        <div style={{ maxWidth: 860, marginLeft: "auto", marginRight: "auto" }}>
          {hasLlmOverview && <LlmOverview content={result.llm_overview as string} />}
          {schoolContent}
        </div>
      }
      mobileSections={[
        ...(hasLlmOverview ? [{
          title: "AI 总览",
          defaultOpen: true,
          content: <LlmOverview content={result.llm_overview as string} />,
        }] : []),
        {
          title: "流派解读",
          defaultOpen: !hasLlmOverview,
          content: schoolContent,
        },
      ]}
    />
  );
}
