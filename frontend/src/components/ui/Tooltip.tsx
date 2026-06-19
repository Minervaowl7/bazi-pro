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
    const handler = (e: Event) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setShow(false);
    };
    const keyHandler = (e: KeyboardEvent) => { if (e.key === "Escape") setShow(false); };
    document.addEventListener("mousedown", handler);
    document.addEventListener("touchstart", handler);
    document.addEventListener("keydown", keyHandler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("touchstart", handler);
      document.removeEventListener("keydown", keyHandler);
    };
  }, [show]);

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      onClick={() => setShow((s) => !s)}
      aria-describedby={show ? tooltipId : undefined}
    >
      {children}
      {show && (
        <div
          id={tooltipId}
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 -translate-x-1/2 mb-2",
            "px-2.5 py-1.5 rounded-md text-[11px] leading-tight",
            "bg-[var(--ink)] text-[var(--bg)]",
            "shadow-lg max-w-[220px] text-center animate-fade-in",
            className
          )}
          style={{ zIndex: "var(--z-tooltip)" }}
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
