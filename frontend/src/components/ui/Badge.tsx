import { cn } from "@/lib/utils";
import { type HTMLAttributes, forwardRef } from "react";

type Variant = "default" | "wood" | "fire" | "earth" | "metal" | "water" | "outline" | "muted";

const variantStyles: Record<Variant, string> = {
  default: "bg-[var(--accent-dim)] text-[var(--color-accent)] border-[var(--border-accent)]",
  wood: "bg-[var(--wood-pill)] text-[var(--el-wood)] border-[var(--wood-pill-border)]",
  fire: "bg-[var(--fire-pill)] text-[var(--el-fire)] border-[var(--fire-pill-border)]",
  earth: "bg-[var(--earth-pill)] text-[var(--el-earth)] border-[var(--earth-pill-border)]",
  metal: "bg-[var(--metal-pill)] text-[var(--el-metal)] border-[var(--metal-pill-border)]",
  water: "bg-[var(--water-pill)] text-[var(--el-water)] border-[var(--water-pill-border)]",
  outline: "bg-transparent text-[var(--color-text-secondary)] border-[var(--color-border)]",
  muted: "bg-[var(--color-bg-panel)] text-[var(--color-text-muted)] border-transparent",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium leading-tight transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = "Badge";

export { Badge, type Variant as BadgeVariant };
