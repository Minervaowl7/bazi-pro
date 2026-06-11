/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck -- echarts-for-react types incompatible with React 19
"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { getDayunLiunian } from "@/lib/api";

const EChartsReact = dynamic(() => import("echarts-for-react"), { ssr: false });

/** 读取 CSS 变量值（ECharts 不支持 var()） */
function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

interface LiunianScore {
  year: number;
  age: number;
  gan_zhi: string;
  score: number;
  level?: string;
  reason?: string;
}

interface OHLCScore {
  year: number;
  age: number;
  gan_zhi: string;
  career: number;
  wealth: number;
  love: number;
  health: number;
  overall: number;
}

interface Props {
  analysisId: string;
}

export default function LifeKlineChart({ analysisId }: Props) {
  const [scores, setScores] = useState<LiunianScore[]>([]);
  const [ohlc, setOhlc] = useState<OHLCScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [birthYear, setBirthYear] = useState<number>(0);
  const [chartMode, setChartMode] = useState<"kline" | "line">("kline");
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    if (!analysisId) return;
    getDayunLiunian(analysisId)
      .then((data) => {
        const list = data.liunian_scores || [];
        setScores(list);
        setOhlc(data.ohlc_scores || []);
        if (list.length > 0) {
          const first = list[0];
          const by = (first.year || 0) - ((first.age || 1) - 1);
          setBirthYear(by > 1900 && by < 2100 ? by : (first.year || 0));
        }
      })
      .catch(() => { /* 大运流年数据加载失败，静默处理 */ })
      .finally(() => setLoading(false));
  }, [analysisId]);

  const option = useMemo(() => {
    if (scores.length === 0) return {};

    const years = scores.map((s) => s.year);
    const scoreValues = scores.map((s) => s.score);
    const yearRange = years[years.length - 1] - years[0] || 1;

    // 均线
    const movingAvg = (data: number[], n: number): (number | null)[] =>
      data.map((_, i) => {
        if (i < n - 1) return null;
        const slice = data.slice(i - n + 1, i + 1);
        return Math.round(slice.reduce((a, b) => a + b, 0) / n);
      });
    const ma5 = movingAvg(scoreValues, 5);
    const ma10 = movingAvg(scoreValues, 10);

    const dataMin = Math.min(...scoreValues);
    const dataMax = Math.max(...scoreValues);
    const padding = Math.max((dataMax - dataMin) * 0.15, 10);
    const yMin = Math.max(0, Math.floor(dataMin - padding));
    const yMax = Math.min(100, Math.ceil(dataMax + padding));

    // OHLC K 线数据: [open(上年overall), close(本年overall), low(四维最低), high(四维最高)]
    const klineData = ohlc.length > 0
      ? ohlc.map((item, i) => {
          const open = i > 0 ? ohlc[i - 1].overall : item.overall;
          const close = item.overall;
          const low = Math.min(item.career, item.wealth, item.love, item.health);
          const high = Math.max(item.career, item.wealth, item.love, item.health);
          return [open, close, low, high];
        })
      : [];

    // 当前年份区域标记
    const currentYearIdx = years.indexOf(currentYear);

    const baseOption: Record<string, unknown> = {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis" as const,
        axisPointer: { type: "cross" as const },
        formatter: (params: Array<{ data?: number | number[]; axisValue?: number | string; seriesName?: string; color?: string }>) => {
          const axisYear = typeof params[0]?.axisValue === "number" ? params[0].axisValue : parseInt(String(params[0]?.axisValue), 10);
          const idx = years.findIndex((y) => y === axisYear);
          const item = idx >= 0 ? scores[idx] : null;
          const ohlcItem = idx >= 0 && ohlc[idx] ? ohlc[idx] : null;
          const ganZhi = item?.gan_zhi || ohlcItem?.gan_zhi || "";
          const displayAge = item?.age ?? (birthYear > 0 ? Math.max(1, axisYear - birthYear + 1) : 0);
          const reason = item?.reason || "";
          const isCurrentYear = axisYear === currentYear;

          let html = `<div style="font-family:'SF Pro Text','PingFang SC',sans-serif;line-height:1.7">`;
          html += `<strong style="font-size:14px">${axisYear}年 · ${ganZhi}（${displayAge}岁）</strong>`;
          if (isCurrentYear) html += ` <span style="color:${cssVar("--wx-fire", "#b84a3c")};font-size:12px;font-weight:700">★ 今年</span>`;
          html += `<br/>`;

          if (chartMode === "kline" && ohlcItem) {
            html += `<span style="font-size:12px;color:${cssVar("--text-2", "#666")}">事业: <strong style="color:${cssVar("--wx-water", "#2d5f8f")}">${ohlcItem.career}</strong></span><br/>`;
            html += `<span style="font-size:12px;color:${cssVar("--text-2", "#666")}">财运: <strong style="color:${cssVar("--wx-metal", "#c49a42")}">${ohlcItem.wealth}</strong></span><br/>`;
            html += `<span style="font-size:12px;color:${cssVar("--text-2", "#666")}">感情: <strong style="color:${cssVar("--wx-wood", "#4a8c5c")}">${ohlcItem.love}</strong></span><br/>`;
            html += `<span style="font-size:12px;color:${cssVar("--text-2", "#666")}">健康: <strong style="color:${cssVar("--wx-fire", "#b84a3c")}">${ohlcItem.health}</strong></span><br/>`;
            html += `<span style="font-size:13px;font-weight:700;color:${cssVar("--ink", "#2d3e5f")}">综合: ${ohlcItem.overall}</span><br/>`;
          } else {
            params.forEach((p) => {
              if (p.data == null) return;
              const color = p.color || "#888";
              const val = Array.isArray(p.data) ? p.data[1] : p.data;
              html += `<span style="color:${color};font-size:13px">● ${p.seriesName}: <strong>${val}</strong></span><br/>`;
            });
          }

          if (reason) {
            html += `<span style="color:#888;font-size:11px;margin-top:4px;display:block">${reason}</span>`;
          }
          html += `</div>`;
          return html;
        },
      },
      legend: {
        data: chartMode === "kline" ? ["运势K线", "MA5", "MA10"] : ["运势分数", "MA5", "MA10"],
        top: 4,
        right: 0,
        textStyle: { fontSize: 11, color: cssVar("--text-3", "#a8a29e") },
      },
      grid: {
        top: 36,
        right: 24,
        bottom: 36,
        left: 52,
      },
      xAxis: {
        type: "category" as const,
        data: years,
        axisLabel: {
          fontSize: 11,
          color: cssVar("--text-3", "#a8a29e"),
          interval: Math.ceil(years.length / 14),
        },
        axisLine: { lineStyle: { color: cssVar("--border-subtle", "rgba(28,25,23,0.08)") } },
        splitLine: { show: false },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value" as const,
        min: yMin,
        max: yMax,
        splitNumber: 5,
        axisLabel: {
          fontSize: 11,
          color: cssVar("--text-3", "#a8a29e"),
          formatter: "{value}",
        },
        axisLine: { lineStyle: { color: cssVar("--border-subtle", "rgba(28,25,23,0.08)") } },
        splitLine: {
          lineStyle: {
            color: cssVar("--border-subtle", "rgba(28,25,23,0.05)"),
            type: "solid",
          },
        },
      },
      dataZoom: [
        {
          type: "inside" as const,
          start: Math.max(0, ((currentYear - 20) - years[0]) / yearRange * 100),
          end: Math.min(100, ((currentYear + 20) - years[0]) / yearRange * 100),
          zoomOnMouseWheel: true,
        },
        {
          type: "slider" as const,
          height: 20,
          bottom: 4,
          borderColor: cssVar("--border-subtle", "rgba(28,25,23,0.08)"),
          backgroundColor: cssVar("--surface-2", "rgba(28,25,23,0.02)"),
          fillerColor: cssVar("--wx-water-bg", "rgba(45,62,95,0.06)"),
          handleStyle: { color: cssVar("--ink", "#2d3e5f") },
          textStyle: { fontSize: 9, color: cssVar("--text-3", "#a8a29e") },
        },
      ],
      series: [],
    };

    if (chartMode === "kline" && klineData.length > 0) {
      // K 线蜡烛图
      baseOption.series = [
        {
          name: "运势K线",
          type: "candlestick" as const,
          data: klineData,
          itemStyle: {
            color: cssVar("--wx-wood", "#4a8c5c"),        // 涨（阳线）
            color0: cssVar("--wx-fire", "#b84a3c"),       // 跌（阴线）
            borderColor: cssVar("--wx-wood", "#4a8c5c"),
            borderColor0: cssVar("--wx-fire", "#b84a3c"),
          },
          markLine: {
            silent: true,
            symbol: "none",
            data: [
              {
                xAxis: currentYear,
                lineStyle: { color: cssVar("--wx-fire", "#b84a3c"), width: 2, type: "dashed" },
                label: {
                  formatter: "★ 今年",
                  position: "end",
                  fontSize: 12,
                  color: cssVar("--wx-fire", "#b84a3c"),
                  fontWeight: 700,
                  backgroundColor: "rgba(184,74,60,0.1)",
                  padding: [2, 6],
                  borderRadius: 4,
                },
              },
            ],
          },
          markArea: currentYearIdx >= 0 ? {
            silent: true,
            data: [[
              { xAxis: Math.max(0, currentYearIdx - 2), itemStyle: { color: "rgba(184,74,60,0.04)" } },
              { xAxis: Math.min(years.length - 1, currentYearIdx + 2) },
            ]] as unknown[],
          } : undefined,
        },
        {
          name: "MA5",
          type: "line" as const,
          data: ma5,
          smooth: true,
          symbol: "none",
          lineStyle: {
            color: cssVar("--wx-metal", "#c49a42"),
            width: 1.5,
            type: "dashed" as const,
          },
        },
        {
          name: "MA10",
          type: "line" as const,
          data: ma10,
          smooth: true,
          symbol: "none",
          lineStyle: {
            color: cssVar("--wx-earth", "#8b5a3c"),
            width: 1.5,
            type: "dashed" as const,
          },
        },
      ];
    } else {
      // 折线图（降级）
      baseOption.series = [
        {
          name: "运势分数",
          type: "line" as const,
          data: scoreValues,
          smooth: true,
          symbol: "circle",
          symbolSize: 4,
          lineStyle: {
            color: cssVar("--wx-water", "#2d5f8f"),
            width: 2,
          },
          itemStyle: {
            color: cssVar("--wx-water", "#2d5f8f"),
          },
          areaStyle: {
            color: {
              type: "linear" as const,
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(45,95,143,0.15)" },
                { offset: 1, color: "rgba(45,95,143,0.01)" },
              ],
            },
          },
          markLine: {
            silent: true,
            symbol: "none",
            data: [
              {
                xAxis: currentYear,
                lineStyle: { color: cssVar("--wx-fire", "#b84a3c"), width: 2, type: "dashed" },
                label: {
                  formatter: "★ 今年",
                  position: "end",
                  fontSize: 12,
                  color: cssVar("--wx-fire", "#b84a3c"),
                  fontWeight: 700,
                  backgroundColor: "rgba(184,74,60,0.1)",
                  padding: [2, 6],
                  borderRadius: 4,
                },
              },
            ],
          },
        },
        {
          name: "MA5",
          type: "line" as const,
          data: ma5,
          smooth: true,
          symbol: "none",
          lineStyle: {
            color: cssVar("--wx-metal", "#c49a42"),
            width: 1.5,
            type: "dashed" as const,
          },
        },
        {
          name: "MA10",
          type: "line" as const,
          data: ma10,
          smooth: true,
          symbol: "none",
          lineStyle: {
            color: cssVar("--wx-earth", "#8b5a3c"),
            width: 1.5,
            type: "dashed" as const,
          },
        },
      ];
    }

    return baseOption;
  }, [scores, ohlc, chartMode, birthYear, currentYear]);

  if (loading) return null;
  if (scores.length === 0) return null;

  return (
    <section
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        boxShadow: "var(--shadow-sm)",
      }}
    >
      <div
        style={{
          borderBottom: "2px solid var(--border-strong)",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h3
          className="font-bold"
          style={{
            fontSize: 16,
            color: "var(--ink)",
            fontFamily: "var(--font-display)",
          }}
        >
          百年运势走势
          <span style={{ fontSize: 12, color: "var(--text-4)", fontWeight: 400, marginLeft: 8 }}>
            {currentYear}年
          </span>
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {ohlc.length > 0 && (
            <div style={{ display: "flex", gap: 4 }}>
              <button
                onClick={() => setChartMode("kline")}
                style={{
                  fontSize: 11,
                  padding: "3px 10px",
                  borderRadius: 4,
                  border: `1px solid ${chartMode === "kline" ? cssVar("--wx-fire", "#b84a3c") : cssVar("--border", "#e5e2dd")}`,
                  background: chartMode === "kline" ? "rgba(184,74,60,0.08)" : "transparent",
                  color: chartMode === "kline" ? cssVar("--wx-fire", "#b84a3c") : cssVar("--text-3", "#a8a29e"),
                  cursor: "pointer",
                  fontWeight: chartMode === "kline" ? 600 : 400,
                }}
              >
                K线
              </button>
              <button
                onClick={() => setChartMode("line")}
                style={{
                  fontSize: 11,
                  padding: "3px 10px",
                  borderRadius: 4,
                  border: `1px solid ${chartMode === "line" ? cssVar("--wx-water", "#2d5f8f") : cssVar("--border", "#e5e2dd")}`,
                  background: chartMode === "line" ? "rgba(45,95,143,0.08)" : "transparent",
                  color: chartMode === "line" ? cssVar("--wx-water", "#2d5f8f") : cssVar("--text-3", "#a8a29e"),
                  cursor: "pointer",
                  fontWeight: chartMode === "line" ? 600 : 400,
                }}
              >
                折线
              </button>
            </div>
          )}
          <span style={{ fontSize: 11, color: "var(--text-4)" }}>
            可滚轮缩放
          </span>
        </div>
      </div>

      <div style={{ padding: "4px 8px 12px 8px" }}>
        <EChartsReact
          option={option}
          style={{ height: "min(420px, 60vw)" }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>
    </section>
  );
}
