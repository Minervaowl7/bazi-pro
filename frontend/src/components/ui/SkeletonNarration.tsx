"use client";

import { ShimmerBar, SkeletonLine } from "./SkeletonCard";

/* ================================================================
   叙述面板骨架屏 — 匹配叙述面板布局
   多段叙述卡片，每段含标题 + 多行文本
   ================================================================ */

interface SkeletonNarrationProps {
  /** 叙述段落数 */
  sections?: number;
  /** 每段文本行数范围 */
  linesPerSection?: number;
}

const DEFAULT_SECTIONS = 3;
const DEFAULT_LINES = 4;

export default function SkeletonNarration({
  sections = DEFAULT_SECTIONS,
  linesPerSection = DEFAULT_LINES,
}: SkeletonNarrationProps) {
  return (
    <div className="space-y-4 mb-6" aria-busy="true" aria-label="叙述内容加载中">
      {Array.from({ length: sections }).map((_, sectionIdx) => (
        <div
          key={sectionIdx}
          className="card overflow-hidden border-l-4"
          style={{ borderLeftColor: "var(--border-subtle)" }}
        >
          <div className="p-6">
            {/* 段落标题 */}
            <ShimmerBar width="w-24" height="h-5" rounded="sm" className="mb-4" />

            {/* 段落文本行 */}
            <div className="space-y-3">
              {Array.from({ length: linesPerSection }).map((_, lineIdx) => {
                // 最后一行短一些，模拟自然段落
                const isLast = lineIdx === linesPerSection - 1;
                const widths = ["w-full", "w-11/12", "w-5/6", "w-4/6"];
                const width = isLast ? "w-3/5" : widths[lineIdx % widths.length];
                return (
                  <SkeletonLine
                    key={lineIdx}
                    width={width}
                    height="h-3.5"
                  />
                );
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
