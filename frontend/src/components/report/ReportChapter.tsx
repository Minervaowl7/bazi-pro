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
  const num = CHAPTER_NUMBERS[index] || String(index + 1);

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
        {/* 章节编号 - 印章风格 */}
        <div
          className="flex-shrink-0 flex items-center justify-center"
          style={{
            width: 36,
            height: 36,
            borderRadius: 4,
            border: "2px solid var(--cinnabar)",
            color: "var(--cinnabar)",
            fontFamily: "var(--font-display)",
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: "0.05em",
          }}
        >
          {num}
        </div>

        {/* 章节标题 */}
        <span
          className="flex-1 text-base font-semibold"
          style={{
            color: "var(--ink)",
            fontFamily: "var(--font-display)",
            letterSpacing: "0.02em",
          }}
        >
          {title}
        </span>

        {/* 展开/收起图标 */}
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
            color: "var(--text-3)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
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

              {/* 古籍引用 */}
              {citation && citation.trim().length > 0 && (
                <div
                  className="mt-6 px-4 py-3 rounded-lg"
                  style={{
                    background: "rgba(180,154,92,0.06)",
                    borderLeft: "3px solid var(--gold)",
                  }}
                >
                  <div
                    className="text-[11px] font-medium mb-1.5 tracking-wide"
                    style={{ color: "var(--gold)" }}
                  >
                    典籍引证
                  </div>
                  <div
                    className="text-xs leading-relaxed"
                    style={{ color: "var(--text-3)" }}
                  >
                    {citation}
                  </div>
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
