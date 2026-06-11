"use client";

import { ShimmerBar, SkeletonLine } from "./SkeletonCard";

/* ================================================================
   五行力量骨架屏 — 匹配 StrengthSlider + ShishenEnergyChart 双栏布局
   左侧：旺衰强度条  右侧：十神能量雷达图
   ================================================================ */

const STRENGTH_ITEMS = 3; // 得令 / 得地 / 得势
const WUXING_ITEMS = 5;   // 木火土金水

export default function SkeletonWuxing() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6" aria-busy="true" aria-label="五行力量加载中">
      {/* 左侧：旺衰强度面板 */}
      <section className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
          <ShimmerBar width="w-24" height="h-5" rounded="sm" />
        </div>
        <div className="p-6 space-y-5">
          {/* 旺衰判定徽章 */}
          <div className="flex items-center gap-3">
            <ShimmerBar width="w-16" height="h-7" rounded="full" />
            <ShimmerBar width="w-28" height="h-4" rounded="sm" />
          </div>

          {/* 得令/得地/得势 条 */}
          {Array.from({ length: STRENGTH_ITEMS }).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-center justify-between">
                <ShimmerBar width="w-10" height="h-3" rounded="sm" />
                <ShimmerBar width="w-12" height="h-3" rounded="sm" />
              </div>
              <ShimmerBar width="w-full" height="h-2" rounded="full" />
            </div>
          ))}

          {/* 底部说明 */}
          <div className="pt-3 border-t border-[var(--border-subtle)] space-y-2">
            <SkeletonLine width="w-full" height="h-3" />
            <SkeletonLine width="w-4/6" height="h-3" />
          </div>
        </div>
      </section>

      {/* 右侧：十神能量 / 五行分布 */}
      <section className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
          <ShimmerBar width="w-28" height="h-5" rounded="sm" />
        </div>
        <div className="p-6">
          {/* 雷达图占位 */}
          <div className="flex items-center justify-center mb-6">
            <ShimmerBar width="w-48 h-48" height="h-48" rounded="full" />
          </div>

          {/* 五行条形 */}
          <div className="space-y-3">
            {Array.from({ length: WUXING_ITEMS }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <ShimmerBar width="w-6" height="h-6" rounded="full" />
                <div className="flex-1 space-y-1">
                  <ShimmerBar
                    width={["w-3/4", "w-5/6", "w-2/3", "w-4/5", "w-1/2"][i % 5]}
                    height="h-2"
                    rounded="full"
                  />
                </div>
                <ShimmerBar width="w-10" height="h-3" rounded="sm" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
