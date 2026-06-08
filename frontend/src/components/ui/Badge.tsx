import { cn } from "@/lib/utils";
import { type HTMLAttributes, forwardRef } from "react";

type Variant = "default" | "wood" | "fire" | "earth" | "metal" | "water" | "outline" | "muted";

const variantStyles: Record<Variant, string> = {
  default: "bg-[var(--cinnabar-light)] text-[var(--cinnabar)] border-[rgba(201,100,66,0.12)]",
  wood: "bg-[var(--wx-wood-bg)] text-[var(--wx-wood)] border-[rgba(58,125,92,0.18)]",
  fire: "bg-[var(--wx-fire-bg)] text-[var(--wx-fire)] border-[rgba(196,82,58,0.18)]",
  earth: "bg-[var(--wx-earth-bg)] text-[var(--wx-earth)] border-[rgba(139,106,58,0.16)]",
  metal: "bg-[var(--wx-metal-bg)] text-[var(--wx-metal)] border-[rgba(197,165,90,0.18)]",
  water: "bg-[var(--wx-water-bg)] text-[var(--wx-water)] border-[rgba(46,92,138,0.18)]",
  outline: "bg-transparent text-[var(--text-2)] border-[var(--border)]",
  muted: "bg-[var(--surface-2)] text-[var(--text-3)] border-transparent",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium leading-tight transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = "Badge";

export { Badge, type Variant as BadgeVariant };
