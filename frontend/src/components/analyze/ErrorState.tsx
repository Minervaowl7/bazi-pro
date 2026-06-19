"use client";

import { useState } from "react";

import type { BirthInput } from "@/lib/api";

interface ErrorStateProps {
  error: string;
  birthInput: BirthInput | null;
  selectedSchool: string;
  onReanalyze: (input: BirthInput, school: string) => void;
  onRetryFetch: () => void;
}

export default function ErrorState({ error, birthInput, selectedSchool, onReanalyze, onRetryFetch }: ErrorStateProps) {
  const [showDetails, setShowDetails] = useState(false);
  const errorMsg = error || "未知错误";
  const isLlmError = errorMsg.includes("LLM") && (errorMsg.includes("未配置") || errorMsg.includes("503") || errorMsg.includes("not configured") || errorMsg.includes("不可用"));
  const isNetworkError = errorMsg.includes("fetch") || errorMsg.includes("network") || errorMsg.includes("网络") || errorMsg.includes("Failed to fetch") || errorMsg.includes("ECONNREFUSED");

  const handleRetry = () => {
    setShowDetails(false);
    if (birthInput) { onReanalyze(birthInput, selectedSchool); }
    else { onRetryFetch(); }
  };

  return (
    <section className="card mb-6 overflow-hidden animate-fade-in" style={{ border: "1px solid var(--danger)" }} role="alert">
      <div style={{ height: 3, background: "linear-gradient(90deg, var(--danger), var(--warning))" }} />
      <div className="p-6">
        <div className="flex items-start gap-4">
          <div className="shrink-0 flex items-center justify-center rounded-full" style={{ width: 40, height: 40, background: "rgba(201,100,66,0.10)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-base mb-1" style={{ color: "var(--danger)", fontFamily: "var(--font-display)" }}>
              {isNetworkError ? "网络连接失败" : isLlmError ? "智能解读暂不可用" : "分析失败"}
            </h3>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-2)" }}>
              {isNetworkError ? "无法连接到分析服务，请检查网络连接后重试。" : isLlmError ? "LLM 智能解读服务未配置或暂时不可用，但核心命理计算（确定性推导）已完成，您仍可查看四柱命盘、旺衰、格局、用神等确定性分析结果。" : errorMsg}
            </p>
            {isLlmError && (
              <div className="mt-3 flex items-start gap-2.5 px-3 py-2.5 rounded-md text-xs leading-relaxed"
                style={{ background: "rgba(46,92,138,0.06)", border: "1px solid rgba(46,92,138,0.12)", color: "var(--text-2)" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--wx-water)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                <span>核心计算结果（十神、旺衰、格局、用神、调候、刑冲合害等）均为确定性推导，不依赖 LLM。如需智能解读，请在服务端配置 <code className="text-[11px] px-1 py-0.5 rounded" style={{ background: "var(--surface-2)", color: "var(--ink)" }}>LLM_API_KEY</code> 环境变量。</span>
              </div>
            )}
            <div className="flex items-center gap-2.5 mt-4">
              <button onClick={handleRetry} className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-[0.97]"
                style={{ background: "var(--cinnabar)", color: "#fff", cursor: "pointer", boxShadow: "0 1px 4px rgba(201,100,66,0.2)" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                重新分析
              </button>
              <button onClick={() => setShowDetails(!showDetails)} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors"
                style={{ color: "var(--text-3)", background: "var(--surface-2)", cursor: "pointer" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  style={{ transform: showDetails ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                  <polyline points="6 9 12 15 18 9" />
                </svg>
                {showDetails ? "隐藏详情" : "查看详情"}
              </button>
            </div>
            {showDetails && (
              <div className="mt-3 px-3 py-2.5 rounded-md text-xs font-mono leading-relaxed overflow-x-auto animate-fade-in"
                style={{ background: "var(--surface-2)", border: "1px solid var(--border-subtle)", color: "var(--text-3)", maxHeight: 160, overflowY: "auto", wordBreak: "break-all" }}>
                {errorMsg}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
