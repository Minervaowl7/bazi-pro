"use client";

/** 分析页骨架屏组件 */
export function SkeletonCard() {
  return (
    <section className="card p-7 mb-6 animate-pulse">
      <div className="h-5 w-32 mb-6 rounded" style={{ background: "var(--surface-2)" }} />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="text-center p-6 border border-[var(--border-subtle)] rounded-xl" style={{ background: "var(--surface-2)" }}>
            <div className="h-3 w-16 mx-auto mb-4 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-14 w-14 mx-auto mb-3 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-14 w-14 mx-auto mb-3 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-12 mx-auto rounded" style={{ background: "var(--surface-2)" }} />
          </div>
        ))}
      </div>
    </section>
  );
}

export function SkeletonNarration() {
  return (
    <div className="space-y-4 mb-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card p-6 animate-pulse border-l-4" style={{ borderLeftColor: "var(--border-subtle)" }}>
          <div className="h-4 w-24 mb-4 rounded" style={{ background: "var(--surface-2)" }} />
          <div className="space-y-3">
            <div className="h-4 w-full rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-5/6 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-4/6 rounded" style={{ background: "var(--surface-2)" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
