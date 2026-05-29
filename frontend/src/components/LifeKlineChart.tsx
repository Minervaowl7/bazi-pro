"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";

interface LiunianScore {
  age: number;
  year: number;
  gan_zhi: string;
  score: number;
  dayun?: string;
  reason?: string;
}

interface DayunScore {
  step: number;
  gan_zhi: string;
  score: number;
  age_range: string;
}

interface LifeKlineChartProps {
  liunianScores: LiunianScore[];
  dayunScores?: DayunScore[];
  qiyunAge?: number;
  birthYear?: number;
}

function calcMA(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j];
      }
      result.push(+(sum / period).toFixed(2));
    }
  }
  return result;
}

export default function LifeKlineChart({
  liunianScores,
  dayunScores,
  birthYear,
}: LifeKlineChartProps) {
  const option = useMemo(() => {
    if (!liunianScores || liunianScores.length === 0) return null;

    const sorted = [...liunianScores].sort((a, b) => a.age - b.age);

    const ages = sorted.map((d) => d.age);
    const years = sorted.map((d) => d.year);
    const ganZhis = sorted.map((d) => d.gan_zhi);
    const scores = sorted.map((d) => d.score);
    const dayuns = sorted.map((d) => d.dayun || "");
    const reasons = sorted.map((d) => d.reason || "");

    const candleData: number[][] = [];
    const closeList: number[] = [];

    for (let i = 0; i < sorted.length; i++) {
      const prev = i === 0 ? 50 : closeList[i - 1];
      const curr = scores[i];
      closeList.push(curr);

      const open = prev;
      const close = curr;
      const low = Math.min(open, close) - Math.abs(open - close) * 0.3 - 1;
      const high = Math.max(open, close) + Math.abs(open - close) * 0.3 + 1;

      candleData.push([
        +open.toFixed(2),
        +close.toFixed(2),
        +Math.max(low, 0).toFixed(2),
        +Math.min(high, 100).toFixed(2),
      ]);
    }

    const ma5 = calcMA(closeList, 5);
    const ma10 = calcMA(closeList, 10);

    const dayunMarkLines: Array<{ xAxis: number; name: string }> = [];
    if (dayunScores && dayunScores.length > 0) {
      for (const ds of dayunScores) {
        const rangeMatch = ds.age_range.match(/(\d+)/);
        if (rangeMatch) {
          const startAge = parseInt(rangeMatch[1], 10);
          const idx = ages.indexOf(startAge);
          if (idx >= 0) {
            dayunMarkLines.push({
              xAxis: idx,
              name: ds.gan_zhi,
            });
          }
        }
      }
    }

    const xLabels = ages.map((a) => {
      const yr = birthYear ? birthYear + a - 1 : "";
      return yr ? `${a}岁` : `${a}岁`;
    });

    return {
      backgroundColor: "transparent",
      animation: true,
      animationDuration: 800,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        backgroundColor: "rgba(24,24,42,0.95)",
        borderColor: "var(--border)",
        textStyle: { color: "#edece8", fontSize: 13 },
        formatter: (params: Array<{ seriesName: string; dataIndex: number; value: number | number[] }>) => {
          const idx = params[0]?.dataIndex ?? 0;
          const age = ages[idx];
          const year = years[idx];
          const gz = ganZhis[idx];
          const score = scores[idx];
          const dayun = dayuns[idx];
          const reason = reasons[idx];

          let html = `<div style="font-weight:600;margin-bottom:6px">${age}岁 · ${year}年 · ${gz}</div>`;
          html += `<div>运势评分: <span style="color:#c9a96e;font-weight:600">${score}</span></div>`;
          if (dayun) html += `<div>大运: ${dayun}</div>`;
          if (reason) html += `<div style="color:#a8a4a0;font-size:12px;margin-top:4px">${reason}</div>`;
          return html;
        },
      },
      axisPointer: {
        link: [{ xAxisIndex: "all" }],
        label: { backgroundColor: "#c9a96e" },
      },
      grid: [
        {
          left: 60,
          right: 30,
          top: 30,
          height: "55%",
        },
        {
          left: 60,
          right: 30,
          top: "72%",
          height: "14%",
        },
      ],
      xAxis: [
        {
          type: "category",
          data: xLabels,
          gridIndex: 0,
          axisLine: { lineStyle: { color: "#24243a" } },
          axisLabel: {
            color: "#5a5a6e",
            fontSize: 11,
            interval: 9,
            formatter: (val: string) => val,
          },
          axisTick: { show: false },
          splitLine: { show: false },
        },
        {
          type: "category",
          data: years.map(String),
          gridIndex: 1,
          axisLine: { lineStyle: { color: "#24243a" } },
          axisLabel: {
            color: "#5a5a6e",
            fontSize: 10,
            interval: 9,
          },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          type: "value",
          gridIndex: 0,
          min: 0,
          max: 100,
          splitLine: { lineStyle: { color: "#1c1c30", type: "dashed" } },
          axisLine: { show: false },
          axisLabel: { color: "#5a5a6e", fontSize: 11 },
          axisTick: { show: false },
        },
        {
          type: "value",
          gridIndex: 1,
          min: 0,
          max: 100,
          splitLine: { show: false },
          axisLine: { show: false },
          axisLabel: { show: false },
          axisTick: { show: false },
        },
      ],
      dataZoom: [
        {
          type: "inside",
          xAxisIndex: [0, 1],
          start: 0,
          end: 100,
        },
        {
          type: "slider",
          xAxisIndex: [0, 1],
          bottom: 10,
          height: 24,
          borderColor: "#24243a",
          backgroundColor: "rgba(18,18,30,0.6)",
          fillerColor: "rgba(201,169,110,0.12)",
          handleStyle: { color: "#c9a96e", borderColor: "#c9a96e" },
          textStyle: { color: "#5a5a6e" },
          dataBackground: {
            lineStyle: { color: "#24243a" },
            areaStyle: { color: "rgba(201,169,110,0.06)" },
          },
          selectedDataBackground: {
            lineStyle: { color: "#c9a96e" },
            areaStyle: { color: "rgba(201,169,110,0.15)" },
          },
        },
      ],
      series: [
        {
          name: "运势K线",
          type: "candlestick",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: candleData,
          itemStyle: {
            color: "#22c55e",
            color0: "#ef4444",
            borderColor: "#22c55e",
            borderColor0: "#ef4444",
          },
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: {
              color: "rgba(255,255,255,0.25)",
              type: "dashed",
              width: 1,
            },
            label: {
              color: "#a8a4a0",
              fontSize: 11,
              position: "insideEndTop",
              formatter: (params: { name?: string }) => params.name || "",
            },
            data: dayunMarkLines.map((ml) => ({
              xAxis: ml.xAxis,
              name: ml.name,
            })),
          },
        },
        {
          name: "MA5",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: ma5,
          smooth: true,
          showSymbol: false,
          lineStyle: { color: "#eab308", width: 1.5 },
          itemStyle: { color: "#eab308" },
        },
        {
          name: "MA10",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: ma10,
          smooth: true,
          showSymbol: false,
          lineStyle: { color: "#3b82f6", width: 1.5 },
          itemStyle: { color: "#3b82f6" },
        },
        {
          name: "评分",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: scores,
          itemStyle: {
            color: (params: { dataIndex: number }) => {
              const idx = params.dataIndex;
              if (idx === 0) return scores[0] >= 50 ? "#22c55e" : "#ef4444";
              return scores[idx] >= scores[idx - 1] ? "#22c55e" : "#ef4444";
            },
          },
        },
      ],
    };
  }, [liunianScores, dayunScores, birthYear]);

  if (!option) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <h3 className="text-base font-semibold mb-4" style={{ color: "var(--accent)" }}>
          人生K线
        </h3>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          暂无流年数据
        </p>
      </div>
    );
  }

  return (
    <div
      className="rounded-2xl p-6 animate-fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold" style={{ color: "var(--accent)" }}>
          人生K线
        </h3>
        <div className="flex items-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
          <span className="flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ background: "#22c55e" }}
            />
            吉运
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ background: "#ef4444" }}
            />
            凶运
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className="inline-block w-4 h-0.5"
              style={{ background: "#eab308" }}
            />
            MA5
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className="inline-block w-4 h-0.5"
              style={{ background: "#3b82f6" }}
            />
            MA10
          </span>
        </div>
      </div>
      <ReactECharts
        option={option}
        style={{ height: 420, width: "100%" }}
        notMerge
        lazyUpdate
      />
    </div>
  );
}
