"use client";

import { useState } from "react";

interface ShenShaItem {
  name: string;
  position: string;
  type: string;
  desc?: string;
}

interface Props {
  result: Record<string, unknown>;
}

const TYPE_STYLES: Record<string, { bg: string; color: string }> = {
  吉: { bg: "rgba(74,222,128,0.12)", color: "var(--success)" },
  凶: { bg: "rgba(251,113,133,0.12)", color: "var(--danger)" },
  中: { bg: "rgba(251,191,36,0.12)", color: "var(--warning)" },
};

const POSITION_ORDER = ["年", "月", "日", "时"];

export default function ShenShaPanel({ result }: Props) {
  const shensha = result.shensha as ShenShaItem[] | undefined;
  const [expanded, setExpanded] = useState(true);

  if (!shensha || shensha.length === 0) return null;

  const grouped: Record<string, ShenShaItem[]> = {};
  for (const pos of POSITION_ORDER) {
    const items = shensha.filter((s) => s.position === pos);
    if (items.length > 0) grouped[pos] = items;
  }

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <button
        className="w-full px-7 py-4 flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <h3
          className="text-sm font-medium"
          style={{ color: "var(--text-muted)" }}
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
        <div className="px-7 py-5 space-y-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          {Object.entries(grouped).map(([pos, items]) => (
            <div key={pos}>
              <div className="text-[11px] font-medium mb-2" style={{ color: "var(--text-muted)" }}>
                {pos}柱
              </div>
              <div className="space-y-2">
                {items.map((item, i) => {
                  const style = TYPE_STYLES[item.type] || TYPE_STYLES["中"];
                  return (
                    <div
                      key={i}
                      className="flex items-start gap-2.5 px-3 py-2 rounded-lg"
                      style={{ background: "var(--bg-secondary)" }}
                    >
                      <span
                        className="text-xs px-2 py-0.5 rounded-md shrink-0 font-medium"
                        style={{ background: style.bg, color: style.color }}
                      >
                        {item.name}
                      </span>
                      {item.desc && (
                        <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                          {item.desc}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
