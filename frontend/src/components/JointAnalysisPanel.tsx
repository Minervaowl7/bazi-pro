"use client";

import { useMemo } from "react";
import BaziChartCard from "@/components/BaziChartCard";
import ZiweiPanel from "@/components/ZiweiPanel";

/* ── 类型定义 ──────────────────────────────────────────────── */

/** 紫微斗数数据结构（与 ZiweiPanel 一致） */
interface ZiweiData {
  soul?: string;
  body?: string;
  fiveElementsClass?: string;
  earthlyBranchOfSoulPalace?: string;
  earthlyBranchOfBodyPalace?: string;
  palaces?: Array<{
    name: string;
    isBodyPalace: boolean;
    heavenlyStem: string;
    earthlyBranch: string;
    majorStars: Array<{ name: string; type: string; brightness?: string | null; mutagen?: string | null }>;
    minorStars: Array<{ name: string; type: string; brightness?: string | null; mutagen?: string | null }>;
    adjectiveStars: Array<{ name: string; type: string; brightness?: string | null; mutagen?: string | null }>;
    changsheng12: string;
    boshi12: string;
  }>;
  [key: string]: unknown;
}

/** 八字分析结果 */
interface AnalysisResult {
  [key: string]: unknown;
}

/** 维度对比数据 */
interface DimensionItem {
  key: string;
  label: string;
  icon: string;
  baziSummary: string;
  ziweiSummary: string;
  verdict?: "吉" | "中" | "凶";
}

/** 综合智能体结果 */
interface AgentInsight {
  source: string;
  dimension: string;
  insight: string;
  confidence?: number;
}

interface JointAnalysisPanelProps {
  /** 八字分析结果 */
  analysisResult: AnalysisResult;
  /** 紫微斗数排盘数据 */
  ziweiData: ZiweiData;
  /** 维度对比数据（可选，外部传入） */
  dimensions?: DimensionItem[];
  /** 综合智能体结果（可选） */
  agentInsights?: AgentInsight[];
}

/* ── 维度对比默认提取逻辑 ──────────────────────────────────── */

/** 从八字结果中提取维度摘要 */
function extractBaziDimension(result: AnalysisResult, key: string): string {
  // 尝试从 narration 中提取
  const narration = result.narration as Record<string, string> | undefined;
  if (narration?.[key]) {
    const text = narration[key];
    // 截取前 80 字符作为摘要
    return text.length > 80 ? text.slice(0, 80) + "…" : text;
  }

  // 从旺衰/格局推导
  const strength = result.strength as { wangshuai?: { verdict?: string } } | undefined;
  const pattern = result.pattern as { pattern?: string } | undefined;
  const yongshen = result.yongshen as { yongshen?: string; xishen?: string[] } | undefined;

  switch (key) {
    case "事业":
      return pattern?.pattern ? `格局：${pattern.pattern}` : "—";
    case "财运":
      return yongshen?.yongshen ? `用神：${yongshen.yongshen}` : "—";
    case "感情":
      return strength?.wangshuai?.verdict ? `旺衰：${strength.wangshuai.verdict}` : "—";
    case "健康":
      return "—";
    default:
      return "—";
  }
}

/** 从紫微数据中提取维度摘要 */
function extractZiweiDimension(data: ZiweiData, key: string): string {
  if (!data.palaces) return "—";

  const palaceMap: Record<string, string> = {
    "事业": "官禄宫",
    "财运": "财帛宫",
    "感情": "夫妻宫",
    "健康": "疾厄宫",
    "人际": "交友宫",
    "家庭": "田宅宫",
  };

  const palaceName = palaceMap[key];
  if (!palaceName) return "—";

  const palace = data.palaces.find((p) => p.name === palaceName);
  if (!palace) return "—";

  const majorStarNames = palace.majorStars.map((s) => s.name).join("、");
  const minorStarNames = palace.minorStars.slice(0, 2).map((s) => s.name).join("、");

  if (majorStarNames) return `主星：${majorStarNames}`;
  if (minorStarNames) return `辅星：${minorStarNames}`;
  return "无主星";
}

/* ── 默认维度 ──────────────────────────────────────────────── */

const DEFAULT_DIMENSIONS: Array<{ key: string; label: string; icon: string }> = [
  { key: "事业", label: "事业", icon: "☰" },
  { key: "财运", label: "财运", icon: "☲" },
  { key: "感情", label: "感情", icon: "☱" },
  { key: "健康", label: "健康", icon: "☳" },
  { key: "人际", label: "人际", icon: "☴" },
  { key: "家庭", label: "家庭", icon: "☷" },
];

/* ── 裁决印章颜色映射 ──────────────────────────────────────── */

const VERDICT_STYLES: Record<string, { color: string; bg: string; border: string }> = {
  吉: { color: "var(--jade)", bg: "rgba(58,125,92,0.08)", border: "rgba(58,125,92,0.20)" },
  中: { color: "var(--gold)", bg: "rgba(180,154,92,0.08)", border: "rgba(180,154,92,0.20)" },
  凶: { color: "var(--cinnabar)", bg: "rgba(201,100,66,0.08)", border: "rgba(201,100,66,0.20)" },
};

/* ── 组件 ──────────────────────────────────────────────────── */

export default function JointAnalysisPanel({
  analysisResult,
  ziweiData,
  dimensions,
  agentInsights,
}: JointAnalysisPanelProps) {
  // 合并外部传入的维度与默认提取
  const resolvedDimensions: DimensionItem[] = useMemo(() => {
    if (dimensions && dimensions.length > 0) return dimensions;

    return DEFAULT_DIMENSIONS.map((d) => ({
      key: d.key,
      label: d.label,
      icon: d.icon,
      baziSummary: extractBaziDimension(analysisResult, d.key),
      ziweiSummary: extractZiweiDimension(ziweiData, d.key),
    }));
  }, [dimensions, analysisResult, ziweiData]);

  // 按来源分组智能体结果
  const groupedInsights = useMemo(() => {
    if (!agentInsights || agentInsights.length === 0) return null;
    const groups: Record<string, AgentInsight[]> = {};
    for (const item of agentInsights) {
      if (!groups[item.source]) groups[item.source] = [];
      groups[item.source].push(item);
    }
    return groups;
  }, [agentInsights]);

  const hasZiweiData = ziweiData.palaces && ziweiData.palaces.length > 0;

  return (
    <div className="space-y-6">
      {/* ===== 八字 + 紫微 并排 ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：八字命盘 */}
        <section className="card overflow-hidden">
          <div className="border-b border-[var(--border)] px-6 py-4 flex items-center gap-2.5 relative bg-[var(--surface-2)]">
            <span
              className="absolute top-0 left-0 right-0 h-[2px]"
              style={{ background: "var(--cinnabar)" }}
            />
            <span
              className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
              style={{ background: "var(--cinnabar-light)", color: "var(--cinnabar)" }}
            >
              ☯
            </span>
            <span className="text-xs font-semibold" style={{ color: "var(--cinnabar)" }}>
              八字命盘
            </span>
          </div>
          <div className="p-4">
            <BaziChartCard result={analysisResult} />
          </div>
        </section>

        {/* 右侧：紫微命盘 */}
        <section className="card overflow-hidden">
          <div className="border-b border-[var(--border)] px-6 py-4 flex items-center gap-2.5 relative bg-[var(--surface-2)]">
            <span
              className="absolute top-0 left-0 right-0 h-[2px]"
              style={{ background: "#a855f7" }}
            />
            <span
              className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
              style={{ background: "rgba(168,85,247,0.12)", color: "#a855f7" }}
            >
              ✧
            </span>
            <span className="text-xs font-semibold" style={{ color: "#a855f7" }}>
              紫微命盘
            </span>
          </div>
          <div className="p-4">
            {hasZiweiData ? (
              <ZiweiPanel data={ziweiData} />
            ) : (
              <div className="py-12 text-center">
                <p className="text-xs text-[var(--text-3)]">暂无紫微排盘数据</p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* ===== 维度对比区域 ===== */}
      <section className="card overflow-hidden">
        <div className="border-b border-[var(--border)] px-6 py-4 flex items-center justify-between bg-[var(--surface-2)]">
          <div className="flex items-center gap-2.5">
            <span
              className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
              style={{ background: "var(--gold)", color: "var(--surface)", opacity: 0.9 }}
            >
              ☰
            </span>
            <span className="text-xs font-semibold text-[var(--ink)]">
              维度对比
            </span>
          </div>
          <span className="text-[10px] px-2.5 py-1 rounded-full font-medium" style={{ background: "var(--surface)", color: "var(--text-3)" }}>
            八字 × 紫微
          </span>
        </div>

        <div className="p-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {resolvedDimensions.map((dim) => {
              const vStyle = dim.verdict ? VERDICT_STYLES[dim.verdict] : null;
              return (
                <div
                  key={dim.key}
                  className="rounded-xl px-5 py-4 bg-[var(--surface-2)] relative overflow-hidden"
                  style={{
                    border: vStyle
                      ? `1px solid ${vStyle.border}`
                      : "1px solid var(--border-subtle)",
                  }}
                >
                  {/* 顶部装饰线 */}
                  {vStyle && (
                    <div
                      className="absolute top-0 left-0 right-0 h-[2px]"
                      style={{ background: vStyle.color }}
                    />
                  )}

                  {/* 维度标题 */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-5 h-5 rounded flex items-center justify-center"
                        style={{
                          fontSize: 11,
                          background: vStyle?.bg || "var(--surface)",
                          color: vStyle?.color || "var(--text-3)",
                        }}
                      >
                        {dim.icon}
                      </span>
                      <span className="text-xs font-semibold text-[var(--ink)]">
                        {dim.label}
                      </span>
                    </div>
                    {dim.verdict && (
                      <span
                        className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                        style={{
                          background: vStyle!.bg,
                          color: vStyle!.color,
                          border: `1px solid ${vStyle!.border}`,
                        }}
                      >
                        {dim.verdict}
                      </span>
                    )}
                  </div>

                  {/* 八字结论 */}
                  <div className="mb-2.5">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span
                        className="w-1.5 h-1.5 rounded-full shrink-0"
                        style={{ background: "var(--cinnabar)" }}
                      />
                      <span className="text-[10px] font-medium text-[var(--text-3)]">八字</span>
                    </div>
                    <p className="text-xs leading-relaxed text-[var(--text-2)] pl-3">
                      {dim.baziSummary || "—"}
                    </p>
                  </div>

                  {/* 紫微结论 */}
                  <div>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span
                        className="w-1.5 h-1.5 rounded-full shrink-0"
                        style={{ background: "#a855f7" }}
                      />
                      <span className="text-[10px] font-medium text-[var(--text-3)]">紫微</span>
                    </div>
                    <p className="text-xs leading-relaxed text-[var(--text-2)] pl-3">
                      {hasZiweiData ? (dim.ziweiSummary || "—") : "—"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ===== 综合智能体结果 ===== */}
      {groupedInsights && (
        <section className="card overflow-hidden">
          <div className="border-b border-[var(--border)] px-6 py-4 flex items-center justify-between bg-[var(--surface-2)]">
            <div className="flex items-center gap-2.5">
              <span
                className="w-6 h-6 rounded-md flex items-center justify-center text-xs"
                style={{ background: "var(--jade)", color: "var(--surface)", opacity: 0.9 }}
              >
                ✦
              </span>
              <span className="text-xs font-semibold text-[var(--ink)]">
                综合智能分析
              </span>
            </div>
            <span className="text-[10px] px-2.5 py-1 rounded-full font-medium" style={{ background: "var(--surface)", color: "var(--text-3)" }}>
              {Object.keys(groupedInsights).length} 源
            </span>
          </div>

          <div className="p-5 space-y-4">
            {Object.entries(groupedInsights).map(([source, items]) => {
              const sourceColors: Record<string, { color: string; bg: string }> = {
                bazi: { color: "var(--cinnabar)", bg: "var(--cinnabar-light)" },
                ziwei: { color: "#a855f7", bg: "rgba(168,85,247,0.12)" },
                joint: { color: "var(--jade)", bg: "rgba(58,125,92,0.10)" },
              };
              const sc = sourceColors[source] || { color: "var(--text-3)", bg: "var(--surface-2)" };

              return (
                <div key={source}>
                  <div className="flex items-center gap-2 mb-2.5">
                    <span
                      className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                      style={{ background: sc.bg, color: sc.color }}
                    >
                      {source === "bazi" ? "八字" : source === "ziwei" ? "紫微" : source === "joint" ? "综合" : source}
                    </span>
                    <span className="text-[10px] text-[var(--text-4)]">{items.length} 条</span>
                  </div>
                  <div className="space-y-2 pl-2">
                    {items.map((item, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2.5 px-4 py-2.5 rounded-lg"
                        style={{ background: "var(--surface-2)" }}
                      >
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded shrink-0 font-medium"
                          style={{ background: sc.bg, color: sc.color }}
                        >
                          {item.dimension}
                        </span>
                        <span className="text-xs leading-relaxed text-[var(--text-2)]">
                          {item.insight}
                        </span>
                        {item.confidence !== undefined && (
                          <span className="text-[10px] tabular-nums text-[var(--text-4)] shrink-0 ml-auto">
                            {(item.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
