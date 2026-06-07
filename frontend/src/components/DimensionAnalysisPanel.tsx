"use client";

import { useState } from "react";

interface Tag {
  label: string;
  value: string;
  variant?: "default" | "good" | "warn" | "bad";
}

interface DimensionConfig {
  icon: string;
  title: string;
  accentColor: string;
  accentBg: string;
  accentBorder: string;
}

interface Props {
  dimension: "marriage" | "health" | "wealth" | "family";
  data: Record<string, unknown>;
  narration: string;
}

const DIMENSION_CONFIGS: Record<string, DimensionConfig> = {
  marriage: {
    icon: "♥",
    title: "感情婚姻",
    accentColor: "#e8637a",
    accentBg: "rgba(232,99,122,0.06)",
    accentBorder: "rgba(232,99,122,0.15)",
  },
  health: {
    icon: "☘",
    title: "健康体质",
    accentColor: "#2e9e6a",
    accentBg: "rgba(46,158,106,0.06)",
    accentBorder: "rgba(46,158,106,0.15)",
  },
  wealth: {
    icon: "◆",
    title: "财富财运",
    accentColor: "#c49a2b",
    accentBg: "rgba(196,154,43,0.06)",
    accentBorder: "rgba(196,154,43,0.15)",
  },
  family: {
    icon: "家",
    title: "六亲关系",
    accentColor: "#5e7ab5",
    accentBg: "rgba(94,122,181,0.06)",
    accentBorder: "rgba(94,122,181,0.15)",
  },
};

function extractTags(dimension: string, data: Record<string, unknown>): Tag[] {
  const tags: Tag[] = [];

  if (dimension === "marriage") {
    const ss = data.spouse_star as Record<string, unknown> | undefined;
    if (ss?.name) tags.push({ label: String(ss.gender_context || "配偶星"), value: String(ss.name), variant: "default" });

    const sp = data.spouse_palace as Record<string, unknown> | undefined;
    if (sp?.branch) tags.push({ label: "配偶宫", value: String(sp.branch), variant: "default" });

    const strength = data.spouse_star_strength as Record<string, unknown> | undefined;
    if (strength?.level) tags.push({ label: "星力", value: `${strength.level}`, variant: "default" });

    const tendency = data.romance_tendency as Record<string, boolean> | undefined;
    if (tendency?.stable) tags.push({ label: "倾向", value: "感情稳定", variant: "good" });
    if (tendency?.complex_romance) tags.push({ label: "倾向", value: "感情复杂", variant: "warn" });
    if (tendency?.early_romance) tags.push({ label: "倾向", value: "早恋倾向", variant: "warn" });

    const risks = data.marriage_risks as Array<Record<string, unknown>> | undefined;
    if (risks && risks.length > 0) {
      const high = risks.filter(r => r.severity === "high");
      if (high.length > 0) tags.push({ label: "风险", value: String(high[0].type), variant: "bad" });
    }
  }

  if (dimension === "health") {
    const constitution = data.constitution as Record<string, unknown> | undefined;
    if (constitution?.type) tags.push({ label: "体质", value: String(constitution.type), variant: "default" });

    const score = data.health_score;
    if (typeof score === "number") {
      tags.push({
        label: "评分",
        value: `${score}/100`,
        variant: score >= 70 ? "good" : score >= 50 ? "warn" : "bad",
      });
    }

    const organs = data.organ_risks as Array<Record<string, unknown>> | undefined;
    if (organs && organs.length > 0) {
      for (const o of organs.slice(0, 2)) {
        const riskLevel = String(o.risk_level || "");
        tags.push({
          label: String(o.organ || ""),
          value: String(o.status || ""),
          variant: riskLevel === "high" ? "bad" : riskLevel === "medium" ? "warn" : "default",
        });
      }
    }

    const crises = data.crisis_indicators as Array<Record<string, unknown>> | undefined;
    if (crises && crises.length > 0) tags.push({ label: "危机", value: String(crises[0].type), variant: "bad" });
  }

  if (dimension === "wealth") {
    const tendency = data.income_tendency as Record<string, unknown> | undefined;
    if (tendency?.stable) tags.push({ label: "正财", value: "稳定收入", variant: "good" });
    if (tendency?.windfall) tags.push({ label: "偏财", value: "投资理财", variant: "good" });

    const score = data.wealth_score;
    if (typeof score === "number") {
      tags.push({
        label: "评分",
        value: `${score}/100`,
        variant: score >= 70 ? "good" : score >= 50 ? "warn" : "bad",
      });
    }

    const carry = data.day_master_carry_wealth as Record<string, unknown> | undefined;
    if (carry) {
      tags.push({
        label: "担财",
        value: carry.can_carry ? "身旺能担" : "身弱难担",
        variant: carry.can_carry ? "good" : "warn",
      });
    }

    const patterns = data.wealth_patterns as Array<Record<string, unknown>> | undefined;
    if (patterns && patterns.length > 0) {
      for (const p of patterns.slice(0, 2)) {
        tags.push({
          label: "格局",
          value: String(p.pattern),
          variant: p.quality === "good" ? "good" : p.quality === "bad" ? "bad" : "default",
        });
      }
    }

    const risks = data.wealth_risks as Array<Record<string, unknown>> | undefined;
    if (risks && risks.length > 0) {
      const high = risks.filter(r => r.severity === "high");
      if (high.length > 0) tags.push({ label: "风险", value: String(high[0].type), variant: "bad" });
    }
  }

  if (dimension === "family") {
    for (const [key, label] of [["father", "父缘"], ["mother", "母缘"]] as const) {
      const info = data[key] as Record<string, unknown> | undefined;
      if (info?.star && info?.affinity) {
        tags.push({
          label,
          value: `${info.star}·${info.affinity}`,
          variant: info.affinity === "深" ? "good" : info.affinity === "浅" ? "warn" : "default",
        });
      }
    }

    const siblings = data.siblings as Record<string, unknown> | undefined;
    if (siblings?.count_desc) tags.push({ label: "兄弟", value: String(siblings.count_desc), variant: "default" });

    const children = data.children as Record<string, unknown> | undefined;
    if (children?.affinity) {
      tags.push({
        label: "子女",
        value: children.count_estimate ? String(children.count_estimate).slice(0, 8) : String(children.affinity),
        variant: children.affinity === "深" ? "good" : children.affinity === "浅" ? "warn" : "default",
      });
    }

    const risks = data.family_risks as Array<Record<string, unknown>> | undefined;
    if (risks && risks.length > 0) tags.push({ label: "风险", value: String(risks[0].type), variant: "bad" });
  }

  return tags;
}

const VARIANT_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  default: { bg: "var(--bg-secondary)", color: "var(--color-text-secondary)", border: "var(--color-border-subtle)" },
  good: { bg: "rgba(45,125,91,0.08)", color: "var(--success)", border: "rgba(45,125,91,0.18)" },
  warn: { bg: "rgba(184,146,63,0.08)", color: "var(--warning)", border: "rgba(184,146,63,0.16)" },
  bad: { bg: "rgba(196,60,44,0.08)", color: "var(--danger)", border: "rgba(196,60,44,0.16)" },
};

export default function DimensionAnalysisPanel({ dimension, data, narration }: Props) {
  const [expanded, setExpanded] = useState(true);
  const cfg = DIMENSION_CONFIGS[dimension];
  const tags = extractTags(dimension, data);

  if (!cfg) return null;

  return (
    <section style={{
      background: cfg.accentBg,
      border: `1px solid ${cfg.accentBorder}`,
      boxShadow: "var(--shadow-sm)",
      borderLeft: `4px solid ${cfg.accentColor}`,
    }}>
      <button
        aria-expanded={expanded}
        className="w-full flex items-center justify-between transition-colors duration-150 hover:bg-[var(--bg-hover)]"
        style={{ padding: "16px 24px" }}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: `${cfg.accentColor}18`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            color: cfg.accentColor,
          }}>
            {cfg.icon}
          </span>
          <h3 className="font-bold" style={{
            fontSize: 16,
            color: "var(--color-text-primary)",
            fontFamily: "var(--font-serif)",
            letterSpacing: "0.02em",
          }}>
            {cfg.title}
          </h3>
        </div>
        <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
          className="transition-transform duration-200"
          style={{ color: "var(--color-text-faint)", transform: expanded ? "rotate(180deg)" : "rotate(0)" }}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {expanded && (
        <div style={{ padding: "0 24px 24px" }}>
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2.5" style={{ marginBottom: 16 }}>
              {tags.map((tag, i) => {
                const vs = VARIANT_STYLES[tag.variant || "default"];
                return (
                  <div key={i} className="flex items-center gap-1.5 px-3 py-1.5" style={{
                    fontSize: 13,
                    background: vs.bg,
                    border: `1px solid ${vs.border}`,
                  }}>
                    <span style={{ color: "var(--color-text-faint)", fontSize: 11 }}>{tag.label}</span>
                    <span className="font-semibold" style={{ color: vs.color }}>{tag.value}</span>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{
            fontSize: 15,
            lineHeight: 1.9,
            color: "var(--color-text-secondary)",
            whiteSpace: "pre-wrap",
          }}>
            {narration || "分析数据暂未生成。"}
          </div>
        </div>
      )}
    </section>
  );
}
