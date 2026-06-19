"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import ReportCover from "./ReportCover";
import ReportChapter from "./ReportChapter";
import ReportNav from "./ReportNav";
import ReportCharts from "./ReportCharts";

const SECTION_META: Array<{ key: string; title: string }> = [
  { key: "overview", title: "命盘总览" },
  { key: "past_validation", title: "过往验证" },
  { key: "future_luck", title: "运势流年" },
  { key: "career_wealth", title: "事业财运" },
  { key: "marriage_love", title: "婚恋感情" },
  { key: "family", title: "家庭六亲" },
  { key: "health", title: "健康提示" },
  { key: "guidance", title: "趋吉避凶" },
];

interface ReportPreviewModalProps {
  open: boolean;
  onClose: () => void;
  onDownloadPdf?: () => void;
  report: {
    sections?: Record<string, string>;
    citations?: Record<string, string>;
    created_at?: string;
  };
  analysis: {
    result?: Record<string, unknown>;
    day_master?: string;
    pattern?: string;
    yongshen?: string;
    created_at?: string;
  };
  name?: string;
  downloading?: boolean;
}

export default function ReportPreviewModal({
  open,
  onClose,
  onDownloadPdf,
  report,
  analysis,
  name,
  downloading,
}: ReportPreviewModalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeChapter, setActiveChapter] = useState("overview");
  const [progress, setProgress] = useState(0);

  const result = analysis?.result as Record<string, unknown> | undefined;
  const validation = result?.validation as
    | { day_master?: string; bazi?: string; gender?: string; zodiac?: string }
    | undefined;
  const strength = result?.strength as
    | { wangshuai?: { verdict?: string } }
    | undefined;
  const pattern = result?.pattern as { pattern?: string } | undefined;
  const yongshen = result?.yongshen as { yongshen?: string } | undefined;

  // 监听滚动，更新进度和活跃章节
  const handleScroll = useCallback(() => {
    const container = scrollRef.current;
    if (!container) return;

    // 进度
    const { scrollTop, scrollHeight, clientHeight } = container;
    const pct = scrollHeight <= clientHeight ? 0 : (scrollTop / (scrollHeight - clientHeight)) * 100;
    setProgress(Math.min(100, Math.max(0, pct)));

    // 活跃章节
    for (let i = SECTION_META.length - 1; i >= 0; i--) {
      const el = document.getElementById(`chapter-${SECTION_META[i].key}`);
      if (el) {
        const rect = el.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        if (rect.top - containerRect.top <= 120) {
          setActiveChapter(SECTION_META[i].key);
          break;
        }
      }
    }
  }, []);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;
    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // ESC 关闭
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  // 锁定 body 滚动
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  return (
    <div
      role="dialog" aria-modal="true" aria-label="详批报告预览"
      className="fixed inset-0 flex flex-col"
      style={{ background: "var(--bg)", zIndex: "var(--z-overlay)" }}
    >
      {/* 顶部栏 */}
      <header
        className="flex items-center justify-between px-6 py-3 flex-shrink-0"
        style={{
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
        }}
      >
        <div className="flex items-center gap-4">
          <h2
            className="text-sm font-semibold"
            style={{
              color: "var(--ink)",
              fontFamily: "var(--font-display)",
            }}
          >
            详批报告
          </h2>
          {name && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                background: "var(--cinnabar-light)",
                color: "var(--cinnabar)",
              }}
            >
              {name}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {onDownloadPdf && (
            <button
              onClick={onDownloadPdf}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all duration-200 hover:opacity-90 disabled:opacity-50"
              style={{
                background: "var(--cinnabar)",
                color: "#fff",
              }}
            >
              {downloading ? (
                <>
                  <svg
                    className="animate-spin w-3.5 h-3.5"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                      opacity="0.25"
                    />
                    <path
                      d="M4 12a8 8 0 018-8"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                  生成中…
                </>
              ) : (
                <>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  下载 PDF
                </>
              )}
            </button>
          )}
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-lg transition-colors duration-200"
            style={{ color: "var(--text-3)" }}
            aria-label="关闭预览"
            title="关闭"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </header>

      {/* 进度条 */}
      <div
        className="h-0.5 flex-shrink-0"
        style={{ background: "var(--border-subtle)" }}
      >
        <div
          className="h-full transition-all duration-150"
          style={{
            width: `${progress}%`,
            background: "var(--cinnabar)",
          }}
        />
      </div>

      {/* 主内容区 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 侧边导航 - 桌面端 */}
        <aside
          className="hidden lg:block flex-shrink-0 overflow-y-auto py-6 px-4"
          style={{
            width: 180,
            borderRight: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <ReportNav items={SECTION_META} activeKey={activeChapter} />
        </aside>

        {/* 主滚动区 */}
        <main
          ref={scrollRef}
          className="flex-1 overflow-y-auto"
        >
          <div className="max-w-3xl mx-auto px-6 py-8 pb-24">
            {/* 封面 */}
            <div className="mb-8">
              <ReportCover
                name={name}
                dayMaster={validation?.day_master || analysis?.day_master}
                bazi={validation?.bazi}
                pattern={pattern?.pattern || analysis?.pattern}
                yongshen={yongshen?.yongshen || analysis?.yongshen}
                wangshuai={strength?.wangshuai?.verdict}
                gender={validation?.gender}
                zodiac={validation?.zodiac}
                createdAt={report?.created_at || analysis?.created_at}
              />
            </div>

            {/* 数据可视化 */}
            {result && (
              <div className="mb-8">
                <div
                  className="text-xs font-medium tracking-widest uppercase mb-4 px-1"
                  style={{ color: "var(--text-3)" }}
                >
                  数据概览
                </div>
                <ReportCharts result={result} />
              </div>
            )}

            {/* 章节列表 */}
            <div className="space-y-4">
              {SECTION_META.map((s, i) => {
                const content = report?.sections?.[s.key];
                if (!content) return null;
                return (
                  <ReportChapter
                    key={s.key}
                    id={`chapter-${s.key}`}
                    index={i}
                    title={s.title}
                    content={content}
                    citation={report?.citations?.[s.key]}
                    defaultOpen={i === 0}
                  />
                );
              })}
            </div>

            {/* 底部声明 */}
            <div
              className="mt-12 pt-6 text-center"
              style={{ borderTop: "1px solid var(--border-subtle)" }}
            >
              <p
                className="text-[11px] leading-relaxed"
                style={{ color: "var(--text-4)" }}
              >
                本报告基于确定性命理计算生成，仅供参考，不构成任何决策依据
                <br />
                报告内容由 AI 辅助生成，已通过数据验证层确保准确性
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
