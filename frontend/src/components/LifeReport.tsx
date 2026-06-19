"use client";

import { useRef } from "react";
import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import { gsap, useGSAP } from "@/lib/gsap";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";

interface LifeReportProps {
  content: string;
  /** 是否为 LLM 生成（true）还是确定性叙述 fallback（false） */
  isLlmGenerated?: boolean;
}

export default function LifeReport({ content, isLlmGenerated = true }: LifeReportProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  useGSAP(() => {
    if (!ref.current) return;
    if (prefersReducedMotion) {
      gsap.set(ref.current, { autoAlpha: 1 });
      return;
    }
    gsap.from(ref.current, {
      autoAlpha: 0,
      y: 24,
      duration: 0.6,
      ease: "power2.out",
      scrollTrigger: {
        trigger: ref.current,
        start: "top 90%",
        once: true,
      },
    });
  }, { scope: ref });

  return (
    <section
      ref={ref}
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-lg)",
        boxShadow: "var(--shadow-lg)",
        overflow: "hidden",
      }}
    >
      {/* 顶部装饰带 */}
      <div style={{
        height: 3,
        background: "linear-gradient(90deg, var(--cinnabar), var(--gold), var(--jade))",
        opacity: 0.6,
      }} />

      {/* 标题区 */}
      <div style={{
        padding: "28px 40px 20px",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div className="flex items-center gap-4">
          <div style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background: "linear-gradient(135deg, var(--cinnabar), #a04030)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 16px rgba(201,100,66,0.3)",
          }}>
            <span style={{
              fontSize: 22,
              color: "#fff",
              fontFamily: "var(--font-display)",
              fontWeight: 700,
            }}>命</span>
          </div>
          <div>
            <h2 style={{
              fontSize: 24,
              fontWeight: 700,
              fontFamily: "var(--font-display)",
              color: "var(--ink)",
              letterSpacing: "-0.02em",
              lineHeight: 1.2,
            }}>
              命书
            </h2>
            <p style={{
              fontSize: 13,
              color: "var(--text-3)",
              marginTop: 4,
              fontFamily: "var(--font-display)",
            }}>
              {isLlmGenerated
                ? "AI 深度解读 · 基于确定性计算"
                : "确定性分析 · 零幻觉"}
            </p>
          </div>
        </div>
      </div>

      {/* 内容区 */}
      <div
        className="life-report-body"
        style={{
          padding: "36px 40px 40px",
          color: "var(--text-2)",
          lineHeight: 1.80,
          fontSize: 16,
          fontFamily: "var(--font-display)",
        }}
      >
        <ReactMarkdown remarkPlugins={[RemarkGfm]}>{content}</ReactMarkdown>
      </div>

      {/* 底部标注 */}
      <div style={{
        padding: "12px 40px",
        borderTop: "1px solid var(--border-subtle)",
        background: "var(--surface-2)",
      }}>
        <p style={{
          fontSize: 11,
          color: "var(--text-4)",
          textAlign: "center",
        }}>
          {isLlmGenerated
            ? "本命书基于确定性命理计算生成，仅供参考，不构成任何决策依据"
            : "本分析基于确定性命理计算，零 LLM 依赖，每句话可追溯到计算数据"}
        </p>
      </div>

      <style jsx>{`
        .life-report-body :global(p) {
          margin-bottom: 1rem;
          text-indent: 2em;
        }
        .life-report-body :global(p:first-child) {
          text-indent: 0;
        }
        .life-report-body :global(strong) {
          color: var(--ink);
          font-weight: 700;
          display: block;
          text-indent: 0;
          margin-top: 2rem;
          margin-bottom: 0.6rem;
          font-size: 1.05em;
          letter-spacing: 0.02em;
        }
        .life-report-body :global(strong:first-child) {
          margin-top: 0;
        }
        .life-report-body :global(blockquote) {
          border-left: 3px solid var(--cinnabar);
          padding-left: 1rem;
          margin: 1rem 0;
          opacity: 0.9;
          font-style: italic;
          text-indent: 0;
        }
        .life-report-body :global(em) {
          color: var(--cinnabar);
          font-style: normal;
        }
      `}</style>
    </section>
  );
}
