"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { WUXING_COLORS, GAN_WUXING, ZHI_WUXING, RELATION_COLORS } from "@/lib/constants";

interface Relation {
  type?: string;
  elements?: string[];
  description?: string;
}

interface PillarDetail {
  gan?: string;
  zhi?: string;
  wuxing_gan?: string;
  wuxing_zhi?: string;
  [key: string]: unknown;
}

interface Props {
  result: Record<string, unknown>;
}

export default function RelationGraph({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const relations = result.relations as Relation[] | undefined;

  const option = useMemo(() => {
    const pillars = shishen?.pillars || [];
    if (pillars.length < 4 || !relations || relations.length === 0) return null;

    const positions = ["年", "月", "日", "时"];
    const nodes: Array<{
      name: string;
      x: number;
      y: number;
      symbolSize: number;
      itemStyle: { color: string };
      label: { show: boolean; color: string; fontSize: number };
    }> = [];

    pillars.forEach((p, i) => {
      const gan = p.gan || "";
      const zhi = p.zhi || "";
      const ganWx = p.wuxing_gan || GAN_WUXING[gan] || "";
      const zhiWx = p.wuxing_zhi || ZHI_WUXING[zhi] || "";

      nodes.push({
        name: `${positions[i]}干·${gan}`,
        x: i * 120 + 60,
        y: 40,
        symbolSize: 40,
        itemStyle: { color: ganWx ? WUXING_COLORS[ganWx] : "#888" },
        label: { show: true, color: "#f0f0f5", fontSize: 12 },
      });
      nodes.push({
        name: `${positions[i]}支·${zhi}`,
        x: i * 120 + 60,
        y: 160,
        symbolSize: 40,
        itemStyle: { color: zhiWx ? WUXING_COLORS[zhiWx] : "#888" },
        label: { show: true, color: "#f0f0f5", fontSize: 12 },
      });
    });

    const links: Array<{
      source: string;
      target: string;
      lineStyle: { color: string; type: string; width: number };
      label: { show: boolean; formatter: string; color: string; fontSize: number };
    }> = [];

    for (const rel of relations) {
      const desc = rel.description || "";
      const type = rel.type || "";
      const color = RELATION_COLORS[type] || "#888";
      const lineType = type === "冲" ? "dashed" : type === "刑" ? "dotted" : "solid";

      const posMap: Record<string, number> = { 年: 0, 月: 1, 日: 2, 时: 3 };
      const pattern = /([年月日时])([干支])/g;
      let match: RegExpExecArray | null;
      const found: string[] = [];

      while ((match = pattern.exec(desc)) !== null) {
        const pillarIdx = posMap[match[1]];
        const row = match[2] === "干" ? "干" : "支";
        const char = row === "干" ? pillars[pillarIdx]?.gan : pillars[pillarIdx]?.zhi;
        if (pillarIdx !== undefined && char) {
          found.push(`${match[1]}${row}·${char}`);
        }
      }

      if (found.length >= 2) {
        links.push({
          source: found[0],
          target: found[1],
          lineStyle: { color, type: lineType, width: 2 },
          label: { show: true, formatter: type, color, fontSize: 10 },
        });
      }
    }

    if (links.length === 0) return null;

    return {
      backgroundColor: "transparent",
      series: [{
        type: "graph",
        layout: "none",
        data: nodes,
        links,
        roam: false,
        lineStyle: { curveness: 0.2 },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 3 },
        },
      }],
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  if (!option) return null;

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div
        className="px-7 py-4"
        style={{ borderBottom: "1px solid var(--border-subtle)" }}
      >
        <h3
          className="text-sm font-medium"
          style={{ color: "var(--text-muted)" }}
        >
          关系图谱
        </h3>
      </div>
      <div className="px-4 py-4">
        <ReactECharts
          option={option}
          style={{ height: 260, width: "100%" }}
          opts={{ renderer: "svg" }}
        />
      </div>
      <div className="px-7 pb-5 flex items-center gap-4 flex-wrap">
        {Object.entries(RELATION_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span
              className="inline-block w-4 h-0.5 rounded"
              style={{
                background: color,
                borderTop: type === "冲" ? `2px dashed ${color}` : "none",
              }}
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
              {type}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
