"use client";

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        {/* 装饰卦象符号 */}
        <div className="mb-6 flex justify-center">
          <svg
            width="64" height="64" viewBox="0 0 64 64" fill="none"
            aria-hidden="true"
            style={{ opacity: 0.2 }}
          >
            {/* 八卦简化纹 — 三爻 */}
            <rect x="18" y="12" width="28" height="3" rx="1.5" fill="var(--gold)" />
            <rect x="18" y="18" width="12" height="3" rx="1.5" fill="var(--gold)" />
            <rect x="34" y="18" width="12" height="3" rx="1.5" fill="var(--gold)" />
            <rect x="18" y="24" width="28" height="3" rx="1.5" fill="var(--gold)" />
            {/* 外圈 */}
            <circle cx="32" cy="32" r="30" stroke="var(--gold)" strokeWidth="0.5" opacity="0.5" />
            <circle cx="32" cy="32" r="26" stroke="var(--gold)" strokeWidth="0.3" opacity="0.3" />
          </svg>
        </div>

        {/* 金色分隔线 */}
        <div
          className="mx-auto mb-6"
          style={{
            width: 80,
            height: 1,
            background: "linear-gradient(90deg, transparent, var(--gold), transparent)",
          }}
        />

        {/* 404 数字 */}
        <div
          className="text-7xl font-bold mb-3 tracking-tight"
          style={{
            color: "var(--text-4)",
            fontFamily: "var(--font-display)",
            letterSpacing: "-0.04em",
          }}
        >
          404
        </div>

        <h1
          className="text-lg font-bold mb-2"
          style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}
        >
          此路不通
        </h1>

        <p className="text-sm mb-8 leading-relaxed" style={{ color: "var(--text-3)" }}>
          您所寻之页已移往他处，或从未存在。
          <br />
          如占卜不得其方，不妨另择吉位。
        </p>

        {/* 金色分隔线 */}
        <div
          className="mx-auto mb-8"
          style={{
            width: 48,
            height: 1,
            background: "linear-gradient(90deg, transparent, var(--gold), transparent)",
          }}
        />

        {/* 操作按钮 */}
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all active:scale-[0.97]"
            style={{
              background: "var(--cinnabar)",
              color: "#fff",
              boxShadow: "0 2px 8px rgba(201,100,66,0.25)",
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            返回首页
          </Link>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium border transition-all active:scale-[0.97]"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-2)",
              background: "var(--surface)",
              cursor: "pointer",
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            返回上页
          </button>
        </div>
      </div>
    </div>
  );
}
