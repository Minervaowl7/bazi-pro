/* eslint-disable */
// @ts-nocheck
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";
import AnalysisProgress from "@/components/AnalysisProgress";
import BaziChartCard from "@/components/BaziChartCard";
import DailyFortuneCard from "@/components/DailyFortuneCard";
import ShareCard from "@/components/ShareCard";
import StrengthSlider from "@/components/StrengthSlider";
import ShishenEnergyChart from "@/components/ShishenEnergyChart";
import RelationGraph from "@/components/RelationGraph";
import SchoolPanel from "@/components/SchoolPanel";
import SchoolComparePanel from "@/components/SchoolComparePanel";
import DayunTimeline from "@/components/DayunTimeline";
import GongweiPanel from "@/components/GongweiPanel";
import ShenShaPanel from "@/components/ShenShaPanel";
import ChatPanel from "@/components/ChatPanel";
import ExportPanel from "@/components/ExportPanel";
import LifeKlineChart from "@/components/LifeKlineChart";
import { SCHOOL_OPTIONS_WITH_ALL } from "@/lib/constants";
import { generateReport } from "@/lib/api";

const SCHOOL_OPTIONS = SCHOOL_OPTIONS_WITH_ALL;

function SkeletonCard() {
  return (
    <div
      className="rounded-2xl p-8 mb-8 animate-pulse"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div
        className="h-5 rounded-md w-1/4 mb-6"
        style={{ background: "var(--bg-hover)" }}
      />
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="text-center p-5 rounded-xl"
            style={{ background: "var(--bg-secondary)" }}
          >
            <div
              className="h-3 rounded-md w-14 mx-auto mb-3"
              style={{ background: "var(--bg-hover)" }}
            />
            <div
              className="h-9 rounded-md w-10 mx-auto mb-2"
              style={{ background: "var(--bg-hover)" }}
            />
            <div
              className="h-9 rounded-md w-10 mx-auto mb-2"
              style={{ background: "var(--bg-hover)" }}
            />
            <div
              className="h-3 rounded-md w-12 mx-auto"
              style={{ background: "var(--bg-hover)" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function SkeletonNarration() {
  return (
    <div className="space-y-4 mb-8">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-r-xl p-6 animate-pulse"
          style={{
            background: "var(--bg-card)",
            borderLeft: "2px solid var(--border)",
          }}
        >
          <div
            className="h-4 rounded-md w-1/5 mb-4"
            style={{ background: "var(--bg-hover)" }}
          />
          <div className="space-y-3">
            <div
              className="h-3 rounded-md w-full"
              style={{ background: "var(--bg-hover)" }}
            />
            <div
              className="h-3 rounded-md w-5/6"
              style={{ background: "var(--bg-hover)" }}
            />
            <div
              className="h-3 rounded-md w-4/6"
              style={{ background: "var(--bg-hover)" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalyzePage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;
  const {
    status,
    result,
    error,
    analysisId: storeAnalysisId,
    birthInput,
    fetchResult,
    startAnalysis,
    reset,
  } = useAnalysisStore();
  const prevIdRef = useRef<string | null>(null);
  const [selectedSchool, setSelectedSchool] = useState("ziping");
  const [schoolDropdownOpen, setSchoolDropdownOpen] = useState(false);
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [reportMsg, setReportMsg] = useState("");

  useEffect(() => {
    if (!analysisId) return;
    if (analysisId !== prevIdRef.current) {
      prevIdRef.current = analysisId;
      if (analysisId !== storeAnalysisId) {
        reset();
        fetchResult(analysisId);
      }
    } else if (status === "idle") {
      fetchResult(analysisId);
    }
  }, [analysisId, status, storeAnalysisId, fetchResult, reset]);

  useEffect(() => {
    if (!schoolDropdownOpen) return;
    const handler = () => setSchoolDropdownOpen(false);
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [schoolDropdownOpen]);

  const handleReanalyze = useCallback(async () => {
    if (!birthInput) return;
    try {
      const newId = await startAnalysis({
        ...birthInput,
        school: selectedSchool,
      });
      router.push(`/analyze/${newId}`);
    } catch {}
  }, [birthInput, selectedSchool, startAnalysis, router]);

  const handleGenerateReport = useCallback(async () => {
    if (reportStatus === "loading") return;
    setReportStatus("loading");
    setReportMsg("");
    try {
      const report = await generateReport(analysisId);
      if (report.sections) {
        const text = Object.entries(report.sections).map(([t, c]) => `## ${t}\n\n${c}`).join("\n\n");
        await navigator.clipboard.writeText(text).catch(() => {
          const ta = document.createElement("textarea");
          ta.value = text;
          ta.style.cssText = "position:fixed;left:-9999px";
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        });
        setReportStatus("done");
        setReportMsg("报告已复制到剪贴板");
      } else {
        setReportStatus("error");
        setReportMsg("报告生成失败，请稍后重试");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("LLM") || msg.includes("503")) {
        setReportMsg("需配置 LLM_API_KEY 环境变量（见 .env.example）");
      } else if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setReportMsg("无法连接服务器，请检查后端是否运行");
      } else {
        setReportMsg(msg || "生成失败，请稍后重试");
      }
      setReportStatus("error");
    }
    setTimeout(() => {
      setReportStatus("idle");
      setReportMsg("");
    }, 4000);
  }, [analysisId, reportStatus]);

  const analysisResult = result?.result as
    | Record<string, unknown>
    | undefined;
  const narration = (result as Record<string, unknown> | null)?.narration as
    | Record<string, unknown>
    | undefined;

  const isLoading = status === "submitting" || status === "streaming";

  const strength = analysisResult?.strength as {
    wangshuai?: { verdict?: string; is_weak?: boolean; is_strong?: boolean };
  } | undefined;
  const wangshuai = strength?.wangshuai;

  const pattern = analysisResult?.pattern as {
    pattern?: string;
    confidence?: number;
    layer?: number;
    reason?: string;
  } | undefined;

  const yongshen = analysisResult?.yongshen as {
    yongshen?: string;
    xishen?: string[];
    jishen?: string[];
    yongshen_gan?: string;
    xishen_gan?: string[];
    jishen_gan?: string[];
    trace?: { method?: string; reason?: string };
  } | undefined;

  const tiaohou = analysisResult?.tiaohou as {
    has_tiaohou?: boolean;
    tiaohou_gan?: string[];
    tiaohou_wx?: string[];
  } | undefined;

  const schoolAnalyses = analysisResult?.school_analyses as Record<string, unknown> | undefined;
  const currentSchool = (analysisResult?.school as string) || "ziping";
  const isCompareMode = currentSchool === "all";

  return (
    <div className="min-h-screen" style={{ background: "var(--background)" }}>
      <main className="flex-1 overflow-y-auto">
        <div className="w-full px-6 md:px-12 lg:px-16 xl:px-24 py-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setSchoolDropdownOpen(!schoolDropdownOpen); }}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-text-secondary)",
                  }}
                >
                  {SCHOOL_OPTIONS.find((s) => s.value === currentSchool)?.label || "传统子平"}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transform: schoolDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                {schoolDropdownOpen && (
                  <div
                    className="absolute right-0 top-full mt-2 w-64 rounded-xl overflow-hidden z-50 animate-fade-in"
                    style={{
                      background: "var(--bg-card)",
                      border: "1px solid var(--border)",
                      boxShadow: "var(--shadow)",
                    }}
                  >
                    {SCHOOL_OPTIONS.map((s) => (
                      <button
                        key={s.value}
                        onClick={() => {
                          setSelectedSchool(s.value);
                          setSchoolDropdownOpen(false);
                        }}
                        className="w-full px-4 py-3 text-left transition-colors duration-150 hover:bg-[var(--bg-hover)]"
                        style={{
                          background: selectedSchool === s.value ? "var(--accent-dim)" : "transparent",
                        }}
                      >
                        <div
                          className="text-sm font-medium"
                          style={{
                            color: selectedSchool === s.value ? "var(--water)" : "var(--text-primary)",
                          }}
                        >
                          {s.label}
                        </div>
                        <div
                          className="text-xs mt-0.5"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {s.desc}
                        </div>
                      </button>
                    ))}
                    <div style={{ borderTop: "1px solid var(--border)" }}>
                      <button
                        onClick={() => {
                          setSchoolDropdownOpen(false);
                          handleReanalyze();
                        }}
                        disabled={!birthInput || isLoading}
                        className="w-full px-4 py-3 text-sm font-medium transition-colors duration-150 disabled:opacity-50"
                        style={{
                          color: "var(--water)",
                        }}
                      >
                        以「{SCHOOL_OPTIONS.find((s) => s.value === selectedSchool)?.label}」重新分析
                      </button>
                    </div>
                  </div>
                )}
              </div>
              {analysisResult && (
                <>
                  <button
                    onClick={handleGenerateReport}
                    disabled={reportStatus === "loading"}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:shadow-sm disabled:opacity-60"
                    style={{
                      background: "var(--bg-elevated)",
                      color: "var(--text-primary)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                    {reportStatus === "loading" ? "生成中..." : "生成详批报告"}
                  </button>
                  {reportMsg && (
                    <span
                      className="text-xs px-2 py-1 rounded-lg"
                      style={{
                        color: reportStatus === "error" ? "var(--danger)" : "var(--success)",
                        background: reportStatus === "error" ? "rgba(248,113,113,0.1)" : "rgba(74,222,128,0.1)",
                      }}
                    >
                      {reportMsg}
                    </span>
                  )}
                  <ExportPanel
                    analysisId={analysisId}
                    result={analysisResult}
                    narration={narration}
                  />
                  <ShareCard result={analysisResult} />
                </>
              )}
            </div>
          </div>

          {isLoading && <AnalysisProgress />}

          {status === "failed" && (
            <div
              className="rounded-xl p-6 mb-8"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--danger)",
              }}
            >
              <h3
                className="font-medium mb-2"
                style={{ color: "var(--danger)" }}
              >
                分析失败
              </h3>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {error || "未知错误"}
              </p>
            </div>
          )}

          {(isLoading || (!analysisResult && status !== "failed")) && (
            <>
              {!isLoading && (
                <div
                  className="rounded-xl p-5 mb-6 flex items-center gap-3"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border)",
                  }}
                >
                  <span
                    className="w-2 h-2 rounded-full animate-pulse shrink-0"
                    style={{ background: "var(--water)" }}
                  />
                  <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                    正在加载分析结果...
                  </span>
                </div>
              )}
              <SkeletonCard />
              <SkeletonNarration />
            </>
          )}

          {analysisResult ? (
            <div className="space-y-8 stagger-in">
              {/* 顶部摘要栏 */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                >
                  <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>旺衰</div>
                  <div className="text-base font-bold" style={{ color: "var(--text-primary)" }}>{wangshuai?.verdict || "—"}</div>
                </div>
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                >
                  <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>格局</div>
                  <div className="text-base font-bold" style={{ color: "var(--text-primary)" }}>{pattern?.pattern || "—"}</div>
                </div>
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.15)" }}
                >
                  <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--success)" }}>用神</div>
                  <div className="text-base font-bold" style={{ color: "var(--success)" }}>{yongshen?.yongshen || "—"}</div>
                </div>
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "rgba(96,165,250,0.06)", border: "1px solid rgba(96,165,250,0.12)" }}
                >
                  <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--water)" }}>喜神</div>
                  <div className="text-sm font-bold" style={{ color: "var(--water)" }}>{(yongshen?.xishen || []).join(" ") || "—"}</div>
                </div>
                <div
                  className="rounded-xl p-4 text-center"
                  style={{ background: "rgba(251,113,133,0.06)", border: "1px solid rgba(251,113,133,0.12)" }}
                >
                  <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--danger)" }}>忌神</div>
                  <div className="text-sm font-bold" style={{ color: "var(--danger)" }}>{(yongshen?.jishen || []).join(" ") || "—"}</div>
                </div>
                {tiaohou?.has_tiaohou && (
                  <div
                    className="rounded-xl p-4 text-center"
                    style={{ background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.12)" }}
                  >
                    <div className="text-[11px] mb-1.5 font-medium" style={{ color: "var(--warning)" }}>调候</div>
                    <div className="text-sm font-bold" style={{ color: "var(--warning)" }}>{(tiaohou.tiaohou_gan || []).join(" ")}</div>
                  </div>
                )}
              </div>

              {/* 今日运势 */}
              <DailyFortuneCard analysisId={analysisId} />

              {/* 四柱命盘 — 全宽 */}
              <BaziChartCard result={analysisResult} />

              {/* 双栏区：日主强弱 + 十神能量 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <StrengthSlider
                  verdict={wangshuai?.verdict}
                  dayMaster={(analysisResult?.validation as { day_master?: string } | undefined)?.day_master}
                  deling={(analysisResult?.strength as Record<string, unknown> | undefined)?.deling as { status?: string; score?: number } | undefined}
                  dedi={(analysisResult?.strength as Record<string, unknown> | undefined)?.dedi as { score?: number; level?: string } | undefined}
                  deshi={(analysisResult?.strength as Record<string, unknown> | undefined)?.deshi as { score?: number; level?: string } | undefined}
                />
                <ShishenEnergyChart result={analysisResult} />
              </div>

              {/* 关系图谱 — 暂时用动态导入绕过 React 19 类型问题 */}
              <div suppressHydrationWarning>
                <RelationGraph result={analysisResult} />
              </div>

              {/* 大运流年 — 全宽 */}
              <DayunTimeline result={analysisResult} />

              {/* 双栏区：宫位 + 神煞 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <GongweiPanel result={analysisResult} />
                <ShenShaPanel result={analysisResult} />
              </div>

              {/* 格局判定依据 */}
              {pattern?.reason && (
                <div
                  className="rounded-2xl p-7"
                  style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                >
                  <h3 className="text-sm font-medium mb-3" style={{ color: "var(--text-muted)" }}>
                    格局判定依据
                  </h3>
                  <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {pattern.reason}
                  </p>
                  {pattern.confidence !== undefined && (
                    <div className="mt-3 flex items-center gap-3">
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>置信度</span>
                      <div className="flex-1 rounded-full" style={{ height: 6, background: "var(--bg-secondary)" }}>
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{
                            width: `${Math.min(pattern.confidence * 100, 100)}%`,
                            background: pattern.confidence >= 0.8 ? "var(--success)" : pattern.confidence >= 0.6 ? "var(--warning)" : "var(--danger)",
                          }}
                        />
                      </div>
                      <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>
                        {(pattern.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* 人生K线图 — 全宽 */}
              {analysisResult?.birth_year && (
                <LifeKlineChart
                  liunianScores={[]}
                  birthYear={Number(analysisResult.birth_year) || undefined}
                  qiyunAge={Number(analysisResult.qiyun_age) || 5}
                />
              )}

              {/* 流派分析 — 全宽 */}
              {isCompareMode && schoolAnalyses ? (
                <SchoolComparePanel schoolAnalyses={schoolAnalyses} />
              ) : (
                <SchoolPanel result={analysisResult} narration={narration as never} />
              )}

              {/* 命理问答 — 全宽 */}
              <ChatPanel analysisId={analysisId} />
            </div>
          ) : null}

          {status === "completed" &&
            !analysisResult &&
            result?.status === "completed" && (
              <div
                className="rounded-xl p-6"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                }}
              >
                <p style={{ color: "var(--text-secondary)" }}>
                  分析已完成，但无详细结果数据。
                </p>
              </div>
            )}
        </div>
      </main>
    </div>
  );
}
