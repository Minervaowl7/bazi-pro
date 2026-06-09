"use client";

import { useAnalysisStore } from "@/stores/analysisStore";
import { useEffect, useState, useRef, useCallback } from "react";

/* ── 步骤定义 ── */
interface StepDef {
  id: string;
  label: string;
  desc: string;
}

const STEPS: StepDef[] = [
  { id: "0",  label: "古籍检索",  desc: "检索经典命理文献" },
  { id: "1",  label: "数据校验",  desc: "校验四柱干支与五行属性" },
  { id: "2",  label: "旺衰判定",  desc: "分析日主得令、得地、得势" },
  { id: "3",  label: "格局判定",  desc: "六层筛查确定命局格局" },
  { id: "4",  label: "十神推导",  desc: "推导天干地支十神关系" },
  { id: "4b", label: "喜用神推导", desc: "确定用神、喜神与忌神" },
  { id: "5",  label: "五行力量",  desc: "计算各行力量与分布" },
  { id: "5b", label: "调候查表",  desc: "穷通宝鉴调候用神查表" },
  { id: "7",  label: "刑冲合害",  desc: "检测地支刑冲合害关系" },
];

const WUXING_CYCLE = ["木", "火", "土", "金", "水"];
const WUXING_VAR: Record<string, string> = {
  木: "var(--wx-wood)", 火: "var(--wx-fire)", 土: "var(--wx-earth)", 金: "var(--wx-metal)", 水: "var(--wx-water)",
};

/* ── 计时组件 ── */
function ElapsedTimerInner({ active }: { active: boolean }) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number>(0);

  useEffect(() => {
    if (!active) return;
    startRef.current = Date.now();
    const t = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(t);
  }, [active]);

  if (!active) return null;

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}分${sec.toString().padStart(2, "0")}秒` : `${sec}秒`;
  };

  return (
    <div className="text-right">
      <div className="font-mono tabular-nums text-lg font-light tracking-wider" style={{
        color: "var(--ink)",
        fontVariantNumeric: "tabular-nums",
      }}>
        {fmt(elapsed)}
      </div>
      <div className="text-[10px]" style={{ color: "var(--text-4)" }}>已用时</div>
    </div>
  );
}

/* 计时器包装 — resetKey 变化时强制 remount 归零 */
function ElapsedTimer({ active, resetKey }: { active: boolean; resetKey: number }) {
  return <ElapsedTimerInner key={resetKey} active={active} />;
}

/* ── 主组件 ── */
export default function AnalysisProgress() {
  const { progress, status, error } = useAnalysisStore();
  const [connectWarn, setConnectWarn] = useState(false);
  const [connectTimeout, setConnectTimeout] = useState(false);
  const firstEventRef = useRef(false);

  /* 监听首个进度事件 */
  useEffect(() => {
    if (progress.length > 0) firstEventRef.current = true;
  }, [progress.length]);

  /* 连接超时检测：10秒无事件显示警告，30秒显示超时 */
  useEffect(() => {
    if (status !== "streaming" || firstEventRef.current) return;
    const warnTimer = setTimeout(() => setConnectWarn(true), 10000);
    const timeoutTimer = setTimeout(() => setConnectTimeout(true), 30000);
    return () => { clearTimeout(warnTimer); clearTimeout(timeoutTimer); };
  }, [status]);

  /* 重置状态 */
  useEffect(() => {
    if (status === "idle" || status === "failed") {
      setConnectWarn(false);
      setConnectTimeout(false);
      firstEventRef.current = false;
    }
  }, [status]);

  if (status !== "streaming" && status !== "submitting") return null;

  /* 当前步骤索引 */
  const latestStep = progress[progress.length - 1];
  const currentIdx = latestStep ? STEPS.findIndex((s) => s.id === latestStep.step) : -1;

  /* 五行装饰色轮转 */
  const accentIdx = Math.max(currentIdx, 0) % WUXING_CYCLE.length;
  const accentWuxing = WUXING_CYCLE[accentIdx];

  return (
    <div className="mb-8 relative">
      {/* ── 顶部概览条 ── */}
      <div className="rounded-2xl overflow-hidden mb-4 relative" style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
      }}>
        {/* 顶部装饰金线 */}
        <div style={{
          position: "absolute", top: 0, left: "10%", right: "10%", height: 1,
          background: `linear-gradient(90deg, transparent, color-mix(in srgb, ${WUXING_VAR[accentWuxing]} 38%, transparent), transparent)`,
          transition: "background 0.8s ease",
        }} />

        <div className="px-7 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* 五行旋转指示器 */}
            <div className="relative w-8 h-8 flex items-center justify-center">
              {WUXING_CYCLE.map((wx, i) => {
                const angle = (i * 72) - 90;
                const rad = (angle * Math.PI) / 180;
                const x = 10 + 10 * Math.cos(rad);
                const y = 10 + 10 * Math.sin(rad);
                const isActiveWx = i === accentIdx;
                return (
                  <span
                    key={wx}
                    className="absolute text-[9px] font-bold transition-all duration-500"
                    style={{
                      left: x, top: y,
                      color: isActiveWx ? WUXING_VAR[wx] : "var(--text-4)",
                      opacity: isActiveWx ? 1 : 0.3,
                      transform: isActiveWx ? "scale(1.3)" : "scale(1)",
                    }}
                  >
                    {wx}
                  </span>
                );
              })}
              {/* 中心脉冲点 */}
              <span className="absolute inset-0 m-auto w-2 h-2 rounded-full" style={{
                background: WUXING_VAR[accentWuxing],
                animation: "pulse-soft 2s ease-in-out infinite",
                transition: "background 0.5s",
              }} />
            </div>

            <div>
              <h3 className="text-[15px] font-semibold" style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}>
                命理推演中
              </h3>
              <p className="text-[11px] mt-0.5" style={{ color: connectTimeout ? "var(--danger)" : connectWarn ? "var(--warning)" : "var(--text-4)" }}>
                {currentIdx >= 0
                  ? STEPS[currentIdx]?.desc
                  : connectTimeout
                    ? "连接超时，请检查后端服务是否运行（端口 8711）"
                    : connectWarn
                      ? "正在连接，若长时间无响应请检查后端..."
                      : "正在连接分析引擎..."}
              </p>
            </div>
          </div>

          {/* 计时器 */}
          <ElapsedTimer active={true} resetKey={progress.length} />
        </div>

        {/* 进度条 */}
        <div className="h-0.5 w-full" style={{ background: "var(--surface-2)" }}>
          <div
            className="h-full transition-all duration-1000 ease-out"
            style={{
              width: `${Math.min(
                ((Math.max(currentIdx, 0) + (latestStep?.status === "done" ? 1 : 0.5)) / STEPS.length) * 100,
                95
              )}%`,
              background: `linear-gradient(90deg, ${WUXING_VAR["水"]}, ${WUXING_VAR["木"]})`,
            }}
          />
        </div>
      </div>

      {/* ── 垂直时间线 ── */}
      <div className="rounded-2xl overflow-hidden relative" style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
      }}>
        <div className="px-7 py-6">
          <div className="space-y-0">
            {STEPS.map((step, i) => {
              const stepProgress = progress.find((p) => p.step === step.id);
              const isDone = stepProgress?.status === "done";
              const isRunning = stepProgress?.status === "running" || (i === currentIdx && !isDone);
              const isPending = !isDone && !isRunning;
              const isLast = i === STEPS.length - 1;

              return (
                <div key={step.id} className="flex gap-4" style={{
                  opacity: isPending ? 0.45 : 1,
                  transition: "opacity 0.4s ease",
                }}>
                  {/* 左侧：时间线连接 */}
                  <div className="flex flex-col items-center w-6 shrink-0">
                    {/* 步骤圆点 */}
                    <div className="relative w-5 h-5 flex items-center justify-center">
                      {isDone ? (
                        <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{
                          background: "rgba(74,222,128,0.15)",
                          border: "1.5px solid rgba(74,222,128,0.4)",
                        }}>
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </div>
                      ) : isRunning ? (
                        <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{
                          background: "rgba(96,165,250,0.1)",
                          border: "1.5px solid rgba(96,165,250,0.4)",
                          animation: "pulse-soft 2s ease-in-out infinite",
                        }}>
                          <div className="w-2 h-2 rounded-full" style={{ background: "var(--wx-water)" }} />
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded-full" style={{
                          border: "1.5px solid var(--border-subtle)",
                          background: "var(--surface-2)",
                        }} />
                      )}
                    </div>
                    {/* 连接线 */}
                    {!isLast && (
                      <div className="w-px flex-1 min-h-[20px]" style={{
                        background: isDone ? "rgba(74,222,128,0.25)" : "var(--border-subtle)",
                        transition: "background 0.4s",
                      }} />
                    )}
                  </div>

                  {/* 右侧：步骤内容 */}
                  <div className={isLast ? "pb-1" : "pb-5"}>
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-medium" style={{
                        color: isDone ? "var(--success)" : isRunning ? "var(--wx-water)" : "var(--text-3)",
                        transition: "color 0.3s",
                      }}>
                        {step.label}
                      </span>
                      {isRunning && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{
                          background: "rgba(96,165,250,0.1)",
                          color: "var(--wx-water)",
                          animation: "fade-pulse 2s ease-in-out infinite",
                        }}>
                          分析中
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] mt-1 leading-relaxed" style={{
                      color: isRunning ? "var(--text-2)" : "var(--text-4)",
                      transition: "color 0.3s",
                    }}>
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
