"use client";

import { cn } from "@/lib/utils";
import { useState, useRef, useEffect, useId, type ReactNode } from "react";

function Tooltip({ children, content, className }: {
  children: ReactNode;
  content: ReactNode;
  className?: string;
}) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const tooltipId = useId();

  useEffect(() => {
    if (!show) return;
    const handler = () => setShow(false);
    document.addEventListener("scroll", handler, true);
    return () => document.removeEventListener("scroll", handler, true);
  }, [show]);

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          id={tooltipId}
          role="tooltip"
          className={cn(
            "absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2",
            "px-2.5 py-1.5 rounded-md text-[11px] leading-tight",
            "bg-[var(--ink)] text-[var(--bg)]",
            "shadow-lg whitespace-nowrap animate-fade-in",
            className
          )}
        >
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="w-2 h-2 rotate-45 bg-[var(--ink)]" />
          </div>
        </div>
      )}
    </div>
  );
}

export { Tooltip };
