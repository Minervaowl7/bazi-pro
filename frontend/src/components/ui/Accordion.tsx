"use client";

import { cn } from "@/lib/utils";
import { useState, type ReactNode } from "react";

function Accordion({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("space-y-2", className)}>{children}</div>;
}

function AccordionItem({ title, badge, children, defaultOpen = false, className }: {
  title: ReactNode;
  badge?: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn(
      "rounded-lg border border-[var(--color-border)] overflow-hidden transition-colors",
      open && "border-[var(--border-accent)]",
      className
    )}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-[var(--color-bg-panel)] transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--color-text-primary)]">{title}</span>
          {badge}
        </div>
        <svg
          className={cn("w-4 h-4 text-[var(--color-text-muted)] transition-transform duration-200", open && "rotate-180")}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-4 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}

export { Accordion, AccordionItem };
