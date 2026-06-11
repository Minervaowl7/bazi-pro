/* eslint-disable */
// @ts-nocheck
"use client";

import { useEffect, useRef, useMemo } from "react";
import dynamic from "next/dynamic";

const EChartsReact = dynamic(() => import("echarts-for-react"), { ssr: false });

const WUXING_ORDER = ["木", "火", "土", "金", "水"];
const WUXING_HEX: Record<string, string> = {
  木: "#3a7d5c",
  火: "#c4523a",
  土: "#8b6a3a",
  金: "#c5a55a",
  水: "#2e5c8a",
};

function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

interface ReportChartsProps {
  result: Record<string, unknown>;
}

// ──────────────────────────────────────────────
// 1. 五行力量雷达图
// ──────────────────────────────────────────────
function WuxingRadar({ result }: ReportChartsProps) {
  const elements = result.elements as { percent?: Record<string, number> } | undefined;
  const percent = elements?.percent || {};
  const ink = cssVar("--ink", "#2c2418");
  const text2 = cssVar("--text-2", "#6b6154");
  const border = cssVar("--border", "rgba(180,160,120,0.20)");
  const chartRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      chartRef.current?.getEchartsInstance()?.dispose();
    };
  }, []);

  const option = useMemo(() => ({
    tooltip: { trigger: "item" },
    radar: {
      indicator: WUXING_ORDER.map(wx => ({ name: wx, max: 40 })),
      shape: "polygon",
      splitNumber: 4,
      axisName: { color: ink, fontSize: 13, fontWeight: 600 },
      splitLine: { lineStyle: { color: border } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: border } },
    },
    series: [{
      type: "radar",
      data: [{
        value: WUXING_ORDER.map(wx => +(percent[wx] || 0).toFixed(1)),
        name: "五行力量",
        areaStyle: { color: "rgba(201,100,66,0.12)" },
        lineStyle: { color: "#c96442", width: 2 },
        itemStyle: { color: "#c96442" },
      }],
    }],
  }), [percent, ink, border]);

  return (
    <div className="report-chart-card">
      <div className="report-chart-title">五行力量分布</div>
      <EChartsReact ref={chartRef} option={option} style={{ height: 260 }} opts={{ renderer: "svg" }} autoresize={true} />
      <div className="flex justify-center gap-4 mt-2 flex-wrap">
        {WUXING_ORDER.map(wx => (
          <div key={wx} className="flex items-center gap-1.5 text-xs" style={{ color: text2 }}>
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: WUXING_HEX[wx] }} />
            <span>{wx}</span>
            <span className="font-medium" style={{ color: ink }}>{(percent[wx] || 0).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 2. 十神能量柱状图
// ──────────────────────────────────────────────
function ShishenBar({ result }: ReportChartsProps) {
  const shishen = result.shishen as { pillars?: Array<{ shishen_gan?: string; shishen_zhi?: string; canggan?: Array<{ shishen?: string }> }> } | undefined;
  const pillars = shishen?.pillars || [];
  const ink = cssVar("--ink", "#2c2418");
  const text3 = cssVar("--text-3", "#9e9488");
  const border = cssVar("--border", "rgba(180,160,120,0.20)");
  const chartRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      chartRef.current?.getEchartsInstance()?.dispose();
    };
  }, []);

  const counts: Record<string, number> = {};
  for (const p of pillars) {
    if (p.shishen_gan) counts[p.shishen_gan] = (counts[p.shishen_gan] || 0) + 1;
    if (p.shishen_zhi) counts[p.shishen_zhi] = (counts[p.shishen_zhi] || 0) + 1;
    for (const cg of p.canggan || []) {
      if (cg.shishen) counts[cg.shishen] = (counts[cg.shishen] || 0) + 0.5;
    }
  }

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  const option = useMemo(() => {
    if (sorted.length === 0) return null;
    return {
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: 60, right: 20, top: 10, bottom: 24 },
      xAxis: {
        type: "value",
        axisLabel: { color: text3, fontSize: 11 },
        splitLine: { lineStyle: { color: border } },
        axisLine: { show: false },
      },
      yAxis: {
        type: "category",
        data: sorted.map(s => s[0]),
        axisLabel: { color: ink, fontSize: 12, fontWeight: 500 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [{
        type: "bar",
        data: sorted.map((s, i) => ({
          value: +s[1].toFixed(1),
          itemStyle: {
            color: i === 0 ? "#c96442" : i < 3 ? "rgba(201,100,66,0.6)" : "rgba(201,100,66,0.3)",
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barWidth: 18,
        label: {
          show: true,
          position: "right",
          color: ink,
          fontSize: 11,
          fontWeight: 600,
          formatter: "{c}",
        },
      }],
    };
  }, [sorted, ink, text3, border]);

  if (!option) return null;

  return (
    <div className="report-chart-card">
      <div className="report-chart-title">十神能量分布</div>
      <EChartsReact ref={chartRef} option={option} style={{ height: Math.max(200, sorted.length * 36 + 40) }} opts={{ renderer: "svg" }} autoresize={true} />
    </div>
  );
}

// ──────────────────────────────────────────────
// 3. 命局评分仪表盘
// ──────────────────────────────────────────────
function QualityGauge({ result }: ReportChartsProps) {
  const chartQuality = result.chart_quality as Record<string, unknown> | undefined;
  const total = typeof chartQuality?.total === "number" ? chartQuality.total : null;
  const ink = cssVar("--ink", "#2c2418");
  const text3 = cssVar("--text-3", "#9e9488");
  const chartRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      chartRef.current?.getEchartsInstance()?.dispose();
    };
  }, []);

  const getColor = (v: number) => {
    if (v >= 80) return "#3a7d5c";
    if (v >= 60) return "#c5a55a";
    if (v >= 40) return "#c96442";
    return "#c4523a";
  };

  const option = useMemo(() => {
    if (total === null) return null;
    return {
      series: [{
        type: "gauge",
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        radius: "90%",
        progress: { show: true, width: 16, itemStyle: { color: getColor(total) } },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 16, color: [[1, "rgba(180,160,120,0.12)"]] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 32,
          fontWeight: 700,
          fontFamily: "var(--font-display)",
          color: ink,
          offsetCenter: [0, "10%"],
          formatter: "{value}",
        },
        title: {
          fontSize: 12,
          color: text3,
          offsetCenter: [0, "45%"],
        },
        data: [{ value: total, name: "命局评分" }],
      }],
    };
  }, [total, ink, text3]);

  if (!option) return null;

  // 子维度分数
  const dimensions = [
    { key: "geju", label: "格局" },
    { key: "yongshen", label: "用神" },
    { key: "wangshuai", label: "旺衰" },
    { key: "tiaohou", label: "调候" },
  ];

  return (
    <div className="report-chart-card">
      <div className="report-chart-title">命局评分</div>
      <EChartsReact ref={chartRef} option={option} style={{ height: 220 }} opts={{ renderer: "svg" }} autoresize={true} />
      <div className="grid grid-cols-4 gap-2 mt-2">
        {dimensions.map(d => {
          const val = typeof chartQuality?.[d.key] === "number" ? chartQuality[d.key] as number : null;
          return (
            <div key={d.key} className="text-center px-2 py-2 rounded-lg" style={{ background: "var(--surface-2)" }}>
              <div className="text-[10px] mb-1" style={{ color: text3 }}>{d.label}</div>
              <div className="text-sm font-semibold" style={{ color: val !== null ? getColor(val) : text3 }}>
                {val !== null ? val : "—"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 4. 大运时间线
// ──────────────────────────────────────────────
function DayunTimeline({ result }: ReportChartsProps) {
  const dayun = result.dayun as Array<{ age_range?: string; gan?: string; zhi?: string; gan_wuxing?: string; zhi_wuxing?: string }> | undefined;
  const ink = cssVar("--ink", "#2c2418");
  const text3 = cssVar("--text-3", "#9e9488");
  const border = cssVar("--border", "rgba(180,160,120,0.20)");
  const chartRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      chartRef.current?.getEchartsInstance()?.dispose();
    };
  }, []);

  const option = useMemo(() => {
    if (!dayun || dayun.length === 0) return null;
    return {
      tooltip: {
        trigger: "item",
        formatter: (params: { name: string; value: number; dataIndex: number }) => {
          const d = dayun[params.dataIndex];
          if (!d) return "";
          return `<strong>${d.gan || ""}${d.zhi || ""}</strong><br/>${d.age_range || ""}`;
        },
      },
      grid: { left: 40, right: 20, top: 30, bottom: 50 },
      xAxis: {
        type: "category",
        data: dayun.map(d => d.gan + d.zhi),
        axisLabel: {
          color: ink,
          fontSize: 12,
          fontWeight: 600,
          fontFamily: "var(--font-display)",
        },
        axisLine: { lineStyle: { color: border } },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        show: false,
      },
      series: [{
        type: "line",
        data: dayun.map((d, i) => ({
          value: i,
          itemStyle: {
            color: WUXING_HEX[d.gan_wuxing || ""] || "#888",
            borderColor: "#fff",
            borderWidth: 2,
          },
        })),
        symbol: "circle",
        symbolSize: 14,
        lineStyle: { color: "rgba(201,100,66,0.3)", width: 2 },
        label: {
          show: true,
          position: "bottom",
          formatter: (params: { dataIndex: number }) => dayun[params.dataIndex]?.age_range || "",
          color: text3,
          fontSize: 10,
        },
      }],
    };
  }, [dayun, ink, text3, border]);

  if (!option) return null;

  return (
    <div className="report-chart-card">
      <div className="report-chart-title">大运走势</div>
      <EChartsReact ref={chartRef} option={option} style={{ height: 200 }} opts={{ renderer: "svg" }} autoresize={true} />
    </div>
  );
}

// ──────────────────────────────────────────────
// 5. 关系图谱（简化版）
// ──────────────────────────────────────────────
function RelationGraphMini({ result }: ReportChartsProps) {
  const relations = result.relations as Array<{ type?: string; description?: string }> | undefined;
  const text3 = cssVar("--text-3", "#9e9488");
  const ink = cssVar("--ink", "#2c2418");

  if (!relations || relations.length === 0) return null;

  // 按类型分组
  const groups: Record<string, string[]> = {};
  for (const r of relations) {
    const t = r.type || "其他";
    if (!groups[t]) groups[t] = [];
    if (r.description) groups[t].push(r.description);
  }

  const typeColors: Record<string, string> = {
    "冲": "#c4523a",
    "合": "#3a7d5c",
    "刑": "#c96442",
    "害": "#8b6a3a",
    "破": "#c5a55a",
  };

  const typeBgColors: Record<string, string> = {
    "冲": "rgba(196,82,58,0.08)",
    "合": "rgba(58,125,92,0.08)",
    "刑": "rgba(201,100,66,0.08)",
    "害": "rgba(139,106,58,0.08)",
    "破": "rgba(197,165,90,0.08)",
  };

  return (
    <div className="report-chart-card">
      <div className="report-chart-title">刑冲合害关系</div>
      <div className="space-y-3 mt-3">
        {Object.entries(groups).map(([type, descs]) => (
          <div key={type}>
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded"
                style={{
                  background: typeBgColors[type] || "var(--surface-2)",
                  color: typeColors[type] || "var(--text-3)",
                }}
              >
                {type}
              </span>
            </div>
            <div className="space-y-1">
              {descs.map((desc, i) => (
                <div
                  key={i}
                  className="text-xs px-3 py-2 rounded-lg"
                  style={{
                    background: "var(--surface-2)",
                    color: "var(--text-2)",
                    borderLeft: `2px solid ${typeColors[type] || "var(--border)"}`,
                  }}
                >
                  {desc}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// 主组件
// ──────────────────────────────────────────────
export default function ReportCharts({ result }: ReportChartsProps) {
  return (
    <div>
      {/* 图表卡片样式 */}
      <style jsx>{`
        .report-chart-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--r);
          padding: 20px 24px;
        }
        .report-chart-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--ink);
          font-family: var(--font-display);
          margin-bottom: 12px;
          letter-spacing: 0.02em;
        }
      `}</style>

      {/* 上排：雷达图 + 仪表盘 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <WuxingRadar result={result} />
        <QualityGauge result={result} />
      </div>

      {/* 中排：十神能量 + 大运时间线 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <ShishenBar result={result} />
        <DayunTimeline result={result} />
      </div>

      {/* 下排：关系图谱 */}
      <RelationGraphMini result={result} />
    </div>
  );
}
