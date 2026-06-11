"use client";

import { ShimmerBar, SkeletonLine } from "./SkeletonCard";

/* ================================================================
   四柱命盘骨架屏 — 匹配 BaziChartCard 布局
   4 列柱位网格：年柱/月柱/日柱/时柱
   ================================================================ */

const PILLAR_COUNT = 4;

export default function SkeletonBaziChart() {
  return (
    <section className="card overflow-hidden mb-6" aria-busy="true" aria-label="四柱命盘加载中">
      {/* 顶部标题栏 */}
      <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
        <ShimmerBar width="w-28" height="h-5" rounded="sm" />
      </div>

      {/* 四柱网格 */}
      <div className="p-6">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: PILLAR_COUNT }).map((_, i) => (
            <div
              key={i}
              className="text-center p-5 rounded-xl"
              style={{ border: "1px solid var(--border-subtle)", background: "var(--surface-2)" }}
            >
              {/* 柱位名称 */}
              <ShimmerBar width="w-12" height="h-3" rounded="sm" className="mx-auto mb-4" />

              {/* 天干 */}
              <ShimmerBar width="w-14 h-14" height="h-14" rounded="lg" className="mx-auto mb-3" />

              {/* 地支 */}
              <ShimmerBar width="w-14 h-14" height="h-14" rounded="lg" className="mx-auto mb-3" />

              {/* 十神 */}
              <ShimmerBar width="w-10" height="h-3" rounded="sm" className="mx-auto mb-2" />

              {/* 纳音 */}
              <ShimmerBar width="w-16" height="h-3" rounded="sm" className="mx-auto mb-3" />

              {/* 藏干区域 */}
              <div className="space-y-1.5 pt-2 border-t border-[var(--border-subtle)]">
                <ShimmerBar width="w-8" height="h-2.5" rounded="sm" className="mx-auto" />
                <ShimmerBar width="w-12" height="h-2.5" rounded="sm" className="mx-auto" />
              </div>
            </div>
          ))}
        </div>

        {/* 底部旺衰指示区 */}
        <div className="mt-6 flex items-center justify-center gap-4">
          <ShimmerBar width="w-20" height="h-6" rounded="full" />
          <ShimmerBar width="w-1" height="h-4" rounded="none" />
          <ShimmerBar width="w-24" height="h-6" rounded="full" />
        </div>
      </div>
    </section>
  );
}
