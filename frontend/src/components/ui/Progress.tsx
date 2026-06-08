import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  max?: number;
  color?: string;
  className?: string;
  showLabel?: boolean;
}

function Progress({ value, max = 100, color, className, showLabel }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex-1 h-2 rounded-full bg-[var(--surface-2)] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, background: color || "var(--cinnabar)" }}
        />
      </div>
      {showLabel && (
        <span className="text-[11px] font-medium text-[var(--text-3)] tabular-nums w-8 text-right">
          {Math.round(pct)}%
        </span>
      )}
    </div>
  );
}

export { Progress };
