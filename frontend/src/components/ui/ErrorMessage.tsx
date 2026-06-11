"use client";

import type { ReactNode } from "react";

/* ── 类型 ── */
export interface ErrorMessageProps {
  /** 标题文字，默认 "渲染出错" */
  title?: string;
  /** 错误描述文字 */
  message?: string;
  /** 重试回调；不传则不显示重试按钮 */
  onRetry?: () => void;
  /** 返回首页按钮；传入导航回调时显示 */
  onGoHome?: () => void;
  /** 额外的操作按钮 */
  extra?: ReactNode;
  /** 容器额外 class */
  className?: string;
}

/* ── ErrorMessage ── */
export default function ErrorMessage({
  title = "渲染出错",
  message,
  onRetry,
  onGoHome,
  extra,
  className,
}: ErrorMessageProps) {
  return (
    <section
      className={`card p-8 text-center${className ? ` ${className}` : ""}`}
      style={{ margin: "2rem auto", maxWidth: 600 }}
    >
      <h3 style={{ color: "var(--danger)", marginBottom: 8, fontSize: 18, fontWeight: 700 }}>
        {title}
      </h3>
      {message && (
        <p style={{ color: "var(--text-2)", fontSize: 14, marginBottom: 16 }}>{message}</p>
      )}
      <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              padding: "10px 24px",
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "var(--surface)",
              cursor: "pointer",
              color: "var(--ink)",
              fontSize: 14,
            }}
          >
            重试
          </button>
        )}
        {onGoHome && (
          <button
            onClick={onGoHome}
            style={{
              padding: "10px 24px",
              borderRadius: 10,
              border: "none",
              background: "var(--scholar-blue)",
              cursor: "pointer",
              color: "#fff",
              fontSize: 14,
            }}
          >
            返回首页
          </button>
        )}
        {extra}
      </div>
    </section>
  );
}
