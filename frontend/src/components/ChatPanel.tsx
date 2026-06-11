"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import {
  getChatHistory,
  sendChatMessageStream,
  type ChatMessage,
  type ChatStreamEvent,
} from "@/lib/api";

/* ─── 古籍引用数据结构 ─── */
interface Citation {
  source: string;
  topic: string;
  score: number;
  content: string;
  isCounter?: boolean;
}

/**
 * 将后端格式化的 citations 字符串解析为结构化引用数组。
 * 格式示例：
 *   【古籍依据】
 *   [1] 《子平真诠》@格局用神 (id=xxx, score=0.8765)
 *       条文内容…
 *   【反证/对立观点】
 *   - 《滴天髓》@xxx (score=0.6543)
 *     反证内容…
 */
function parseCitations(raw: string): Citation[] {
  if (!raw || raw.trim().length === 0) return [];

  const results: Citation[] = [];

  // 按【反证/对立观点】分割主引用和反证
  const counterSplit = raw.split(/【反证[\/／]?对立观点】/);
  const mainSection = counterSplit[0] ?? "";
  const counterSection = counterSplit[1] ?? "";

  // 解析主引用：[n] 《source》@topic (id=xxx, score=0.xxxx)\n    content
  const mainRe = /\[\d+]\s*《([^》]+)》@(\S+)\s*\([^)]*score=([\d.]+)[^)]*\)\s*\n([\s\S]*?)(?=\[\d+]|$)/g;
  let m: RegExpExecArray | null;
  while ((m = mainRe.exec(mainSection)) !== null) {
    results.push({
      source: m[1],
      topic: m[2],
      score: parseFloat(m[3]),
      content: m[4].replace(/^ {4}/gm, "").trim(),
    });
  }

  // 解析反证：- 《source》@topic (score=0.xxxx)\n  content
  const counterRe = /-\s*《([^》]+)》@(\S+)\s*\([^)]*score=([\d.]+)[^)]*\)\s*\n([\s\S]*?)(?=-\s*《|$)/g;
  while ((m = counterRe.exec(counterSection)) !== null) {
    results.push({
      source: m[1],
      topic: m[2],
      score: parseFloat(m[3]),
      content: m[4].replace(/^ {2}/gm, "").trim(),
      isCounter: true,
    });
  }

  return results;
}

/* ─── 单条引用卡片 ─── */
function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [expanded, setExpanded] = useState(false);

  // 评分等级色彩
  const scoreColor = citation.score >= 0.75 ? "var(--jade)"
    : citation.score >= 0.5 ? "var(--gold)"
    : "var(--text-3)";

  return (
    <div
      className="rounded-lg overflow-hidden transition-all duration-200"
      style={{
        background: "var(--surface)",
        border: `1px solid ${expanded ? "var(--border-strong)" : "var(--border-subtle)"}`,
        boxShadow: expanded ? "var(--shadow-sm)" : "none",
      }}
    >
      {/* 卡片头部 - 可点击展开 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors duration-150"
        style={{ background: expanded ? "var(--surface-2)" : "transparent" }}
      >
        {/* 序号 */}
        <span
          className="shrink-0 w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold"
          style={{
            background: citation.isCounter ? "var(--cinnabar-light)" : "rgba(45,62,95,0.08)",
            color: citation.isCounter ? "var(--cinnabar)" : "var(--scholar-blue)",
          }}
        >
          {index + 1}
        </span>

        {/* 古籍名 */}
        <span
          className="text-xs font-semibold truncate"
          style={{
            color: citation.isCounter ? "var(--cinnabar)" : "var(--scholar-blue)",
            fontFamily: "var(--font-display)",
          }}
        >
          {citation.isCounter ? "反" : ""}《{citation.source}》
        </span>

        {/* 主题标签 */}
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium"
          style={{ background: "var(--surface-2)", color: "var(--text-3)" }}
        >
          {citation.topic}
        </span>

        {/* 评分 */}
        <span
          className="shrink-0 ml-auto px-1.5 py-0.5 rounded text-[10px] font-bold tabular-nums"
          style={{ color: scoreColor, background: "var(--surface-2)" }}
        >
          {(citation.score * 100).toFixed(0)}%
        </span>

        {/* 展开箭头 */}
        <svg
          width="10" height="10" viewBox="0 0 12 12" fill="none"
          className="shrink-0"
          style={{
            transform: expanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
            color: "var(--text-4)",
          }}
        >
          <path d="M4.5 2.5L7.5 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* 展开区域：完整条文 */}
      <div
        style={{
          maxHeight: expanded ? 300 : 0,
          opacity: expanded ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.3s ease, opacity 0.2s ease",
        }}
      >
        <div
          className="px-3.5 pb-3 pt-0 text-xs leading-relaxed"
          style={{
            color: "var(--text-2)",
            borderLeft: `3px solid ${citation.isCounter ? "var(--cinnabar)" : "var(--scholar-blue)"}`,
            marginLeft: 14,
            marginRight: 14,
            paddingLeft: 12,
            paddingTop: 8,
            paddingBottom: 8,
            background: citation.isCounter ? "var(--cinnabar-light)" : "rgba(45,62,95,0.04)",
            borderRadius: 6,
            whiteSpace: "pre-wrap",
            maxHeight: 240,
            overflowY: "auto",
          }}
        >
          {citation.content}
        </div>
      </div>
    </div>
  );
}

/* ─── 折叠面板：古籍引用区域 ─── */
function CitationsBlock({ citations }: { citations?: string }) {
  const [open, setOpen] = useState(false);
  const parsed = parseCitations(citations ?? "");
  if (parsed.length === 0) return null;

  const mainCount = parsed.filter(c => !c.isCounter).length;
  const counterCount = parsed.filter(c => c.isCounter).length;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs font-medium transition-all duration-200"
        style={{ color: open ? "var(--scholar-blue)" : "var(--text-4)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
          <path d="M4.5 2.5L7.5 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        古籍引用
        <span
          className="px-1.5 py-0.5 rounded text-[10px] font-bold tabular-nums"
          style={{ background: "var(--scholar-blue)", color: "var(--surface)" }}
        >
          {mainCount}{counterCount > 0 ? `+${counterCount}反` : ""}
        </span>
      </button>
      <div
        style={{
          maxHeight: open ? 800 : 0,
          opacity: open ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.35s ease, opacity 0.2s ease, margin-top 0.2s ease",
          marginTop: open ? 8 : 0,
        }}
      >
        <div className="flex flex-col gap-2">
          {parsed.map((c, i) => (
            <CitationCard key={`${c.source}-${c.topic}-${i}`} citation={c} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── 折叠面板：思考过程 ─── */
function ReasoningBlock({ content }: { content: string }) {
  const [open, setOpen] = useState(false);
  if (!content || content.trim().length === 0) return null;
  return (
    <div className="mb-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs font-medium transition-all duration-200"
        style={{ color: open ? "var(--scholar-blue)" : "var(--text-4)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
          <path d="M4.5 2.5L7.5 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        思考过程
        <span className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: "var(--surface-2)", color: "var(--text-4)" }}>
          {content.length} 字
        </span>
      </button>
      <div
        style={{
          maxHeight: open ? 600 : 0,
          opacity: open ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.3s ease, opacity 0.2s ease, margin-top 0.2s ease",
          marginTop: open ? 8 : 0,
        }}
      >
        <div
          className="px-4 py-3 rounded-lg text-xs leading-relaxed whitespace-pre-wrap"
          style={{
            background: "var(--bg-card)",
            color: "var(--text-4)",
            border: "1px solid var(--border-subtle)",
            borderLeft: "3px solid var(--text-4)",
            maxHeight: 400,
            overflowY: "auto",
          }}
        >
          {content}
        </div>
      </div>
    </div>
  );
}

/* ─── 常量 ─── */
const QUICK_QUESTIONS = [
  { icon: "⚖", label: "旺衰格局", q: "请详细分析我的日主旺衰和格局" },
  { icon: "✦", label: "事业方向", q: "我的事业发展方向是什么？适合什么职业？" },
  { icon: "♡", label: "感情婚姻", q: "我的感情运势如何？什么时候有姻缘？" },
  { icon: "◈", label: "今年运势", q: "今年运势怎么样？有什么需要注意的？" },
  { icon: "☯", label: "性格特点", q: "从命盘看我的性格特点是什么？" },
  { icon: "☘", label: "健康养生", q: "健康方面需要注意什么？五行如何养生？" },
];

const STALL_TIMEOUT_MS = 60000; // 60 秒无数据 → 判定中断

interface Props { analysisId: string; school?: string; }

export default function ChatPanel({ analysisId, school = "ziping" }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [showQuick, setShowQuick] = useState(true);

  /* 流式状态 */
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingReasoning, setStreamingReasoning] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mountedRef = useRef(true);
  const abortRef = useRef<AbortController | null>(null);
  const stallTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const contentRef = useRef(""); // 累积的 token 内容

  /* ─── 失速检测 ─── */
  const clearStallTimer = useCallback(() => {
    if (stallTimerRef.current) {
      clearTimeout(stallTimerRef.current);
      stallTimerRef.current = null;
    }
  }, []);

  const resetStallTimer = useCallback(() => {
    clearStallTimer();
    stallTimerRef.current = setTimeout(() => {
      stallTimerRef.current = null;
      if (mountedRef.current) {
        abortRef.current?.abort();
        setIsStreaming(false);
        // 保存已收到的部分内容
        if (contentRef.current) {
          setMessages(prev => [...prev, { role: "assistant", content: contentRef.current }]);
          contentRef.current = "";
        }
        setStreamingContent("");
        setStreamingReasoning("");
        setError("连接中断，请重试");
      }
    }, STALL_TIMEOUT_MS);
  }, [clearStallTimer]);

  /* ─── 加载历史 ─── */
  useEffect(() => {
    let cancelled = false;
    mountedRef.current = true;
    getChatHistory(analysisId, school).then((data) => {
      if (cancelled) return;
      if (data.messages && data.messages.length > 0) { setMessages(data.messages); setShowQuick(false); }
    }).catch(() => { /* 历史加载失败静默处理 */ });
    return () => { cancelled = true; mountedRef.current = false; };
  }, [analysisId, school]);

  /* ─── 自动滚动 ─── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  /* ─── 清理 ─── */
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
      clearStallTimer();
    };
  }, [clearStallTimer]);

  /* ─── 发送消息（SSE 流式） ─── */
  function handleSend(text?: string) {
    const message = text || input.trim();
    if (!message || isStreaming) return;
    setInput(""); setError(""); setShowQuick(false);
    setMessages(prev => [...prev, { role: "user", content: message }]);
    setIsStreaming(true);
    setStreamingContent("");
    setStreamingReasoning("");
    contentRef.current = "";

    resetStallTimer();

    const controller = sendChatMessageStream(
      analysisId,
      message,
      school,
      /* onEvent */
      (evt: ChatStreamEvent) => {
        if (!mountedRef.current) return;
        resetStallTimer();
        if (evt.type === "token") {
          contentRef.current += evt.content;
          setStreamingContent(contentRef.current);
        } else if (evt.type === "reasoning") {
          setStreamingReasoning(prev => prev + evt.content);
        }
        // heartbeat/tool_call/tool_result 只重置 stall timer，不显示内容
      },
      /* onError */
      (err: Error) => {
        if (!mountedRef.current) return;
        clearStallTimer();
        setIsStreaming(false);
        if (contentRef.current) {
          setMessages(prev => [...prev, { role: "assistant", content: contentRef.current }]);
          contentRef.current = "";
        }
        setStreamingContent("");
        setStreamingReasoning("");
        const errMsg = err.message;
        if (errMsg.includes("LLM") && (errMsg.includes("未配置") || errMsg.includes("503") || errMsg.includes("not configured"))) {
          setError("LLM 服务未配置。请在服务端设置 LLM_API_KEY 环境变量后重启。");
        } else {
          setError(errMsg);
        }
      },
      /* onDone */
      () => {
        if (!mountedRef.current) return;
        clearStallTimer();
        setIsStreaming(false);
        if (contentRef.current) {
          setMessages(prev => [...prev, { role: "assistant", content: contentRef.current }]);
          contentRef.current = "";
        }
        setStreamingContent("");
        setStreamingReasoning("");
        // 刷新历史以获取后端生成的 citations（古籍引用溯源）
        getChatHistory(analysisId, school).then((data) => {
          if (!mountedRef.current) return;
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          }
        }).catch(() => { /* 静默处理 */ });
      },
    );

    abortRef.current = controller;
  }

  function handleKeyDown(e: React.KeyboardEvent) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }

  /* ─── 中断流式 ─── */
  function handleStop() {
    abortRef.current?.abort();
    clearStallTimer();
    setIsStreaming(false);
    if (contentRef.current) {
      setMessages(prev => [...prev, { role: "assistant", content: contentRef.current }]);
      contentRef.current = "";
    }
    setStreamingContent("");
    setStreamingReasoning("");
  }

  return (
    <section className="card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-4 sm:px-7 py-[18px]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, var(--cinnabar), #c0392b)", boxShadow: "0 2px 8px rgba(192,57,43,0.25)" }}>
            <span className="text-lg text-white">☯</span>
          </div>
          <div>
            <h3 className="font-bold text-base tracking-wide leading-tight" style={{ fontFamily: "var(--font-display)" }}>命理问答</h3>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-4)" }}>基于命盘数据 · AI 解读</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: "rgba(46,204,113,0.1)", color: "#2ecc71", border: "1px solid rgba(46,204,113,0.3)" }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "#2ecc71" }} />
              生成中
            </span>
          )}
          <span className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: "var(--surface-2)", color: "var(--text-4)", border: "1px solid var(--border-subtle)" }}>
            {school === "ziping" ? "子平法" : school === "mangpai" ? "盲派" : school === "xinpai" ? "新派" : school}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="overflow-y-auto px-7 py-6" role="log" aria-live="polite" aria-relevant="additions" style={{ maxHeight: 600, minHeight: 200 }}>
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-[72px] h-[72px] rounded-full flex items-center justify-center mb-5" style={{ background: "linear-gradient(135deg, rgba(192,57,43,0.08), rgba(45,62,95,0.08))", border: "2px dashed var(--border)" }}>
              <span className="text-[32px] opacity-60">☯</span>
            </div>
            <p className="text-[17px] font-semibold mb-2" style={{ fontFamily: "var(--font-display)" }}>向命理师提问</p>
            <p className="text-sm text-center max-w-[320px] leading-relaxed" style={{ color: "var(--text-4)" }}>
              基于你的八字命盘，AI 将结合古籍条文给出针对性解读
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`mb-6 ${msg.role === "user" ? "flex justify-end" : ""}`}
            style={{ animation: "fadeInUp 0.3s ease both", animationDelay: `${Math.min(i * 0.05, 0.3)}s` }}>
            {msg.role === "assistant" ? (
              <div className="pr-16">
                <div className="flex items-center gap-2.5 mb-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0" style={{ background: "linear-gradient(135deg, var(--cinnabar), #c0392b)" }}>
                    <span className="text-sm text-white">☯</span>
                  </div>
                  <span className="font-semibold text-[13px] tracking-wider" style={{ color: "var(--scholar-blue)", fontFamily: "var(--font-display)" }}>命理师</span>
                </div>
                <div className="markdown-body pl-10 text-[15px] leading-[1.85]" style={{ color: "var(--text-2)" }}>
                  <ReactMarkdown remarkPlugins={[RemarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
                <div className="pl-10">
                  <CitationsBlock citations={msg.citations} />
                </div>
              </div>
            ) : (
              <div className="max-w-[78%]">
                <div className="px-5 py-3.5 whitespace-pre-wrap rounded-2xl rounded-br-md" style={{
                  fontSize: 15, lineHeight: 1.7, color: "var(--ink)",
                  background: "var(--scholar-blue)", border: "none",
                  boxShadow: "0 2px 8px rgba(45,62,95,0.15)",
                }}>
                  {msg.content}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* 流式渲染中的助手消息 */}
        {isStreaming && (
          <div className="mb-6 pr-16" style={{ animation: "fadeInUp 0.3s ease both" }}>
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0" style={{ background: "linear-gradient(135deg, var(--cinnabar), #c0392b)" }}>
                <span className="text-sm text-white">☯</span>
              </div>
              <span className="font-semibold text-[13px] tracking-wider" style={{ color: "var(--scholar-blue)", fontFamily: "var(--font-display)" }}>命理师</span>
            </div>
            <div className="pl-10">
              {/* reasoning 折叠面板 */}
              <ReasoningBlock content={streamingReasoning} />
              {/* 正文逐字渲染 */}
              {streamingContent ? (
                <div className="markdown-body text-[15px] leading-[1.85]" style={{ color: "var(--text-2)" }}>
                  <ReactMarkdown remarkPlugins={[RemarkGfm]}>{streamingContent}</ReactMarkdown>
                  <span className="inline-block w-[2px] h-[16px] ml-0.5 align-text-bottom animate-pulse" style={{ background: "var(--scholar-blue)" }} />
                </div>
              ) : (
                <div className="flex items-center gap-1.5" style={{ padding: "12px 0" }}>
                  {[0, 1, 2].map((idx) => (
                    <span key={idx} className="typing-dot" style={{
                      width: 8, height: 8, borderRadius: "50%",
                      background: "var(--scholar-blue)",
                      opacity: 0.4,
                      animation: "typingBounce 1.2s ease-in-out infinite",
                      animationDelay: `${idx * 0.15}s`,
                    }} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="px-7 py-3 border-t flex items-center gap-2" style={{ borderColor: "var(--border-subtle)", background: "rgba(220,38,38,0.04)" }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" stroke="var(--danger)" strokeWidth="1.5" /><path d="M7 4v3M7 9.5v.5" stroke="var(--danger)" strokeWidth="1.5" strokeLinecap="round" /></svg>
          <p className="font-medium" style={{ fontSize: 13, color: "var(--danger)" }}>{error}</p>
        </div>
      )}

      {/* Quick Questions */}
      {showQuick && messages.length === 0 && (
        <div className="px-7 py-6 border-t" style={{ borderColor: "var(--border-subtle)", background: "var(--bg-card)" }}>
          <p className="mb-4 font-semibold" style={{ fontSize: 13, color: "var(--text-4)", letterSpacing: "0.05em" }}>快捷提问</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {QUICK_QUESTIONS.map((item, i) => (
              <button key={i} onClick={() => handleSend(item.q)} disabled={isStreaming}
                className="group flex items-center gap-2.5 px-4 py-3 rounded-lg hover-card text-left disabled:opacity-50"
                style={{
                  fontSize: 13, fontWeight: 500,
                  color: "var(--text-2)",
                  background: "var(--surface)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <span style={{ fontSize: 16, opacity: 0.7, flexShrink: 0 }}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-7 py-5 border-t sticky bottom-0" style={{ borderColor: "var(--border-subtle)", background: "var(--surface)" }}>
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              aria-label="输入你的问题"
              placeholder="向命理师提问…"
              rows={1}
              className="w-full resize-none transition-all duration-200 focus:border-[var(--scholar-blue)] focus:shadow-[0_0_0_3px_rgba(45,62,95,0.1)]"
              style={{
                fontSize: 15, fontFamily: "var(--font-body)",
                background: "color-mix(in srgb, var(--surface) 85%, var(--ink))",
                border: "1.5px solid var(--border)",
                borderRadius: 10,
                color: "var(--ink)",
                padding: "12px 16px",
                maxHeight: 100,
                outline: "none",
              }}
              disabled={isStreaming}
            />
          </div>
          <button onClick={isStreaming ? handleStop : () => handleSend()} disabled={!isStreaming && !input.trim()}
            className="flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              width: 44, height: 44, borderRadius: 10,
              background: input.trim() ? "var(--scholar-blue)" : "var(--surface)",
              border: "none",
              boxShadow: input.trim() ? "0 2px 8px rgba(45,62,95,0.25)" : "none",
            }}
          >
            {isStreaming ? (
              /* 停止按钮 */
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <rect x="4" y="4" width="10" height="10" rx="2" fill={input.trim() ? "#fff" : "var(--text-4)"} />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3 9H15M15 9L10 4M15 9L10 14" stroke={input.trim() ? "#fff" : "var(--text-4)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
        </div>
        <p className="mt-2.5 text-center" style={{ fontSize: 11, color: "var(--text-4)", opacity: 0.6 }}>
          Enter 发送 · Shift+Enter 换行
        </p>
      </div>

      <style jsx>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-6px); opacity: 1; }
        }
        .markdown-body :global(h1),.markdown-body :global(h2),.markdown-body :global(h3)
          { color:var(--scholar-blue);margin-top:1.3rem;margin-bottom:0.6rem;font-weight:700;font-family:var(--font-display); }
        .markdown-body :global(h1){font-size:1.35rem;} .markdown-body :global(h2){font-size:1.2rem;} .markdown-body :global(h3){font-size:1.05rem;}
        .markdown-body :global(p){line-height:1.85;font-size:15;margin-bottom:0.6rem;}
        .markdown-body :global(strong){font-weight:700;color:var(--ink);}
        .markdown-body :global(ul),.markdown-body :global(ol){padding-left:1.3rem;margin-top:0.4rem;margin-bottom:0.6rem;}
        .markdown-body :global(li){margin-top:0.3rem;font-size:15;line-height:1.7;}
        .markdown-body :global(code){font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--surface-2);padding:0.12rem 0.4rem;border-radius:4px;font-size:13px;}
        .markdown-body :global(pre){background:var(--surface-2);border-radius:8px;padding:1rem;overflow-x:auto;margin-top:0.6rem;margin-bottom:0.6rem;border:1px solid var(--border-subtle);}
        .markdown-body :global(pre code){background:transparent;padding:0;font-size:13px;}
        .markdown-body :global(blockquote){border-left:3px solid var(--scholar-blue);padding-left:1rem;font-style:italic;font-size:15;opacity:0.85;margin:0.6rem 0;color:var(--text-2);}
        .markdown-body :global(hr){border-top:1px solid var(--border-subtle);margin:1.1rem 0;}
        .markdown-body :global(a){color:var(--scholar-blue);text-decoration:underline;text-underline-offset:2px;}
        .markdown-body :global(table){width:100%;font-size:15;border-collapse:collapse;margin:0.6rem 0;}
        .markdown-body :global(th){background:var(--surface-2);padding:0.55rem 0.85rem;text-align:left;font-weight:600;border-bottom:2px solid var(--border-subtle);}
        .markdown-body :global(td){padding:0.55rem 0.85rem;border-bottom:1px solid var(--border-subtle);}
      `}</style>
    </section>
  );
}
