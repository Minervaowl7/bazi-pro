"use client";

import { useState } from "react";

/* ── 类型 ─────────────────────────────────────────────────── */

interface NarrationSection {
  key: string;
  title: string;
  icon: string;
  accentColor: string;
  accentBg: string;
  accentBorder: string;
}

interface Props {
  narration: Record<string, string>;
}

/* ── 维度配置 ─────────────────────────────────────────────── */

const SECTIONS: NarrationSection[] = [
  {
    key: "overview",
    title: "命盘总览",
    icon: "☯",
    accentColor: "var(--dim-gold)",
    accentBg: "color-mix(in srgb, var(--dim-gold) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-gold) 15%, transparent)",
  },
  {
    key: "ming_palace",
    title: "命宫分析",
    icon: "★",
    accentColor: "var(--dim-rose)",
    accentBg: "color-mix(in srgb, var(--dim-rose) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-rose) 15%, transparent)",
  },
  {
    key: "pattern",
    title: "格局分析",
    icon: "◆",
    accentColor: "var(--dim-steel)",
    accentBg: "color-mix(in srgb, var(--dim-steel) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-steel) 15%, transparent)",
  },
  {
    key: "sihua",
    title: "四化分析",
    icon: "◈",
    accentColor: "var(--dim-grape)",
    accentBg: "color-mix(in srgb, var(--dim-grape) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-grape) 15%, transparent)",
  },
  {
    key: "wealth",
    title: "财帛宫",
    icon: "◆",
    accentColor: "var(--dim-amber)",
    accentBg: "color-mix(in srgb, var(--dim-amber) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-amber) 15%, transparent)",
  },
  {
    key: "career",
    title: "官禄宫",
    icon: "⚖",
    accentColor: "var(--dim-teal)",
    accentBg: "color-mix(in srgb, var(--dim-teal) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-teal) 15%, transparent)",
  },
  {
    key: "marriage",
    title: "夫妻宫",
    icon: "♥",
    accentColor: "var(--dim-rose)",
    accentBg: "color-mix(in srgb, var(--dim-rose) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-rose) 15%, transparent)",
  },
  {
    key: "health",
    title: "疾厄宫",
    icon: "☘",
    accentColor: "var(--dim-teal)",
    accentBg: "color-mix(in srgb, var(--dim-teal) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-teal) 15%, transparent)",
  },
  {
    key: "summary",
    title: "综合评述",
    icon: "✦",
    accentColor: "var(--dim-gold)",
    accentBg: "color-mix(in srgb, var(--dim-gold) 6%, transparent)",
    accentBorder: "color-mix(in srgb, var(--dim-gold) 15%, transparent)",
  },
];

/* ── 组件 ─────────────────────────────────────────────────── */

export default function ZiweiNarrationPanel({ narration }: Props) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set(["overview", "summary"]));

  const toggle = (key: string) => {
    setExpandedKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // 过滤掉空内容的 section
  const visibleSections = SECTIONS.filter(s => narration[s.key]?.trim());

  if (visibleSections.length === 0) {
    return (
      <section className="card p-6">
        <p style={{ color: "var(--text-3)", fontSize: 15 }}>紫微斗数叙述数据暂未生成。</p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3
          className="font-bold text-base"
          style={{ fontFamily: "var(--font-display)", color: "var(--ink)" }}
        >
          紫微斗数简批
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setExpandedKeys(new Set(visibleSections.map(s => s.key)))}
            style={{ fontSize: 11, color: "var(--text-4)", cursor: "pointer", background: "none", border: "none" }}
          >
            全部展开
          </button>
          <button
            onClick={() => setExpandedKeys(new Set())}
            style={{ fontSize: 11, color: "var(--text-4)", cursor: "pointer", background: "none", border: "none" }}
          >
            全部折叠
          </button>
        </div>
      </div>

      {visibleSections.map(section => {
        const isExpanded = expandedKeys.has(section.key);
        return (
          <section
            key={section.key}
            className="rounded-xl"
            style={{
              background: section.accentBg,
              border: `1px solid ${section.accentBorder}`,
              borderLeft: `4px solid ${section.accentColor}`,
            }}
          >
            <button
              aria-expanded={isExpanded}
              className="w-full flex items-center justify-between px-6 py-4 transition-colors duration-150 hover:bg-[var(--surface-2)]"
              onClick={() => toggle(section.key)}
            >
              <div className="flex items-center gap-3">
                <span
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 14,
                    background: `color-mix(in srgb, ${section.accentColor} 9%, transparent)`,
                    color: section.accentColor,
                  }}
                >
                  {section.icon}
                </span>
                <h3
                  className="font-bold text-base tracking-wide"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  {section.title}
                </h3>
              </div>
              <svg
                aria-hidden="true"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                className="transition-transform duration-200"
                style={{
                  color: "var(--text-4)",
                  transform: isExpanded ? "rotate(180deg)" : "rotate(0)",
                }}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {isExpanded && (
              <div style={{ padding: "0 24px 24px" }}>
                <div
                  style={{
                    fontSize: 15,
                    lineHeight: 1.9,
                    color: "var(--text-2)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {narration[section.key]}
                </div>
              </div>
            )}
          </section>
        );
      })}
    </section>
  );
}
