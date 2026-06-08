"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import { sendChatMessage, getChatHistory, type ChatMessage } from "@/lib/api";

function CitationsBlock({ citations }: { citations?: string }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.trim().length === 0) return null;
  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs font-medium transition-all duration-200"
        style={{ color: open ? "var(--scholar-blue)" : "var(--text-4)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
          <path d="M4.5 2.5L7.5 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        古籍依据
      </button>
      <div
        style={{
          maxHeight: open ? 400 : 0,
          opacity: open ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.3s ease, opacity 0.2s ease, margin-top 0.2s ease",
          marginTop: open ? 8 : 0,
        }}
      >
        <div
          className="px-4 py-3 rounded-lg text-xs leading-relaxed"
          style={{
            background: "var(--bg-card)",
            color: "var(--text-3)",
            border: "1px solid var(--border)",
            borderLeft: "3px solid var(--scholar-blue)",
          }}
        >
          {citations}
        </div>
      </div>
    </div>
  );
}

const QUICK_QUESTIONS = [
  { icon: "⚖", label: "旺衰格局", q: "请详细分析我的日主旺衰和格局" },
  { icon: "✦", label: "事业方向", q: "我的事业发展方向是什么？适合什么职业？" },
  { icon: "♡", label: "感情婚姻", q: "我的感情运势如何？什么时候有姻缘？" },
  { icon: "◈", label: "今年运势", q: "今年运势怎么样？有什么需要注意的？" },
  { icon: "☯", label: "性格特点", q: "从命盘看我的性格特点是什么？" },
  { icon: "☘", label: "健康养生", q: "健康方面需要注意什么？五行如何养生？" },
];

interface Props { analysisId: string; school?: string; }

export default function ChatPanel({ analysisId, school = "ziping" }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showQuick, setShowQuick] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    let cancelled = false;
    mountedRef.current = true;
    getChatHistory(analysisId, school).then((data) => {
      if (cancelled) return;
      if (data.messages && data.messages.length > 0) { setMessages(data.messages); setShowQuick(false); }
    }).catch(() => {});
    return () => { cancelled = true; mountedRef.current = false; };
  }, [analysisId, school]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const message = text || input.trim();
    if (!message || loading) return;
    setInput(""); setError(""); setShowQuick(false);
    setMessages(prev => [...prev, { role: "user", content: message }]);
    setLoading(true);
    try {
      const data = await sendChatMessage(analysisId, message, school);
      if (!mountedRef.current) return;
      setMessages(prev => [...prev, { role: "assistant", content: data.reply, citations: data.citations }]);
    } catch (err) {
      if (!mountedRef.current) return;
      const errMsg = err instanceof Error ? err.message : "发送失败";
      if (errMsg.includes("LLM") && (errMsg.includes("未配置") || errMsg.includes("503") || errMsg.includes("not configured"))) {
        setError("LLM 服务未配置。请在服务端设置 LLM_API_KEY 环境变量后重启。");
      } else { setError(errMsg); }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }

  return (
    <section className="card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-7 py-[18px]">
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
          <span className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: "var(--surface-2)", color: "var(--text-4)", border: "1px solid var(--border-subtle)" }}>
            {school === "ziping" ? "子平法" : school === "mangpai" ? "盲派" : school === "xinpai" ? "新派" : school}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="overflow-y-auto px-7 py-6" style={{ maxHeight: 600, minHeight: 200 }}>
        {messages.length === 0 && !loading && (
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

        {loading && (
          <div className="mb-6 pr-16" style={{ animation: "fadeInUp 0.3s ease both" }}>
            <div className="flex items-center gap-2.5 mb-3">
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg, var(--cinnabar), #c0392b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 14, color: "#fff" }}>☯</span>
              </div>
              <span className="font-semibold" style={{ fontSize: 13, color: "var(--scholar-blue)", fontFamily: "var(--font-display)", letterSpacing: "0.05em" }}>命理师</span>
            </div>
            <div className="flex items-center gap-1.5 ml-[40px]" style={{ padding: "12px 0" }}>
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
              <button key={i} onClick={() => handleSend(item.q)} disabled={loading}
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
                background: "var(--surface-2)",
                border: "1.5px solid var(--border-subtle)",
                borderRadius: 10,
                color: "var(--ink)",
                padding: "12px 16px",
                maxHeight: 100,
                outline: "none",
              }}
              disabled={loading}
            />
          </div>
          <button onClick={() => handleSend()} disabled={loading || !input.trim()}
            className="flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              width: 44, height: 44, borderRadius: 10,
              background: input.trim() ? "var(--scholar-blue)" : "var(--surface-2)",
              border: "none",
              boxShadow: input.trim() ? "0 2px 8px rgba(45,62,95,0.25)" : "none",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9H15M15 9L10 4M15 9L10 14" stroke={input.trim() ? "#fff" : "var(--text-4)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
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
