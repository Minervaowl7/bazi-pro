"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ThemeToggle } from "@/components/ThemeProvider";
import { SCHOOL_OPTIONS } from "@/lib/constants";
import {
  getAnalysis,
  getReport,
  generateReport,
  type AnalysisResult,
  type ReportResponse,
} from "@/lib/api";

// 8章详批报告结构
const SECTION_META: Array<{
  key: string;
  title: string;
  icon: string;
}> = [
  { key: "overview", title: "命盘总览", icon: "☯" },
  { key: "past_validation", title: "过往验证", icon: "📜" },
  { key: "future_luck", title: "运势流年", icon: "📅" },
  { key: "career_wealth", title: "事业财运", icon: "💼" },
  { key: "marriage_love", title: "婚恋感情", icon: "❤" },
  { key: "family", title: "家庭六亲", icon: "👨‍👩‍👧‍👦" },
  { key: "health", title: "健康提示", icon: "⚕" },
  { key: "guidance", title: "趋吉避凶", icon: "🍀" },
];

function SectionCard({
  title,
  icon,
  content,
  citation,
  defaultOpen = false,
}: {
  title: string;
  icon: string;
  content: string;
  citation?: string;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div
      className="rounded-2xl overflow-hidden transition-all duration-300"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-5 text-left transition-colors duration-200"
        style={{ background: open ? "var(--surface-2)" : "transparent" }}
      >
        <span className="flex items-center gap-3">
          <span className="text-lg">{icon}</span>
          <span className="text-base font-semibold" style={{ color: "var(--cinnabar)" }}>
            {title}
          </span>
        </span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-5 h-5 transition-transform duration-300"
          style={{
            color: "var(--text-3)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && (
        <div
          className="px-6 pb-6 pt-2 animate-fade-in"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <div
            className="prose-sm"
            style={{ color: "var(--text-2)", lineHeight: 1.85 }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
          {citation && citation.trim().length > 0 && (
            <div
              className="mt-4 px-3 py-2.5 rounded-md text-xs leading-relaxed"
              style={{
                background: "var(--surface-2)",
                color: "var(--text-3)",
                border: "1px solid var(--border)",
              }}
            >
              {citation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SkeletonSection() {
  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
      }}
    >
      <div className="px-6 py-5 flex items-center gap-3">
        <div
          className="h-5 w-5 rounded-md animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
        <div
          className="h-5 rounded-md w-32 animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
      </div>
      <div className="px-6 pb-6 space-y-3">
        <div
          className="h-3 rounded-md w-full animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
        <div
          className="h-3 rounded-md w-5/6 animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
        <div
          className="h-3 rounded-md w-4/6 animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
        <div
          className="h-3 rounded-md w-3/4 animate-shimmer"
          style={{ background: "var(--surface-2)" }}
        />
      </div>
    </div>
  );
}

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params.id as string;

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSchool, setSelectedSchool] = useState("ziping");
  const [schoolDropdownOpen, setSchoolDropdownOpen] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    let analysisData: AnalysisResult | null = null;
    let reportData: ReportResponse | null = null;
    try {
      analysisData = await getAnalysis(analysisId);
    } catch {}
    try {
      reportData = await getReport(analysisId);
    } catch {}
    return { analysisData, reportData };
  }, [analysisId]);

  useEffect(() => {
    let cancelled = false;
    fetchData().then(({ analysisData, reportData }) => {
      if (cancelled) return;
      if (!analysisData) {
        setError("加载分析数据失败");
      } else {
        setAnalysis(analysisData);
        setReport(reportData);
      }
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [fetchData]);

  useEffect(() => {
    if (report?.status === "generating") {
      pollRef.current = setInterval(async () => {
        try {
          const updated = await getReport(analysisId);
          if (updated && updated.status !== "generating") {
            setReport(updated);
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch {}
      }, 3000);
      return () => {
        if (pollRef.current) clearInterval(pollRef.current);
      };
    }
  }, [report?.status, analysisId]);

  // 点击外部关闭下拉框
  useEffect(() => {
    if (!schoolDropdownOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setSchoolDropdownOpen(false);
      }
    };
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [schoolDropdownOpen]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const resp = await generateReport(analysisId, selectedSchool);
      setReport(resp);
    } catch (e) {
      setError(e instanceof Error ? e.message : "生成报告失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyText = async () => {
    if (!report?.sections) return;
    const text = SECTION_META.map((s) => {
      const content = report.sections?.[s.key] || "";
      return content ? `## ${s.title}\n\n${content}` : "";
    })
      .filter(Boolean)
      .join("\n\n---\n\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  };

  const handleExportPDF = () => {
    window.print();
  };

  const result = analysis?.result as Record<string, unknown> | undefined;
  const validation = result?.validation as { day_master?: string; bazi?: string; gender?: string } | undefined;
  const pattern = result?.pattern as { pattern?: string } | undefined;
  const yongshen = result?.yongshen as { yongshen?: string } | undefined;
  const strength = result?.strength as { wangshuai?: { verdict?: string } } | undefined;

  if (loading) {
    return (
      <div className="min-h-screen" style={{ background: "var(--bg)" }}>
        <div className="max-w-4xl mx-auto px-8 py-8">
          <div className="space-y-6">
            <div
              className="rounded-2xl p-8 animate-shimmer"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border)", height: 160 }}
            />
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonSection key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      <div className="max-w-4xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <Link
            href={`/analyze/${analysisId}`}
            className="text-sm transition-colors duration-200 hover:text-[var(--cinnabar)]"
            style={{ color: "var(--text-3)" }}
          >
            ← 返回分析页
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
          </div>
        </div>

        <div
          className="rounded-2xl p-6 mb-8 animate-fade-in"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <h1
            className="text-2xl font-bold mb-5"
            style={{ color: "var(--cinnabar)" }}
          >
            详批报告
          </h1>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div
              className="rounded-xl p-4 text-center"
              style={{ background: "var(--surface-2)" }}
            >
              <div className="text-xs mb-1.5" style={{ color: "var(--text-3)" }}>
                八字
              </div>
              <div className="text-sm font-semibold" style={{ color: "var(--ink)" }}>
                {validation?.bazi || "—"}
              </div>
            </div>
            <div
              className="rounded-xl p-4 text-center"
              style={{ background: "var(--surface-2)" }}
            >
              <div className="text-xs mb-1.5" style={{ color: "var(--text-3)" }}>
                格局
              </div>
              <div className="text-sm font-semibold" style={{ color: "var(--cinnabar)" }}>
                {pattern?.pattern || "—"}
              </div>
            </div>
            <div
              className="rounded-xl p-4 text-center"
              style={{ background: "var(--surface-2)" }}
            >
              <div className="text-xs mb-1.5" style={{ color: "var(--text-3)" }}>
                用神
              </div>
              <div className="text-sm font-semibold" style={{ color: "var(--cinnabar)" }}>
                {yongshen?.yongshen || "—"}
              </div>
            </div>
            <div
              className="rounded-xl p-4 text-center"
              style={{ background: "var(--surface-2)" }}
            >
              <div className="text-xs mb-1.5" style={{ color: "var(--text-3)" }}>
                旺衰
              </div>
              <div className="text-sm font-semibold" style={{ color: "var(--cinnabar)" }}>
                {strength?.wangshuai?.verdict || "—"}
              </div>
            </div>
          </div>
        </div>

        {!report && !generating && (
          <div className="text-center py-16">
            <p className="text-base mb-6" style={{ color: "var(--text-2)" }}>
              尚未生成详批报告
            </p>

            {/* 派别选择 */}
            <div className="mb-6 flex justify-center" ref={dropdownRef}>
              <div className="relative inline-block text-left">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSchoolDropdownOpen(!schoolDropdownOpen);
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    color: "var(--ink)",
                  }}
                >
                  <span style={{ color: "var(--text-3)" }}>分析视角：</span>
                  <span className="font-semibold">
                    {SCHOOL_OPTIONS.find((s) => s.value === selectedSchool)?.label || "传统子平法"}
                  </span>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{
                      transform: schoolDropdownOpen ? "rotate(180deg)" : "none",
                      transition: "transform 0.2s",
                    }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                {schoolDropdownOpen && (
                  <div
                    className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 z-50 rounded-xl overflow-hidden"
                    style={{
                      background: "var(--bg-card)",
                      border: "1px solid var(--border)",
                      boxShadow: "0 8px 32px rgba(0,0,0,0.15)",
                    }}
                  >
                    {SCHOOL_OPTIONS.map((s) => (
                      <button
                        key={s.value}
                        onClick={() => {
                          setSelectedSchool(s.value);
                          setSchoolDropdownOpen(false);
                        }}
                        className="w-full px-5 py-3 text-left transition-colors hover:bg-[var(--surface-2)]"
                        style={{
                          fontSize: 13,
                          background:
                            selectedSchool === s.value
                              ? "var(--accent-dim, rgba(45,125,91,0.08))"
                              : "transparent",
                        }}
                      >
                        <div
                          className="font-medium"
                          style={{
                            color:
                              selectedSchool === s.value
                                ? "var(--cinnabar)"
                                : "var(--ink)",
                          }}
                        >
                          {s.label}
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-3)" }}>
                          {s.desc}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              className="px-8 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--cinnabar)",
                color: "#0c0c14",
              }}
            >
              生成详批报告
            </button>
          </div>
        )}

        {generating && (
          <div className="space-y-6">
            <div className="flex items-center justify-center gap-3 py-4">
              <div className="animate-pulse-glow w-3 h-3 rounded-full" style={{ background: "var(--cinnabar)" }} />
              <span className="text-sm" style={{ color: "var(--text-3)" }}>
                正在以「{SCHOOL_OPTIONS.find((s) => s.value === selectedSchool)?.label || "传统子平法"}」视角生成报告，请稍候...
              </span>
            </div>
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonSection key={i} />
            ))}
          </div>
        )}

        {report?.status === "generating" && !generating && (
          <div className="space-y-6">
            <div className="flex items-center justify-center gap-3 py-4">
              <div className="animate-pulse-glow w-3 h-3 rounded-full" style={{ background: "var(--cinnabar)" }} />
              <span className="text-sm" style={{ color: "var(--text-3)" }}>
                报告生成中，自动刷新中...
              </span>
            </div>
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonSection key={i} />
            ))}
          </div>
        )}

        {report?.status === "failed" && (
          <div
            className="rounded-xl p-6 mb-8 text-center"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--danger)",
            }}
          >
            <p className="text-sm mb-4" style={{ color: "var(--danger)" }}>
              报告生成失败：{report.error || "未知错误"}
            </p>
            <button
              onClick={handleGenerate}
              className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--danger)",
                color: "#fff",
              }}
            >
              重试
            </button>
          </div>
        )}

        {error && !report && (
          <div
            className="rounded-xl p-6 mb-8 text-center"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--danger)",
            }}
          >
            <p className="text-sm mb-4" style={{ color: "var(--danger)" }}>{error}</p>
            <button
              onClick={handleGenerate}
              className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--danger)",
                color: "#fff",
              }}
            >
              重试
            </button>
          </div>
        )}

        {report?.status === "completed" && report.sections && (
          <div className="space-y-4">
            {SECTION_META.map((s, i) => {
              const content = report.sections?.[s.key];
              if (!content) return null;
              return (
                <SectionCard
                  key={s.key}
                  title={s.title}
                  icon={s.icon}
                  content={content}
                  citation={report.citations?.[s.key]}
                  defaultOpen={i === 0}
                />
              );
            })}
          </div>
        )}

        {report?.status === "completed" && (
          <div
            className="fixed bottom-0 left-0 right-0 py-4 px-8 flex items-center justify-center gap-4 no-print"
            style={{
              background: "linear-gradient(to top, var(--bg) 60%, transparent)",
              zIndex: 50,
            }}
          >
            <button
              onClick={handleExportPDF}
              className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--cinnabar)",
                color: "#0c0c14",
              }}
            >
              导出PDF
            </button>
            <button
              onClick={handleCopyText}
              className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--bg-card)",
                color: "var(--ink)",
                border: "1px solid var(--border)",
              }}
            >
              复制文本
            </button>
            <button
              onClick={() => router.push(`/analyze/${analysisId}`)}
              className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: "var(--surface-2)",
                color: "var(--text-2)",
                border: "1px solid var(--border)",
              }}
            >
              返回分析页
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
