"use client";

import { cn } from "@/lib/utils";
import { createContext, useContext, useState, type ReactNode } from "react";

interface TabsContextValue {
  value: string;
  onChange: (v: string) => void;
}

const TabsContext = createContext<TabsContextValue>({ value: "", onChange: () => {} });

function Tabs({ defaultValue, value, onValueChange, children, className }: {
  defaultValue?: string;
  value?: string;
  onValueChange?: (v: string) => void;
  children: ReactNode;
  className?: string;
}) {
  const [internal, setInternal] = useState(defaultValue || "");
  const current = value ?? internal;
  const onChange = onValueChange ?? setInternal;

  return (
    <TabsContext.Provider value={{ value: current, onChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);

  return (
    <div role="tablist" className={cn(
      "inline-flex items-center gap-1 rounded-lg p-1",
      "bg-[var(--surface-2)] border border-[var(--border)]",
      className
    )} onKeyDown={(e) => {
      const tabs = Array.from((e.currentTarget as HTMLElement).querySelectorAll('[role="tab"]'));
      const vals = tabs.map(t => (t as HTMLElement).dataset.value).filter(Boolean) as string[];
      if (vals.length === 0) return;
      const idx = vals.indexOf(ctx.value);
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        ctx.onChange(vals[(idx + 1) % vals.length]);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        ctx.onChange(vals[(idx - 1 + vals.length) % vals.length]);
      }
    }}>
      {children}
    </div>
  );
}

function TabsTrigger({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  const active = ctx.value === value;

  return (
    <button
      role="tab"
      aria-selected={active}
      tabIndex={active ? 0 : -1}
      data-value={value}
      onClick={() => ctx.onChange(value)}
      className={cn(
        "px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200",
        active
          ? "bg-[var(--surface)] text-[var(--ink)] shadow-sm"
          : "text-[var(--text-3)] hover:text-[var(--text-2)]",
        className
      )}
    >
      {children}
    </button>
  );
}

function TabsContent({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (ctx.value !== value) return null;
  return <div role="tabpanel" className={cn("mt-3 animate-fade-in", className)}>{children}</div>;
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
