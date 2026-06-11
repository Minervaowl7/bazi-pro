"use client";

import { ShimmerBar } from "./SkeletonCard";

/* ================================================================
   大运时间轴骨架屏 — 匹配 DayunTimeline 布局
   垂直时间线：左侧连接线 + 右侧大运卡片
   ================================================================ */

const DAYUN_COUNT = 8; // 通常显示 8 步大运

export default function SkeletonDayun() {
  return (
    <section className="card overflow-hidden mb-6" aria-busy="true" aria-label="大运时间轴加载中">
      {/* 顶部标题栏 */}
      <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center justify-between">
          <ShimmerBar width="w-24" height="h-5" rounded="sm" />
          <ShimmerBar width="w-16" height="h-4" rounded="full" />
        </div>
      </div>

      {/* 大运列表 */}
      <div className="p-6">
        <div className="space-y-0">
          {Array.from({ length: DAYUN_COUNT }).map((_, i) => {
            const isLast = i === DAYUN_COUNT - 1;
            return (
              <div key={i} className="flex gap-4">
                {/* 左侧：时间线连接 */}
                <div className="flex flex-col items-center w-6 shrink-0">
                  <ShimmerBar width="w-5" height="h-5" rounded="full" />
                  {!isLast && (
                    <div className="w-px flex-1 min-h-[20px] my-1" style={{ background: "var(--border-subtle)" }} />
                  )}
                </div>

                {/* 右侧：大运内容 */}
                <div className={isLast ? "pb-1" : "pb-5"}>
                  <div className="flex items-center gap-3">
                    {/* 干支对 */}
                    <div className="flex gap-1.5">
                      <ShimmerBar width="w-8 h-8" height="h-8" rounded="lg" />
                      <ShimmerBar width="w-8 h-8" height="h-8" rounded="lg" />
                    </div>
                    {/* 年龄范围 */}
                    <ShimmerBar width="w-20" height="h-3" rounded="sm" />
                  </div>
                  {/* 十神 / 五行标签 */}
                  <div className="flex gap-2 mt-2">
                    <ShimmerBar width="w-12" height="h-5" rounded="full" />
                    <ShimmerBar width="w-10" height="h-5" rounded="full" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
