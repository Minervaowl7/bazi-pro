"use client";

import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";

export default function LlmOverview({ content }: { content: string }) {
  if (!content) return null;
  return (
    <section className="card relative overflow-hidden">
      {/* 朱砂竖线 */}
      <div className="cinnabar-bar" />
      <div className="pl-5 pr-8 pt-5 pb-4">
        <h3 className="font-bold text-xl" style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}>命书</h3>
        <p className="text-xs mt-0.5 tracking-wide" style={{ color: "var(--text-3)" }}>AI 解读 · 基于确定性计算</p>
      </div>
      {/* 金色分隔线 */}
      <div className="gold-divider ml-5 mb-5 max-w-[200px]" />
      <div className="llm-overview-body px-5 pb-8 pr-8" style={{ color: "var(--text-2)", lineHeight: 1.85, fontSize: 15, fontFamily: "var(--font-display)" }}>
        <ReactMarkdown remarkPlugins={[RemarkGfm]}>{content}</ReactMarkdown>
      </div>
      <style jsx>{`
        .llm-overview-body :global(h2) { color: var(--cinnabar); font-size: 1.2rem; font-weight: 700; font-family: var(--font-display); margin-top: 1.8rem; margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border-subtle); }
        .llm-overview-body :global(h2:first-child) { margin-top: 0; }
        .llm-overview-body :global(h3) { color: var(--ink); font-size: 1.05rem; font-weight: 600; font-family: var(--font-display); margin-top: 1.4rem; margin-bottom: 0.6rem; }
        .llm-overview-body :global(p) { margin-bottom: 0.8rem; text-indent: 2em; }
        .llm-overview-body :global(p:first-child) { text-indent: 0; }
        .llm-overview-body :global(strong) { color: var(--ink); font-weight: 700; }
        .llm-overview-body :global(ul), .llm-overview-body :global(ol) { padding-left: 1.3rem; margin: 0.6rem 0; }
        .llm-overview-body :global(li) { margin: 0.3rem 0; line-height: 1.75; }
        .llm-overview-body :global(blockquote) { border-left: 3px solid var(--cinnabar); padding-left: 1rem; opacity: 0.9; margin: 0.8rem 0; font-style: italic; }
        .llm-overview-body :global(code) { background: var(--surface-2); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
      `}</style>
    </section>
  );
}
