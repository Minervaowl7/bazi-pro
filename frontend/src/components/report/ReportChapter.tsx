"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const CHAPTER_NUMBERS = ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌"];

interface ReportChapterProps {
  index: number;
  title: string;
  content: string;
  citation?: string;
  defaultOpen?: boolean;
  id?: string;
}

export default function ReportChapter({
  index,
  title,
  content,
  citation,
  defaultOpen = false,
  id,
}: ReportChapterProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [showCitation, setShowCitation] = useState(false);
  const num = CHAPTER_NUMBERS[index] || String(index + 1);
  const hasCitation = citation && citation.trim().length > 0;

  return (
    <section
      id={id}
      className="group"
      style={{
        background: "var(--surface)",
        borderRadius: "var(--r)",
        border: "1px solid var(--border)",
        overflow: "hidden",
        transition: "border-color 0.2s",
      }}
    >
      {/* 章节头部 */}
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center gap-4 px-6 py-5 text-left transition-colors duration-200"
        style={{
          background: open ? "var(--surface-2)" : "transparent",
        }}
      >
        {/* 章节编号 - 金边印章 */}
        <div
          className="flex-shrink-0 flex items-center justify-center"
          style={{
            width: 38,
            height: 38,
            borderRadius: 6,
            border: "1.5px solid var(--gold)",
            color: "var(--cinnabar)",
            fontFamily: "var(--font-display)",
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: "0.05em",
            background: open ? "rgba(180,154,92,0.06)" : "transparent",
            transition: "background 0.2s",
          }}
        >
          {num}
        </div>

        {/* 章节标题 */}
        <span
          className="flex-1 font-semibold"
          style={{
            color: "var(--ink)",
            fontFamily: "var(--font-display)",
            letterSpacing: "0.02em",
            fontSize: 16,
          }}
        >
          {title}
        </span>

        {/* 引证标记 + 展开图标 */}
        <div className="flex items-center gap-2">
          {hasCitation && (
            <span
              className="text-[10px] px-1.5 py-0.5 rounded"
              style={{
                background: "rgba(180,154,92,0.08)",
                color: "var(--gold)",
                letterSpacing: "0.04em",
              }}
            >
              引
            </span>
          )}
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              color: "var(--text-4)",
              transform: open ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 0.2s",
            }}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {/* 章节内容 */}
      {open && (
        <div
          className="animate-fade-in"
          style={{
            borderTop: "1px solid var(--border)",
          }}
        >
          {/* 朱砂竖线装饰 */}
          <div className="flex">
            <div
              className="flex-shrink-0"
              style={{
                width: 3,
                background: "linear-gradient(180deg, var(--cinnabar), transparent)",
                opacity: 0.4,
              }}
            />
            <div className="flex-1 px-6 py-6">
              {/* 正文 */}
              <div
                className="report-chapter-body"
                style={{
                  color: "var(--text-2)",
                  lineHeight: 1.85,
                  fontSize: 15,
                  fontFamily: "var(--font-display)",
                }}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {content}
                </ReactMarkdown>
              </div>

              {/* 典籍引证 — 折叠式，节省空间 */}
              {hasCitation && (
                <div className="mt-4">
                  <button
                    onClick={() => setShowCitation(!showCitation)}
                    className="flex items-center gap-1.5 text-[12px] transition-colors duration-150"
                    style={{
                      color: "var(--gold)",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: "4px 0",
                      fontFamily: "var(--font-display)",
                    }}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    </svg>
                    参考典籍
                    <svg
                      width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                      style={{
                        transform: showCitation ? "rotate(90deg)" : "rotate(0deg)",
                        transition: "transform 0.15s",
                      }}
                    >
                      <polyline points="9 6 15 12 9 18" />
                    </svg>
                  </button>
                  {showCitation && (
                    <div
                      className="mt-2 px-3 py-2.5 rounded text-[12px] leading-relaxed animate-fade-in"
                      style={{
                        background: "rgba(180,154,92,0.04)",
                        color: "var(--text-3)",
                        borderLeft: "2px solid rgba(180,154,92,0.2)",
                      }}
                    >
                      {citation}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .report-chapter-body :global(p) {
          margin-bottom: 0.9rem;
          text-indent: 2em;
        }
        .report-chapter-body :global(p:first-child) {
          text-indent: 0;
        }
        .report-chapter-body :global(strong) {
          color: var(--ink);
          font-weight: 700;
          display: block;
          text-indent: 0;
          margin-top: 1.6rem;
          margin-bottom: 0.5rem;
          font-size: 1.02em;
        }
        .report-chapter-body :global(strong:first-child) {
          margin-top: 0;
        }
        .report-chapter-body :global(blockquote) {
          border-left: 3px solid var(--cinnabar);
          padding-left: 1rem;
          margin: 1rem 0;
          opacity: 0.9;
          font-style: italic;
          text-indent: 0;
        }
        .report-chapter-body :global(em) {
          color: var(--cinnabar);
          font-style: normal;
        }
        .report-chapter-body :global(ul),
        .report-chapter-body :global(ol) {
          padding-left: 1.5rem;
          margin: 0.6rem 0;
        }
        .report-chapter-body :global(li) {
          margin: 0.3rem 0;
        }
      `}</style>
    </section>
  );
}
