"use client";

import { useRef, useEffect, useState, useCallback } from "react";

import {
  WUXING_COLORS,
  WUXING_BG,
  RELATION_COLORS,
  GAN_WUXING,
} from "@/lib/constants";

interface CangganItem {
  gan: string;
  wuxing?: string;
  shishen?: string;
  qi?: string;
}

interface PillarDetail {
  position?: string;
  gan?: string;
  zhi?: string;
  wuxing_gan?: string;
  wuxing_zhi?: string;
  shishen_gan?: string;
  shishen_zhi?: string;
  shishen?: string;
  canggan?: CangganItem[];
}

interface Props {
  result: Record<string, unknown>;
}

interface RelationLine {
  type: string;
  fromPillar: number;
  toPillar: number;
  fromRow: "gan" | "zhi";
  toRow: "gan" | "zhi";
  description: string;
}

interface CellRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

function parseRelation(
  rel: { type?: string; description?: string; elements?: string[] },
  pillars: PillarDetail[]
): RelationLine | null {
  const desc = rel.description || "";
  const type = rel.type || "";

  const positionMap: Record<string, number> = { 年: 0, 月: 1, 日: 2, 时: 3 };

  const positionPattern = /([年月日时])([干支])/g;
  let match: RegExpExecArray | null;
  const positions: { pillar: number; row: "gan" | "zhi" }[] = [];

  while ((match = positionPattern.exec(desc)) !== null) {
    const pillar = positionMap[match[1]];
    const row = match[2] === "干" ? "gan" : "zhi";
    if (pillar !== undefined) {
      positions.push({ pillar, row });
    }
  }

  if (positions.length >= 2) {
    return {
      type,
      fromPillar: positions[0].pillar,
      toPillar: positions[1].pillar,
      fromRow: positions[0].row,
      toRow: positions[1].row,
      description: desc,
    };
  }

  const allGan = pillars.map((p) => p.gan || "");
  const allZhi = pillars.map((p) => p.zhi || "");

  const found: { pillar: number; row: "gan" | "zhi" }[] = [];

  for (let i = 0; i < allGan.length; i++) {
    if (allGan[i] && desc.includes(allGan[i])) {
      found.push({ pillar: i, row: "gan" });
    }
  }

  for (let i = 0; i < allZhi.length; i++) {
    if (allZhi[i] && desc.includes(allZhi[i])) {
      found.push({ pillar: i, row: "zhi" });
    }
  }

  if (found.length >= 2) {
    return {
      type,
      fromPillar: found[0].pillar,
      toPillar: found[1].pillar,
      fromRow: found[0].row,
      toRow: found[1].row,
      description: desc,
    };
  }

  return null;
}

export default function BaziChartCard({ result }: Props) {
  const shishen = result.shishen as { pillars?: PillarDetail[] } | undefined;
  const pillars = shishen?.pillars || [];

  const strength = result.strength as {
    wangshuai?: { verdict?: string; is_weak?: boolean; is_strong?: boolean };
    deling?: { status?: string; score?: number };
    dedi?: { score?: number };
    deshi?: { score?: number };
  } | undefined;
  const wangshuai = strength?.wangshuai;

  const validation = result.validation as {
    day_master?: string;
    bazi?: string;
    gender?: string;
  } | undefined;
  const dayMaster = validation?.day_master || "";
  const elements = result.elements as { percent?: Record<string, number> } | undefined;
  const relations = result.relations as Array<{
    type?: string;
    elements?: string[];
    description?: string;
  }> | undefined;

  const pattern = result.pattern as {
    pattern?: string;
    confidence?: number;
    layer?: number;
    reason?: string;
  } | undefined;

  const formation = (pattern as Record<string, unknown> | undefined)?.formation as {
    has_formation?: boolean;
    type?: string;
    branches?: string[];
    element?: string;
  } | undefined;

  const breakConditions = (pattern as Record<string, unknown> | undefined)?.break_conditions as Array<{
    type?: string;
    severity?: string;
    detail?: string;
  }> | undefined;

  const percent = elements?.percent || {};
  const wuxingOrder = ["木", "火", "土", "金", "水"];

  const allTiangan = pillars.map((p) => p.gan || "");
  const allCanggan = pillars.map((p) => p.canggan || []);

  const isGanTouchu = useCallback(
    (gan: string) => allTiangan.includes(gan),
    [allTiangan]
  );

  const isGanXutou = useCallback(
    (gan: string) => {
      const wx = GAN_WUXING[gan];
      if (!wx) return false;
      return !allCanggan.some((pillarCanggan) =>
        pillarCanggan.some((cg) => cg.wuxing === wx)
      );
    },
    [allCanggan]
  );

  const relationLines = (relations || [])
    .map((r) => parseRelation(r, pillars))
    .filter(Boolean) as RelationLine[];

  const chartRef = useRef<HTMLDivElement>(null);
  const [cellRects, setCellRects] = useState<Record<string, CellRect>>({});
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);
  const [svgReady, setSvgReady] = useState(false);

  const measureCells = useCallback(() => {
    if (!chartRef.current) return;

    const container = chartRef.current;
    const containerRect = container.getBoundingClientRect();
    const rects: Record<string, CellRect> = {};

    container.querySelectorAll("[data-cell]").forEach((el) => {
      const key = el.getAttribute("data-cell")!;
      const rect = el.getBoundingClientRect();
      rects[key] = {
        x: rect.left - containerRect.left,
        y: rect.top - containerRect.top,
        width: rect.width,
        height: rect.height,
      };
    });

    setCellRects(rects);
    setSvgReady(Object.keys(rects).length > 0);
  }, []);

  useEffect(() => {
    measureCells();

    const observer = new ResizeObserver(measureCells);
    if (chartRef.current) {
      observer.observe(chartRef.current);
    }

    return () => observer.disconnect();
  }, [measureCells]);

  useEffect(() => {
    const timer = setTimeout(measureCells, 100);
    return () => clearTimeout(timer);
  }, [measureCells, pillars]);

  function getCellCenter(key: string): { x: number; y: number } | null {
    const rect = cellRects[key];
    if (!rect) return null;
    return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
  }

  function getTooltipStyle(
    line: RelationLine
  ): React.CSSProperties | null {
    const from = getCellCenter(`${line.fromRow}-${line.fromPillar}`);
    const to = getCellCenter(`${line.toRow}-${line.toPillar}`);
    if (!from || !to) return null;

    const midX = (from.x + to.x) / 2;
    const arcHeight = Math.max(20, Math.abs(from.x - to.x) * 0.12);
    const cpY = Math.min(from.y, to.y) - arcHeight;
    const curveMidY = (from.y + 2 * cpY + to.y) / 4;

    return {
      left: midX,
      top: curveMidY - 8,
      transform: "translate(-50%, -100%)",
    };
  }

  const pillarBorder = (i: number): React.CSSProperties =>
    i < 3 ? { borderRight: "1px solid var(--border)" } : {};

  const dayPillarBg = (i: number): React.CSSProperties =>
    i === 2 ? { background: "var(--accent-dim)" } : {};

  return (
    <div className="animate-fade-in space-y-6">
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow)",
        }}
      >
        <div
          className="px-6 py-5 flex items-center justify-between"
          style={{ borderBottom: "1px solid var(--border)" }}
        >
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--accent)" }}
          >
            四柱命盘
          </h2>
          <div className="flex items-center gap-4">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
            >
              {wangshuai?.verdict || "—"}
            </span>
            <span className="text-sm" style={{ color: "var(--text-muted)" }}>
              {dayMaster}日主
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <div ref={chartRef} className="relative" style={{ minWidth: 520 }}>
            <table className="w-full text-center">
              <thead>
                <tr
                  className="text-xs uppercase tracking-wider"
                  style={{
                    color: "var(--text-muted)",
                    background: "var(--bg-secondary)",
                  }}
                >
                  <th
                    className="py-3 px-3 w-16"
                    style={{ borderRight: "1px solid var(--border)" }}
                  ></th>
                  {pillars.map((p, i) => (
                    <th
                      key={i}
                      className="py-3 px-4 font-medium"
                      style={{
                        ...pillarBorder(i),
                        ...dayPillarBg(i),
                      }}
                    >
                      {p.position || ["年柱", "月柱", "日柱", "时柱"][i]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-2.5 text-xs"
                    style={{
                      color: "var(--text-muted)",
                      borderRight: "1px solid var(--border)",
                    }}
                  >
                    十神
                  </td>
                  {pillars.map((p, i) => (
                    <td
                      key={i}
                      className="py-2.5 px-2 text-xs"
                      style={{
                        color: "var(--text-secondary)",
                        ...pillarBorder(i),
                        ...dayPillarBg(i),
                      }}
                    >
                      {i === 2 ? "日主" : p.shishen_gan || p.shishen || "—"}
                    </td>
                  ))}
                </tr>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-2.5 text-xs"
                    style={{
                      color: "var(--text-muted)",
                      borderRight: "1px solid var(--border)",
                    }}
                  >
                    天干
                  </td>
                  {pillars.map((p, i) => {
                    const gan = p.gan || "";
                    const xutou = gan && isGanXutou(gan);
                    return (
                      <td
                        key={i}
                        data-cell={`gan-${i}`}
                        className="py-4 px-2"
                        style={{
                          ...pillarBorder(i),
                          ...dayPillarBg(i),
                        }}
                      >
                        <div className="flex flex-col items-center gap-1">
                          <span
                            className="text-3xl font-bold inline-block px-3 py-1 rounded-lg"
                            style={{
                              color: p.wuxing_gan
                                ? WUXING_COLORS[p.wuxing_gan]
                                : "inherit",
                              border: xutou
                                ? "2px dashed var(--text-muted)"
                                : "none",
                              opacity: xutou ? 0.7 : 1,
                            }}
                          >
                            {gan || "—"}
                          </span>
                          {xutou && (
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                              style={{
                                background: "rgba(128,128,128,0.2)",
                                color: "var(--text-muted)",
                              }}
                            >
                              虚
                            </span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-2.5 text-xs"
                    style={{
                      color: "var(--text-muted)",
                      borderRight: "1px solid var(--border)",
                    }}
                  >
                    地支
                  </td>
                  {pillars.map((p, i) => (
                    <td
                      key={i}
                      data-cell={`zhi-${i}`}
                      className="py-4 px-2"
                      style={{
                        ...pillarBorder(i),
                        ...dayPillarBg(i),
                      }}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span
                          className="text-3xl font-bold inline-block px-3 py-1 rounded-lg"
                          style={{
                            color: p.wuxing_zhi
                              ? WUXING_COLORS[p.wuxing_zhi]
                              : "inherit",
                          }}
                        >
                          {p.zhi || "—"}
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-2.5 text-xs"
                    style={{
                      color: "var(--text-muted)",
                      borderRight: "1px solid var(--border)",
                    }}
                  >
                    十神
                  </td>
                  {pillars.map((p, i) => (
                    <td
                      key={i}
                      className="py-2.5 px-2 text-xs"
                      style={{
                        color: "var(--text-secondary)",
                        ...pillarBorder(i),
                        ...dayPillarBg(i),
                      }}
                    >
                      {p.shishen_zhi || "—"}
                    </td>
                  ))}
                </tr>
                {pillars.some((p) => p.canggan && p.canggan.length > 0) && (
                  <>
                    <tr
                      style={{
                        borderTop: "1px solid var(--border)",
                        background: "var(--bg-secondary)",
                      }}
                    >
                      <td
                        className="py-2 text-xs"
                        style={{
                          color: "var(--text-muted)",
                          borderRight: "1px solid var(--border)",
                        }}
                      >
                        藏干
                      </td>
                      {pillars.map((p, i) => (
                        <td
                          key={i}
                          className="py-2 px-2"
                          style={{
                            ...pillarBorder(i),
                            ...(i === 2
                              ? { background: "rgba(201,169,110,0.06)" }
                              : {}),
                          }}
                        >
                          <div className="flex flex-col items-center gap-1">
                            {(p.canggan || []).map((cg, j) => {
                              const touchu = isGanTouchu(cg.gan);
                              return (
                                <span
                                  key={j}
                                  className="text-sm font-medium inline-flex items-center gap-1"
                                  style={{
                                    color: cg.wuxing
                                      ? WUXING_COLORS[cg.wuxing]
                                      : "inherit",
                                  }}
                                >
                                  {cg.gan}
                                  <span
                                    className="text-[9px] px-1 py-px rounded font-medium leading-none"
                                    style={{
                                      background: touchu
                                        ? "rgba(34,197,94,0.2)"
                                        : "rgba(128,128,128,0.15)",
                                      color: touchu
                                        ? "#22c55e"
                                        : "var(--text-muted)",
                                    }}
                                  >
                                    {touchu ? "透" : "暗"}
                                  </span>
                                </span>
                              );
                            })}
                          </div>
                        </td>
                      ))}
                    </tr>
                    <tr style={{ background: "var(--bg-secondary)" }}>
                      <td
                        className="py-2 text-xs"
                        style={{
                          color: "var(--text-muted)",
                          borderRight: "1px solid var(--border)",
                        }}
                      >
                        十神
                      </td>
                      {pillars.map((p, i) => (
                        <td
                          key={i}
                          className="py-2 px-2"
                          style={{
                            ...pillarBorder(i),
                            ...(i === 2
                              ? { background: "rgba(201,169,110,0.06)" }
                              : {}),
                          }}
                        >
                          <div className="flex flex-col items-center gap-1">
                            {(p.canggan || []).map((cg, j) => (
                              <span
                                key={j}
                                className="text-xs"
                                style={{ color: "var(--text-muted)" }}
                              >
                                {cg.shishen || "—"}
                              </span>
                            ))}
                          </div>
                        </td>
                      ))}
                    </tr>
                  </>
                )}
              </tbody>
            </table>

            {svgReady && relationLines.length > 0 && (
              <svg
                className="absolute inset-0 pointer-events-none"
                style={{
                  width: "100%",
                  height: "100%",
                  overflow: "visible",
                  zIndex: 10,
                }}
              >
                {relationLines.map((line, i) => {
                  const from = getCellCenter(
                    `${line.fromRow}-${line.fromPillar}`
                  );
                  const to = getCellCenter(`${line.toRow}-${line.toPillar}`);
                  if (!from || !to) return null;

                  const midX = (from.x + to.x) / 2;
                  const arcHeight = Math.max(
                    20,
                    Math.abs(from.x - to.x) * 0.12
                  );
                  const cpY = Math.min(from.y, to.y) - arcHeight;
                  const color =
                    RELATION_COLORS[line.type] || "var(--text-muted)";
                  const isClash = line.type === "冲";

                  return (
                    <g key={i}>
                      <path
                        d={`M ${from.x} ${from.y} Q ${midX} ${cpY} ${to.x} ${to.y}`}
                        fill="none"
                        stroke="transparent"
                        strokeWidth={14}
                        style={{ pointerEvents: "stroke" }}
                        onMouseEnter={() => setHoveredLine(i)}
                        onMouseLeave={() => setHoveredLine(null)}
                      />
                      <path
                        d={`M ${from.x} ${from.y} Q ${midX} ${cpY} ${to.x} ${to.y}`}
                        fill="none"
                        stroke={color}
                        strokeWidth={2}
                        strokeDasharray={isClash ? "6 3" : undefined}
                        style={{
                          pointerEvents: "none",
                          animation: isClash
                            ? "dash-flow 0.8s linear infinite"
                            : undefined,
                          opacity: hoveredLine === i ? 1 : 0.6,
                          transition: "opacity 0.2s ease",
                        }}
                      />
                      {hoveredLine === i && (
                        <circle
                          cx={from.x}
                          cy={from.y}
                          r={4}
                          fill={color}
                          style={{ pointerEvents: "none" }}
                        />
                      )}
                      {hoveredLine === i && (
                        <circle
                          cx={to.x}
                          cy={to.y}
                          r={4}
                          fill={color}
                          style={{ pointerEvents: "none" }}
                        />
                      )}
                    </g>
                  );
                })}
              </svg>
            )}

            {hoveredLine !== null && relationLines[hoveredLine] && (
              <div
                className="absolute z-20 px-3 py-2 rounded-lg text-xs pointer-events-none whitespace-nowrap"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  color: "var(--text-secondary)",
                  boxShadow: "var(--shadow)",
                  ...(getTooltipStyle(relationLines[hoveredLine]) || {}),
                }}
              >
                <span
                  className="font-medium"
                  style={{
                    color:
                      RELATION_COLORS[relationLines[hoveredLine].type] ||
                      "var(--accent)",
                  }}
                >
                  {relationLines[hoveredLine].type}
                </span>{" "}
                {relationLines[hoveredLine].description}
              </div>
            )}
          </div>
        </div>

        {relationLines.length > 0 && (
          <div
            className="px-6 py-3 flex items-center gap-4 flex-wrap"
            style={{ borderTop: "1px solid var(--border)" }}
          >
            {Object.entries(RELATION_COLORS).map(([type, color]) => {
              const count = relationLines.filter(
                (l) => l.type === type
              ).length;
              if (count === 0) return null;
              return (
                <div key={type} className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-5 h-0.5 rounded"
                    style={{
                      background: color,
                      borderTop:
                        type === "冲" ? `2px dashed ${color}` : "none",
                    }}
                  />
                  <span
                    className="text-[11px]"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {type}({count})
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div
        className="rounded-2xl p-6"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <h3
          className="text-sm font-semibold mb-5"
          style={{ color: "var(--text-secondary)" }}
        >
          五行力量分布
        </h3>
        <div className="space-y-3">
          {wuxingOrder.map((wx) => {
            const val = percent[wx] || 0;
            return (
              <div key={wx} className="flex items-center gap-3">
                <span
                  className="text-xs font-medium w-7 text-center rounded-md px-1.5 py-0.5"
                  style={{ color: WUXING_COLORS[wx], background: WUXING_BG[wx] }}
                >
                  {wx}
                </span>
                <div
                  className="flex-1 rounded-full"
                  style={{ height: 10, background: "var(--bg-secondary)" }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(val, 100)}%`,
                      background: WUXING_COLORS[wx],
                      opacity: 0.85,
                    }}
                  />
                </div>
                <span
                  className="text-xs w-11 text-right tabular-nums"
                  style={{ color: "var(--text-muted)" }}
                >
                  {val.toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {relations && relations.length > 0 && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            刑冲合害
          </h3>
          <div className="space-y-2.5">
            {relations.map((r, i) => {
              const rColor =
                RELATION_COLORS[r.type || ""] || "var(--accent)";
              return (
                <div key={i} className="flex items-start gap-2.5">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md shrink-0"
                    style={{
                      background: rColor
                        ? `${rColor}20`
                        : "var(--accent-dim)",
                      color: rColor || "var(--accent)",
                    }}
                  >
                    {r.type || "关系"}
                  </span>
                  <span
                    className="text-sm leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {r.description || (r.elements || []).join(" ")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {formation && formation.has_formation && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            方局/三合局
          </h3>
          <div className="flex items-center gap-3">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{
                background: "rgba(251,191,36,0.15)",
                color: "var(--warning)",
              }}
            >
              {formation.type || "会局"}
            </span>
            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              {(formation.branches || []).join(" ")}
            </span>
            <span
              className="text-xs px-2 py-0.5 rounded-md"
              style={{
                color: WUXING_COLORS[formation.element || ""],
                background: WUXING_BG[formation.element || ""],
              }}
            >
              {formation.element}
            </span>
          </div>
        </div>
      )}

      {breakConditions && breakConditions.length > 0 && (
        <div
          className="rounded-2xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h3
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            破格条件
          </h3>
          <div className="space-y-2.5">
            {breakConditions.map((bc, i) => {
              const severityColor =
                bc.severity === "high"
                  ? "var(--danger)"
                  : bc.severity === "medium"
                    ? "var(--warning)"
                    : "var(--text-muted)";
              return (
                <div key={i} className="flex items-start gap-2.5">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md shrink-0 font-medium"
                    style={{
                      background: `${severityColor}20`,
                      color: severityColor,
                    }}
                  >
                    {bc.severity === "high" ? "重" : bc.severity === "medium" ? "中" : "轻"}
                  </span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {bc.type}
                    </span>
                    {bc.detail && (
                      <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        {bc.detail}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
