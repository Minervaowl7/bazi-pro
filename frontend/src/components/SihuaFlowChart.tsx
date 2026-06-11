"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { gsap } from "@/lib/gsap";

/* ════════════════════════════════════════════════════════════════
   紫微四化飞星可视化
   - 12 宫格 SVG 渲染（4×3 传统排列）
   - 四化星彩色标注（化禄绿·化权蓝·化科紫·化忌红）
   - GSAP 飞星轨迹动画（弧线 + 移动光点）
   - 点击宫位显示四化详情面板
   - 暗色模式：全部使用 CSS 变量
   ════════════════════════════════════════════════════════════════ */

/* ── 类型定义 ────────────────────────────────────────────── */

interface SihuaBenming {
  sihua?: Record<string, string>;
  star_sihua_map?: Record<string, string>;
  palace_sihua?: Record<string, string[]>;
}

interface SihuaResult {
  benming?: SihuaBenming;
  [key: string]: unknown;
}

interface PalaceDetail {
  name: string;
  earthlyBranch: string;
  heavenlyStem: string;
}

interface SihuaFlowChartProps {
  /** /api/v2/ziwei/sihua 返回的完整数据 */
  data: SihuaResult;
  /** 可选：十二宫详情（来自 /api/v2/ziwei/chart），用于显示地支 */
  palaces?: PalaceDetail[];
  /** 选中宫位变化回调 */
  onPalaceSelect?: (palaceName: string | null) => void;
}

/* ── 四化配色（CSS 变量，自动适配 dark mode） ────────────── */

const SIHUA_COLORS: Record<string, { color: string; bg: string; label: string }> = {
  化禄: {
    color: "var(--wx-wood)",
    bg: "color-mix(in srgb, var(--wx-wood) 14%, transparent)",
    label: "禄",
  },
  化权: {
    color: "var(--wx-water)",
    bg: "color-mix(in srgb, var(--wx-water) 14%, transparent)",
    label: "权",
  },
  化科: {
    color: "var(--scholar-blue)",
    bg: "color-mix(in srgb, var(--scholar-blue) 14%, transparent)",
    label: "科",
  },
  化忌: {
    color: "var(--wx-fire)",
    bg: "color-mix(in srgb, var(--wx-fire) 14%, transparent)",
    label: "忌",
  },
};

/* ── 12 宫格 4×3 排列（紫微斗数传统布局） ───────────────── */

const GRID_COLS = 4;
const GRID_ROWS = 3;

const PALACE_LAYOUT: string[][] = [
  ["巳", "午", "未", "申"],
  ["辰", "酉", "酉", "酉"], // 占位，实际宫名动态填充
  ["卯", "戌", "戌", "戌"], // 占位
  ["寅", "丑", "子", "亥"],
];

const PALACE_ORDER = [
  "命宫", "兄弟宫", "夫妻宫", "子女宫",
  "财帛宫", "疾厄宫", "迁移宫", "交友宫",
  "官禄宫", "田宅宫", "福德宫", "父母宫",
];

/* ── 宫格坐标计算（百分比） ──────────────────────────────── */

function cellCenter(col: number, row: number): { x: number; y: number } {
  const xPct = (col + 0.5) / GRID_COLS;
  const yPct = (row + 0.5) / GRID_ROWS;
  return { x: xPct * 100, y: yPct * 100 };
}

/** 获取宫位在 4×3 网格中的列/行索引 */
function getPalaceGridPos(index: number): { col: number; row: number } {
  // 上排：巳(0,0) 午(1,0) 未(2,0) 申(3,0)
  // 中左：辰(0,1)   中右：酉(3,1)
  // 中左：卯(0,2)   中右：戌(3,2)
  // 下排：寅(3,3) 丑(2,3) 子(1,3) 亥(0,3) ← 逆序
  const posMap: Array<{ col: number; row: number }> = [
    { col: 0, row: 0 }, // 巳
    { col: 1, row: 0 }, // 午
    { col: 2, row: 0 }, // 未
    { col: 3, row: 0 }, // 申
    { col: 0, row: 1 }, // 辰
    { col: 0, row: 2 }, // 卯
    { col: 3, row: 1 }, // 酉
    { col: 3, row: 2 }, // 戌
    { col: 3, row: 3 }, // 亥
    { col: 2, row: 3 }, // 子
    { col: 1, row: 3 }, // 丑
    { col: 0, row: 3 }, // 寅
  ];
  return posMap[index] ?? { col: 0, row: 0 };
}

/** 生成两点之间的 SVG 弧线路径（贝塞尔曲线） */
function curvedPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  // 弧度与距离成正比，但有上下限
  const curvature = Math.min(dist * 0.3, 12);
  // 法线方向偏移
  const mx = (x1 + x2) / 2 - (dy / dist) * curvature;
  const my = (y1 + y2) / 2 + (dx / dist) * curvature;
  return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

/* ── 主组件 ──────────────────────────────────────────────── */

export default function SihuaFlowChart({
  data,
  palaces,
  onPalaceSelect,
}: SihuaFlowChartProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const animCtxRef = useRef<gsap.Context | null>(null);

  const benming = data.benming;
  const palaceSihua = benming?.palace_sihua ?? {};
  const sihuaMap = benming?.sihua ?? {};

  /* ── 宫位地支查找 ──────────────────────────────────────── */

  const getBranch = useCallback(
    (palaceName: string): string => {
      if (palaces) {
        const p = palaces.find((pp) => pp.name === palaceName);
        return p?.earthlyBranch ?? "";
      }
      // 从 sihua 数据中推断（无则返回空）
      return "";
    },
    [palaces],
  );

  /* ── 宫位点击 ──────────────────────────────────────────── */

  const handlePalaceClick = useCallback(
    (name: string) => {
      const next = selected === name ? null : name;
      setSelected(next);
      onPalaceSelect?.(next);
    },
    [selected, onPalaceSelect],
  );

  /* ── 飞星轨迹动画 ─────────────────────────────────────── */

  useEffect(() => {
    if (!containerRef.current || !palaceSihua || Object.keys(palaceSihua).length === 0) return;

    // 清理上一轮动画
    animCtxRef.current?.revert();

    animCtxRef.current = gsap.context(() => {
      const svg = svgRef.current;
      if (!svg) return;

      // 清除旧的动画元素
      svg.querySelectorAll(".sihua-path, .sihua-dot").forEach((el) => el.remove());

      // 收集飞星路径：从宿主宫 → 四化落入宫
      const flows: Array<{
        sihuaType: string;
        srcPalace: string;
        dstPalace: string;
      }> = [];

      for (const [palaceName, types] of Object.entries(palaceSihua)) {
        for (const sihuaType of types) {
          // 该四化类型的星曜名
          const starName = sihuaMap[sihuaType];
          if (!starName) continue;

          // 查找该星曜所在的源宫位（遍历所有宫位，找该星曜所在的宫）
          let srcPalace = "";
          for (const [pName, pTypes] of Object.entries(palaceSihua)) {
            // 同一宫位且是同一星曜的不同四化 → 不是源
            if (pName === palaceName) continue;
          }
          // 实际上：四化星曜所在的宫位就是 palaceName
          // 飞星方向：四化从年干天干对应的星曜飞入该星曜所在的宫位
          // 所以 src 和 dst 都是同一个宫位——不对，飞星是说：
          // "化禄星飞入某宫"，意思是该四化落入了那个宫位
          // 飞星轨迹应该从命宫（本命四化的出发点）到该宫位
          // 或者从四化源头到落入宫位

          // 简化模型：每条飞星从命宫出发，飞到四化落入的宫位
          srcPalace = "命宫";
          flows.push({ sihuaType, srcPalace, dstPalace: palaceName });
        }
      }

      if (flows.length === 0) return;

      // 绘制飞星路径并创建动画
      const tl = gsap.timeline({ delay: 0.3 });

      for (let i = 0; i < flows.length; i++) {
        const { sihuaType, srcPalace, dstPalace } = flows[i];
        if (srcPalace === dstPalace) continue; // 同宫不画线

        const srcIdx = PALACE_ORDER.indexOf(srcPalace);
        const dstIdx = PALACE_ORDER.indexOf(dstPalace);
        if (srcIdx === -1 || dstIdx === -1) continue;

        const srcPos = getPalaceGridPos(srcIdx);
        const dstPos = getPalaceGridPos(dstIdx);
        const src = cellCenter(srcPos.col, srcPos.row);
        const dst = cellCenter(dstPos.col, dstPos.row);

        // 创建 SVG 弧线路径
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", curvedPath(src.x, src.y, dst.x, dst.y));
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", SIHUA_COLORS[sihuaType]?.color ?? "var(--ink)");
        path.setAttribute("stroke-width", "1.5");
        path.setAttribute("stroke-dasharray", "4 3");
        path.setAttribute("opacity", "0.6");
        path.classList.add("sihua-path");
        svg.appendChild(path);

        const pathLength = path.getTotalLength();
        gsap.set(path, { strokeDashoffset: pathLength });

        // 创建移动光点
        const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        dot.setAttribute("r", "3");
        dot.setAttribute("fill", SIHUA_COLORS[sihuaType]?.color ?? "var(--ink)");
        dot.setAttribute("opacity", "0");
        dot.classList.add("sihua-dot");
        svg.appendChild(dot);

        // 计算弧线控制点（与 curvedPath 一致）
        const dx = dst.x - src.x;
        const dy = dst.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const curvature = Math.min(dist * 0.3, 12);
        const cpx = (src.x + dst.x) / 2 - (dy / dist) * curvature;
        const cpy = (src.y + dst.y) / 2 + (dx / dist) * curvature;

        // 路径描边动画 + 光点沿贝塞尔曲线移动
        const progress = { t: 0 };
        const pos = i * 0.2; // 交错起始时间

        tl.to(
          path,
          { strokeDashoffset: 0, duration: 0.8, ease: "power1.inOut" },
          pos,
        );
        tl.to(
          progress,
          {
            t: 1,
            duration: 0.8,
            ease: "power1.inOut",
            onUpdate: () => {
              // 二次贝塞尔插值
              const t = progress.t;
              const mt = 1 - t;
              const x = mt * mt * src.x + 2 * mt * t * cpx + t * t * dst.x;
              const y = mt * mt * src.y + 2 * mt * t * cpy + t * t * dst.y;
              dot.setAttribute("cx", String(x));
              dot.setAttribute("cy", String(y));
              dot.setAttribute("opacity", String(Math.sin(t * Math.PI))); // 弧形淡入淡出
            },
          },
          pos,
        );
      }

      // 动画结束后移除路径和光点
      tl.call(() => {
        svg.querySelectorAll(".sihua-path, .sihua-dot").forEach((el) => el.remove());
      });
    }, containerRef.current);

    return () => {
      animCtxRef.current?.revert();
    };
  }, [palaceSihua, sihuaMap]);

  /* ── 无数据守卫 ────────────────────────────────────────── */

  if (!benming || Object.keys(palaceSihua).length === 0) {
    return (
      <div className="flex items-center justify-center py-12" style={{ color: "var(--text-3)" }}>
        暂无四化数据
      </div>
    );
  }

  /* ── 选中宫位的四化详情 ────────────────────────────────── */

  const selectedSihua = selected ? palaceSihua[selected] ?? [] : [];

  /* ── 渲染 ──────────────────────────────────────────────── */

  return (
    <div ref={containerRef} className="space-y-4">
      {/* 图例 */}
      <div className="flex flex-wrap items-center gap-4 text-xs" style={{ color: "var(--text-3)" }}>
        {Object.entries(SIHUA_COLORS).map(([type, cfg]) => (
          <span key={type} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ background: cfg.color }}
            />
            <span>{type}</span>
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5 opacity-60">
          <span
            className="inline-block w-4 border-t border-dashed"
            style={{ borderColor: "var(--text-3)" }}
          />
          <span>飞星轨迹</span>
        </span>
      </div>

      {/* 宫格 + SVG 飞星层 */}
      <div
        className="relative overflow-hidden"
        style={{
          borderRadius: "var(--r)",
          border: "1px solid var(--border)",
          background: "var(--surface)",
        }}
      >
        {/* 12 宫格 */}
        <div
          className="grid"
          style={{
            gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)`,
            gridTemplateRows: `repeat(${GRID_ROWS}, 1fr)`,
            aspectRatio: "4 / 3",
          }}
        >
          {PALACE_ORDER.map((name, idx) => {
            const sihuaHere = palaceSihua[name] ?? [];
            const branch = getBranch(name);
            const pos = getPalaceGridPos(idx);
            const isSelected = selected === name;
            const hasSihua = sihuaHere.length > 0;

            return (
              <div
                key={name}
                onClick={() => handlePalaceClick(name)}
                className="relative flex flex-col items-center justify-center p-2 sm:p-3 transition-all duration-200 cursor-pointer select-none"
                style={{
                  gridColumn: pos.col + 1,
                  gridRow: pos.row + 1,
                  borderRight: pos.col < GRID_COLS - 1 ? "1px solid var(--border-subtle)" : "none",
                  borderBottom: pos.row < GRID_ROWS - 1 ? "1px solid var(--border-subtle)" : "none",
                  background: isSelected
                    ? "var(--cinnabar-light)"
                    : hasSihua
                      ? "color-mix(in srgb, var(--gold) 4%, transparent)"
                      : "transparent",
                  outline: isSelected ? "2px solid var(--cinnabar)" : "none",
                  outlineOffset: "-2px",
                  zIndex: isSelected ? 2 : 1,
                }}
              >
                {/* 宫位名 */}
                <span
                  className="text-[11px] sm:text-xs font-medium leading-tight"
                  style={{
                    color: isSelected ? "var(--cinnabar)" : "var(--ink)",
                    fontFamily: "var(--font-display)",
                  }}
                >
                  {name}
                </span>

                {/* 地支（如果有） */}
                {branch && (
                  <span className="text-[10px] mt-0.5" style={{ color: "var(--text-3)" }}>
                    {branch}
                  </span>
                )}

                {/* 四化标记 */}
                {hasSihua && (
                  <div className="flex items-center gap-1 mt-1 flex-wrap justify-center">
                    {sihuaHere.map((type) => {
                      const cfg = SIHUA_COLORS[type];
                      return (
                        <span
                          key={type}
                          className="inline-flex items-center justify-center rounded-full font-bold"
                          style={{
                            width: 18,
                            height: 18,
                            fontSize: 10,
                            background: cfg?.bg ?? "var(--surface-2)",
                            color: cfg?.color ?? "var(--ink)",
                            boxShadow: `0 0 6px color-mix(in srgb, ${cfg?.color ?? "var(--ink)"} 30%, transparent)`,
                          }}
                        >
                          {cfg?.label ?? type.charAt(1)}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* SVG 飞星轨迹层（覆盖在宫格上方） */}
        <svg
          ref={svgRef}
          className="absolute inset-0 pointer-events-none"
          viewBox="0 0 100 75"
          preserveAspectRatio="none"
          style={{ width: "100%", height: "100%", overflow: "visible" }}
        />
      </div>

      {/* 四化详情面板 */}
      {selected && (
        <div
          className="animate-fade-in"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--r)",
            boxShadow: "var(--shadow-sm)",
            padding: "16px 20px",
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <h4
              className="font-semibold text-sm"
              style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}
            >
              {selected}
            </h4>
            {getBranch(selected) && (
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: "var(--surface-2)", color: "var(--text-2)" }}
              >
                {getBranch(selected)}
              </span>
            )}
            <button
              onClick={() => {
                setSelected(null);
                onPalaceSelect?.(null);
              }}
              className="ml-auto text-xs px-2 py-0.5 rounded transition-colors"
              style={{ color: "var(--text-3)" }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "var(--surface-2)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
            >
              关闭
            </button>
          </div>

          {selectedSihua.length > 0 ? (
            <div className="space-y-2">
              {selectedSihua.map((type) => {
                const cfg = SIHUA_COLORS[type];
                const starName = sihuaMap[type] ?? "";
                return (
                  <div
                    key={type}
                    className="flex items-center gap-3 p-2 rounded-lg transition-colors"
                    style={{ background: cfg?.bg ?? "var(--surface-2)" }}
                  >
                    <span
                      className="inline-flex items-center justify-center rounded-full font-bold shrink-0"
                      style={{
                        width: 28,
                        height: 28,
                        fontSize: 13,
                        background: cfg?.color ?? "var(--ink)",
                        color: "var(--surface)",
                      }}
                    >
                      {cfg?.label ?? ""}
                    </span>
                    <div>
                      <span className="text-sm font-medium" style={{ color: "var(--ink)" }}>
                        {type}
                      </span>
                      {starName && (
                        <span className="text-sm ml-2" style={{ color: "var(--text-2)" }}>
                          {starName}星
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-3)" }}>
              此宫位无四化星飞入
            </p>
          )}
        </div>
      )}
    </div>
  );
}
