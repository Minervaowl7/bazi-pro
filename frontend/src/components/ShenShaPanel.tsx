"use client";

import { useState, useRef, useEffect } from "react";

interface ShenShaItem { name: string; position: string; type: string; desc?: string; }
interface Props { result: Record<string, unknown>; }

const TYPE_ORDER = ["吉", "凶", "中"];
const TYPE_LABELS: Record<string, string> = { "吉": "吉神", "凶": "凶煞", "中": "中性" };
const TYPE_COLORS: Record<string, { dot: string; bg: string; text: string; border: string }> = {
  吉: { dot: "var(--wx-wood)", bg: "rgba(58,125,92,0.06)", text: "var(--wx-wood)", border: "rgba(58,125,92,0.16)" },
  凶: { dot: "var(--wx-fire)", bg: "rgba(196,82,58,0.06)", text: "var(--wx-fire)", border: "rgba(196,82,58,0.16)" },
  中: { dot: "var(--wx-earth)", bg: "rgba(197,165,90,0.06)", text: "var(--wx-earth)", border: "rgba(197,165,90,0.14)" },
};

export default function ShenShaPanel({ result }: Props) {
  const shensha = result.shensha as ShenShaItem[] | undefined;
  const [expanded, setExpanded] = useState(true);
  const [expandedGroup, setExpandedGroup] = useState<Record<string, boolean>>({ "吉": true, "凶": true, "中": true });
  const [activeItem, setActiveItem] = useState<ShenShaItem | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭 tooltip
  useEffect(() => {
    if (!activeItem) return;
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setActiveItem(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [activeItem]);

  if (!shensha || shensha.length === 0) return null;

  const grouped: Record<string, ShenShaItem[]> = {};
  for (const t of TYPE_ORDER) {
    const items = shensha.filter(s => s.type === t);
    if (items.length > 0) grouped[t] = items;
  }

  return (
    <section ref={panelRef} className="card relative" style={{ zIndex: activeItem ? 10 : 1 }}>
      <button
        aria-expanded={expanded}
        className="w-full flex items-center justify-between border-b border-[var(--border)] px-6 py-4 transition-colors duration-150 hover:bg-[var(--surface-2)] rounded-t-xl"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>神煞</h3>
        <div className="flex items-center gap-3">
          <span className="text-[13px]" style={{ color: "var(--text-4)" }}>{shensha.length}个</span>
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="transition-transform duration-200" style={{ color: "var(--text-4)", transform: expanded ? "rotate(180deg)" : "rotate(0)" }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="p-6 space-y-5">
          {Object.entries(grouped).map(([type, items]) => {
            const colors = TYPE_COLORS[type] || TYPE_COLORS["中"];
            const isGroupExpanded = expandedGroup[type] !== false;
            return (
              <div key={type}>
                <button
                  className="flex items-center gap-2 mb-3 w-full text-left"
                  onClick={() => setExpandedGroup(prev => ({ ...prev, [type]: !isGroupExpanded }))}
                  style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
                >
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.dot, flexShrink: 0 }} />
                  <span className="font-semibold" style={{ fontSize: 13, color: "var(--ink)" }}>{TYPE_LABELS[type] || type}</span>
                  <span style={{ fontSize: 11, color: "var(--text-4)" }}>{items.length}个</span>
                  <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="ml-auto transition-transform duration-200" style={{ color: "var(--text-4)", transform: isGroupExpanded ? "rotate(180deg)" : "rotate(0)" }}>
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {isGroupExpanded && (
                  <div className="flex flex-wrap gap-2">
                    {items.map((item, i) => {
                      const isActive = activeItem?.name === item.name && activeItem?.position === item.position;
                      return (
                        <div key={i} style={{ position: "relative" }}>
                          <button
                            onClick={() => setActiveItem(isActive ? null : item)}
                            className="px-3 py-1.5 transition-all duration-200"
                            style={{
                              fontSize: 13,
                              fontWeight: 500,
                              fontFamily: "var(--font-display)",
                              background: isActive ? colors.bg.replace("0.06", "0.15") : colors.bg,
                              color: colors.text,
                              border: `1px solid ${isActive ? colors.text : colors.border}`,
                              borderRadius: 9999,
                              cursor: "pointer",
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.04)"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
                          >
                            {item.name}
                          </button>

                          {isActive && item.desc && (
                            <div
                              style={{
                                position: "absolute",
                                bottom: "calc(100% + 8px)",
                                left: "50%",
                                transform: "translateX(-50%)",
                                width: 280,
                                padding: "12px 14px",
                                background: "var(--surface)",
                                border: "1px solid var(--border-strong)",
                                borderRadius: 10,
                                boxShadow: "var(--shadow-lg)",
                                zIndex: 50,
                                animation: "fadeIn 0.15s ease",
                              }}
                            >
                              {/* 小三角 */}
                              <div style={{
                                position: "absolute",
                                bottom: -6,
                                left: "50%",
                                transform: "translateX(-50%) rotate(45deg)",
                                width: 10,
                                height: 10,
                                background: "var(--surface)",
                                borderRight: "1px solid var(--border-strong)",
                                borderBottom: "1px solid var(--border-strong)",
                              }} />
                              <div className="flex items-center gap-2 mb-1.5">
                                <span className="font-bold" style={{ fontSize: 14, color: colors.text, fontFamily: "var(--font-display)" }}>{item.name}</span>
                                <span style={{ fontSize: 11, color: "var(--text-4)" }}>{item.position}柱</span>
                                <button
                                  onClick={(e) => { e.stopPropagation(); setActiveItem(null); }}
                                  className="ml-auto"
                                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-4)", fontSize: 16, padding: 2, lineHeight: 1 }}
                                >
                                  ×
                                </button>
                              </div>
                              <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--text-2)" }}>
                                {item.desc}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
