"use client";

import { cn } from "@/lib/utils";

/* ================================================================
   通用骨架屏组件 — shimmer 动画效果
   使用 CSS 变量驱动，支持暗色模式，尊重 prefers-reduced-motion
   ================================================================ */

/* ── 基础 Shimmer 条 ── */
interface ShimmerBarProps {
  /** 宽度（Tailwind 类或 CSS 值） */
  width?: string;
  /** 高度（Tailwind 类或 CSS 值） */
  height?: string;
  /** 圆角风格 */
  rounded?: "sm" | "md" | "lg" | "full" | "none";
  /** 额外 className */
  className?: string;
}

const ROUNDED_MAP = {
  none: "rounded-none",
  sm: "rounded-sm",
  md: "rounded",
  lg: "rounded-lg",
  full: "rounded-full",
} as const;

export function ShimmerBar({ width = "w-full", height = "h-4", rounded = "md", className }: ShimmerBarProps) {
  return (
    <div
      className={cn(width, height, ROUNDED_MAP[rounded], "animate-shimmer", className)}
      aria-hidden="true"
    />
  );
}

/* ── 文本行骨架 ── */
interface SkeletonLineProps {
  /** 行宽度（Tailwind 类） */
  width?: string;
  /** 行高度 */
  height?: string;
  /** 额外 className */
  className?: string;
}

export function SkeletonLine({ width = "w-full", height = "h-4", className }: SkeletonLineProps) {
  return <ShimmerBar width={width} height={height} rounded="sm" className={className} />;
}

/* ── 圆形骨架 ── */
interface SkeletonCircleProps {
  /** 尺寸（Tailwind 类如 w-14 h-14） */
  size?: string;
  /** 额外 className */
  className?: string;
}

export function SkeletonCircle({ size = "w-10 h-10", className }: SkeletonCircleProps) {
  return <ShimmerBar width={size} height={size} rounded="full" className={className} />;
}

/* ── 通用卡片骨架屏 ── */
interface SkeletonCardProps {
  /** 标题区行数（0 = 无标题） */
  titleLines?: number;
  /** 内容区行数 */
  contentLines?: number;
  /** 内容行宽度模式 */
  contentWidths?: string[];
  /** 是否显示顶部边框标题区 */
  showHeader?: boolean;
  /** 额外 className */
  className?: string;
  /** 子元素（用于自定义内容区） */
  children?: React.ReactNode;
}

export default function SkeletonCard({
  titleLines = 1,
  contentLines = 3,
  contentWidths,
  showHeader = true,
  className,
  children,
}: SkeletonCardProps) {
  const defaultWidths = ["w-full", "w-5/6", "w-4/6", "w-3/4", "w-2/3"];
  const widths = contentWidths ?? defaultWidths;

  return (
    <section
      className={cn("card overflow-hidden", className)}
      aria-busy="true"
      aria-label="内容加载中"
    >
      {/* 标题区 */}
      {showHeader && titleLines > 0 && (
        <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
          {Array.from({ length: titleLines }).map((_, i) => (
            <ShimmerBar
              key={i}
              width={i === 0 ? "w-32" : "w-20"}
              height="h-4"
              rounded="sm"
              className={i > 0 ? "mt-2" : ""}
            />
          ))}
        </div>
      )}

      {/* 内容区 */}
      <div className="p-6">
        {children ?? (
          <div className="space-y-3">
            {Array.from({ length: contentLines }).map((_, i) => (
              <SkeletonLine
                key={i}
                width={widths[i % widths.length]}
                height="h-4"
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
