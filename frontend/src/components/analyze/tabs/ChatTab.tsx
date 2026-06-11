"use client";

import dynamic from "next/dynamic";

function PanelSkeleton() {
  return (
    <section className="card animate-pulse">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
      </div>
      <div className="p-6 space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  );
}

const ChatPanel = dynamic(() => import("@/components/ChatPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton />,
});

interface ChatTabProps {
  analysisId: string;
  school: string;
}

export default function ChatTab({ analysisId, school }: ChatTabProps) {
  return <ChatPanel analysisId={analysisId} school={school} />;
}
