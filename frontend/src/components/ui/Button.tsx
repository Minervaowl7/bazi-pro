import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "outline" | "danger";
type Size = "sm" | "md" | "lg";

const variantStyles: Record<Variant, string> = {
  primary: "bg-[var(--color-accent)] text-white hover:opacity-90 shadow-sm",
  secondary: "bg-[var(--color-bg-panel)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-bg-panel-hover)]",
  ghost: "text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-panel)] hover:text-[var(--color-text-primary)]",
  outline: "border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-panel)]",
  danger: "bg-[var(--danger)] text-white hover:opacity-90",
};

const sizeStyles: Record<Size, string> = {
  sm: "h-8 px-3 text-xs gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-6 text-sm gap-2",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--water)] focus-visible:ring-offset-1",
        "disabled:pointer-events-none disabled:opacity-50",
        "active:scale-[0.97]",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { Button };
