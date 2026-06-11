"use client";

import { Component, type ReactNode } from "react";

/* ── 类型 ── */
export interface ErrorBoundaryProps {
  children: ReactNode;
  /** 自定义 fallback UI；不传时使用内置 ErrorMessage */
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

/* ── ErrorBoundary 类组件 ── */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <section
            className="card p-8 text-center"
            style={{ margin: "2rem auto", maxWidth: 600 }}
          >
            <h3 style={{ color: "var(--danger)", marginBottom: 8 }}>渲染出错</h3>
            <p style={{ color: "var(--text-2)", fontSize: 14 }}>
              {this.state.error?.message || "未知错误"}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              style={{
                marginTop: 16,
                padding: "8px 20px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--surface)",
                cursor: "pointer",
                color: "var(--ink)",
              }}
            >
              重试
            </button>
          </section>
        )
      );
    }
    return this.props.children;
  }
}

/* ── Safe 便捷包装 ── */
export function Safe({ children, fallback }: ErrorBoundaryProps) {
  return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>;
}
