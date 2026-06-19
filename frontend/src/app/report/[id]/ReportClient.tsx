"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeProvider";
import { SCHOOL_OPTIONS } from "@/lib/constants";
import ReportPreviewModal from "@/components/report/ReportPreviewModal";
import {
  API_BASE,
  getAnalysis,
  getReport,
  generateReport,
  type AnalysisResult,
  type ReportResponse,
} from "@/lib/api";

export default function ReportClient() {
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
  const [previewOpen, setPreviewOpen] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 从 birth_json 中提取姓名
  const birthJson = analysis?.result?.birth_json as Record<string, unknown> | undefined;
  const name = (birthJson?.name as string) || "";

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
      let failCount = 0;
      pollRef.current = setInterval(async () => {
        try {
          const updated = await getReport(analysisId);
          if (updated && updated.status !== "generating") {
            setReport(updated);
            if (pollRef.current) clearInterval(pollRef.current);
          }
          failCount = 0;
        } catch {
          failCount++;
          if (failCount >= 10) {
            if (pollRef.current) clearInterval(pollRef.current);
            setReport(prev => prev ? { ...prev, status: "failed" } : null);
          }
        }
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

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    setPdfError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v2/report/${analysisId}/pdf`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error?.message || data.detail || data.message || "PDF 生成失败");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `详批报告_${name || "命主"}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "PDF 下载失败");
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
        <div className="text-center">
          <div className="animate-pulse-glow w-4 h-4 rounded-full mx-auto mb-4" style={{ background: "var(--cinnabar)" }} />
          <p className="text-sm" style={{ color: "var(--text-3)" }}>加载中…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* 顶部导航 */}
      <div className="max-w-4xl mx-auto px-4 sm:px-8 py-6">
        <div className="flex items-center justify-between mb-8">
          <Link
            href={`/analyze/${analysisId}`}
            className="text-sm transition-colors duration-200 hover:text-[var(--cinnabar)]"
            style={{ color: "var(--text-3)" }}
          >
            ← 返回分析页
          </Link>
          <ThemeToggle />
        </div>

        {/* 标题区 */}
        <div
          className="rounded-2xl p-6 mb-8 animate-fade-in"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
          }}
        >
          <h1
            className="text-2xl font-bold mb-2"
            style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}
          >
            详批报告
          </h1>
          {name && (
            <p className="text-sm mb-4" style={{ color: "var(--text-3)" }}>
              命主：{name}
            </p>
          )}

          {/* 状态提示 */}
          {generating && (
            <div className="flex items-center gap-3 py-3 px-4 rounded-lg mt-4" style={{ background: "var(--surface-2)" }}>
              <div className="animate-pulse-glow w-3 h-3 rounded-full" style={{ background: "var(--cinnabar)" }} />
              <span className="text-sm" style={{ color: "var(--text-3)" }}>
                正在以「{SCHOOL_OPTIONS.find((s) => s.value === selectedSchool)?.label || "传统子平法"}」视角生成报告…
              </span>
            </div>
          )}

          {report?.status === "generating" && !generating && (
            <div className="flex items-center gap-3 py-3 px-4 rounded-lg mt-4" style={{ background: "var(--surface-2)" }}>
              <div className="animate-pulse-glow w-3 h-3 rounded-full" style={{ background: "var(--cinnabar)" }} />
              <span className="text-sm" style={{ color: "var(--text-3)" }}>
                报告生成中，自动刷新中…
              </span>
            </div>
          )}

          {report?.status === "failed" && (
            <div className="py-3 px-4 rounded-lg mt-4" style={{ background: "rgba(201,100,66,0.08)", border: "1px solid var(--danger)" }}>
              <p className="text-sm mb-3" style={{ color: "var(--danger)" }}>
                报告生成失败：{report.error || "未知错误"}
              </p>
              <button
                onClick={handleGenerate}
                className="px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200"
                style={{ background: "var(--danger)", color: "#fff" }}
              >
                重试
              </button>
            </div>
          )}

          {error && !report && (
            <div className="py-3 px-4 rounded-lg mt-4" style={{ background: "rgba(201,100,66,0.08)", border: "1px solid var(--danger)" }}>
              <p className="text-sm mb-3" style={{ color: "var(--danger)" }}>{error}</p>
              <button
                onClick={handleGenerate}
                className="px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200"
                style={{ background: "var(--danger)", color: "#fff" }}
              >
                重试
              </button>
            </div>
          )}
        </div>

        {/* 操作区 */}
        {!report && !generating && (
          <div className="text-center py-12">
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
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    color: "var(--ink)",
                  }}
                >
                  <span style={{ color: "var(--text-3)" }}>分析视角：</span>
                  <span className="font-semibold">
                    {SCHOOL_OPTIONS.find((s) => s.value === selectedSchool)?.label || "传统子平法"}
                  </span>
                  <svg
                    width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
                    style={{ transform: schoolDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                {schoolDropdownOpen && (
                  <div
                    className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 rounded-xl overflow-hidden"
                    style={{ zIndex: "var(--z-dropdown)", background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "0 8px 32px rgba(0,0,0,0.15)" }}
                  >
                    {SCHOOL_OPTIONS.map((s) => (
                      <button
                        key={s.value}
                        onClick={() => { setSelectedSchool(s.value); setSchoolDropdownOpen(false); }}
                        className="w-full px-5 py-3 text-left transition-colors hover:bg-[var(--surface-2)]"
                        style={{
                          fontSize: 13,
                          background: selectedSchool === s.value ? "var(--cinnabar-light)" : "transparent",
                        }}
                      >
                        <div className="font-medium" style={{ color: selectedSchool === s.value ? "var(--cinnabar)" : "var(--ink)" }}>
                          {s.label}
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-3)" }}>{s.desc}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              className="px-8 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95"
              style={{ background: "var(--cinnabar)", color: "#fff" }}
            >
              生成详批报告
            </button>
          </div>
        )}

        {/* 报告已生成 - 显示预览入口 */}
        {report?.status === "completed" && report.sections && (
          <div className="space-y-4">
            {/* 预览按钮 */}
            <button
              onClick={() => setPreviewOpen(true)}
              className="w-full py-4 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-3"
              style={{
                background: "var(--ink)",
                color: "var(--bg)",
                boxShadow: "0 6px 24px rgba(0,0,0,0.2)",
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
              查看详批报告
            </button>

            {/* PDF下载按钮 */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="w-full py-4 rounded-xl text-sm font-semibold transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-3 disabled:opacity-50"
              style={{
                background: "var(--surface)",
                color: "var(--ink)",
                border: "1px solid var(--border)",
              }}
            >
              {downloadingPdf ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.25" />
                    <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                  正在生成 PDF…
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  下载 PDF 报告
                </>
              )}
            </button>

            {/* PDF 错误提示 */}
            {pdfError && (
              <div className="py-3 px-4 rounded-lg" style={{ background: "var(--cinnabar-light)", border: "1px solid var(--danger)" }}>
                <p className="text-sm" style={{ color: "var(--danger)" }}>{pdfError}</p>
              </div>
            )}

            {/* 返回按钮 */}
            <button
              onClick={() => router.push(`/analyze/${analysisId}`)}
              className="w-full py-3 rounded-xl text-xs font-medium transition-colors duration-200"
              style={{ color: "var(--text-3)" }}
            >
              返回分析页
            </button>
          </div>
        )}
      </div>

      {/* 预览弹窗 */}
      {report?.status === "completed" && analysis && (
        <ReportPreviewModal
          open={previewOpen}
          onClose={() => setPreviewOpen(false)}
          onDownloadPdf={handleDownloadPdf}
          report={report}
          analysis={analysis}
          name={name}
          downloading={downloadingPdf}
        />
      )}
    </div>
  );
}
