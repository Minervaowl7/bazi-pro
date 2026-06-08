/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck -- echarts-for-react types incompatible with React 19
"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { getDayunLiunian } from "@/lib/api";

const EChartsReact = dynamic(() => import("echarts-for-react"), { ssr: false });

interface LiunianScore {
  year: number;
  age: number;
  gan_zhi: string;
  score: number;
  level?: string;
  reason?: string;
}

interface Props {
  analysisId: string;
}

export default function LifeKlineChart({ analysisId }: Props) {
  const [scores, setScores] = useState<LiunianScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [birthYear, setBirthYear] = useState<number>(0);
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    if (!analysisId) return;
    getDayunLiunian(analysisId)
      .then((data) => {
        const list = data.liunian_scores || [];
        setScores(list);
        if (list.length > 0) {
          const first = list[0];
          const by = (first.year || 0) - ((first.age || 1) - 1);
          setBirthYear(by > 1900 && by < 2100 ? by : (first.year || 0));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [analysisId]);

  if (loading) return null;
  if (scores.length === 0) return null;

  const years = scores.map((s) => s.year);
  const scoreValues = scores.map((s) => s.score);
  const yearRange = years[years.length - 1] - years[0] || 1;

  // 计算均线
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

  const option = {
    backgroundColor: "transparent",
    title: {
      text: "百年运势走势",
      left: 0,
      top: 0,
      textStyle: {
        fontSize: 17,
        fontWeight: 700,
        color: "#1c1917",
        fontFamily: '"Noto Serif SC", "Source Han Serif SC", serif',
      },
    },
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "line" as const },
      formatter: (params: Array<{ data?: number; axisValue?: number | string; seriesName?: string; color?: string }>) => {
        const axisYear = typeof params[0]?.axisValue === "number" ? params[0].axisValue : parseInt(String(params[0]?.axisValue), 10);
        const idx = years.findIndex((y) => y === axisYear);
        const item = idx >= 0 ? scores[idx] : null;
        const ganZhi = item?.gan_zhi || "";
        const displayAge = item?.age ?? (birthYear > 0 ? Math.max(1, axisYear - birthYear + 1) : 0);
        const reason = item?.reason || "";

        let html = `<div style="font-family:'SF Pro Text','PingFang SC',sans-serif;line-height:1.7">`;
        html += `<strong style="font-size:14px">${axisYear}年 · ${ganZhi}（${displayAge}岁）</strong><br/>`;

        params.forEach((p) => {
          if (p.data == null) return;
          const color = p.color || "#888";
          html += `<span style="color:${color};font-size:13px">● ${p.seriesName}: <strong>${p.data}</strong></span><br/>`;
        });

        if (reason) {
          html += `<span style="color:#888;font-size:11px;margin-top:4px;display:block">${reason}</span>`;
        }
        html += `</div>`;
        return html;
      },
    },
    legend: {
      data: ["运势分数", "MA5", "MA10"],
      top: 4,
      right: 0,
      textStyle: { fontSize: 11, color: "#a8a29e" },
    },
    grid: {
      top: 50,
      right: 24,
      bottom: 36,
      left: 52,
    },
    xAxis: {
      type: "category" as const,
      data: years,
      axisLabel: {
        fontSize: 11,
        color: "#a8a29e",
        interval: Math.ceil(years.length / 14),
      },
      axisLine: { lineStyle: { color: "rgba(28,25,23,0.08)" } },
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
        color: "#a8a29e",
        formatter: "{value}",
      },
      axisLine: { lineStyle: { color: "rgba(28,25,23,0.08)" } },
      splitLine: {
        lineStyle: {
          color: "rgba(28,25,23,0.05)",
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
        borderColor: "rgba(28,25,23,0.08)",
        backgroundColor: "rgba(28,25,23,0.02)",
        fillerColor: "rgba(45,62,95,0.06)",
        handleStyle: { color: "#2d3e5f" },
        textStyle: { fontSize: 9, color: "#a8a29e" },
      },
    ],
    series: [
      {
        name: "运势分数",
        type: "line" as const,
        data: scoreValues,
        smooth: true,
        symbol: "circle",
        symbolSize: 4,
        lineStyle: {
          color: "#2d5f8f",
          width: 2,
        },
        itemStyle: {
          color: "#2d5f8f",
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
              xAxis: String(currentYear),
              lineStyle: { color: "#b84a3c", width: 1.5, type: "dashed" },
              label: { formatter: "今年", position: "end", fontSize: 11, color: "#b84a3c", fontWeight: 700 },
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
          color: "#c49a42",
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
          color: "#8b5a3c",
          width: 1.5,
          type: "dashed" as const,
        },
      },
    ],
  };

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
        </h3>
        <span style={{ fontSize: 11, color: "var(--text-4)" }}>
          基于用神喜忌计算 · 可滚轮缩放
        </span>
      </div>

      <div style={{ padding: "4px 8px 12px 8px" }}>
        <EChartsReact
          option={option}
          style={{ height: 420 }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>
    </section>
  );
}
