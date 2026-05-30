"use client";

import { useState } from "react";

interface ShenShaItem {
  name: string;
  position: string;
  type: string;
}

interface Props {
  result: Record<string, unknown>;
}

const TYPE_STYLES: Record<string, { bg: string; color: string }> = {
  吉: { bg: "rgba(74,222,128,0.15)", color: "var(--success)" },
  凶: { bg: "rgba(248,113,113,0.15)", color: "var(--danger)" },
  中: { bg: "rgba(251,191,36,0.15)", color: "var(--warning)" },
};

export default function ShenShaPanel({ result }: Props) {
  const shensha = result.shensha as ShenShaItem[] | undefined;
  const [expanded, setExpanded] = useState(false);

  if (!shensha || shensha.length === 0) return null;

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <button
        className="w-full px-6 py-4 flex items-center justify-between"
        style={{ background: "var(--bg-secondary)" }}
        onClick={() => setExpanded(!expanded)}
      >
        <h3
          className="text-sm font-semibold"
          style={{ color: "var(--text-secondary)" }}
        >
          神煞
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {shensha.length}个
          </span>
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className="transition-transform duration-200"
            style={{
              color: "var(--text-muted)",
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-6 py-4">
          <div className="flex flex-wrap gap-2">
            {shensha.map((item, i) => {
              const style = TYPE_STYLES[item.type] || TYPE_STYLES["中"];
              return (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg"
                  style={{ background: style.bg, color: style.color }}
                >
                  <span className="font-medium">{item.name}</span>
                  <span style={{ opacity: 0.7 }}>({item.position})</span>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
