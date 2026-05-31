"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import { sendChatMessage, getChatHistory, type ChatMessage } from "@/lib/api";

interface Props {
  analysisId: string;
}

const QUICK_QUESTIONS = [
  "我的事业发展方向是什么？",
  "我的感情运势如何？",
  "今年运势怎么样？",
  "我的性格特点是什么？",
  "适合什么样的职业？",
  "健康方面需要注意什么？",
];

export default function ChatPanel({ analysisId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showQuick, setShowQuick] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    getChatHistory(analysisId)
      .then((data) => {
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
          setShowQuick(false);
        }
      })
      .catch(() => {});
  }, [analysisId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const message = text || input.trim();
    if (!message || loading) return;

    setInput("");
    setError("");
    setShowQuick(false);

    const userMsg: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendChatMessage(analysisId, message);
      const assistantMsg: ChatMessage = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "发送失败";
      if (errMsg.includes("LLM") && (errMsg.includes("未配置") || errMsg.includes("503") || errMsg.includes("not configured"))) {
        setError("LLM 服务未配置。请在服务端设置 LLM_API_KEY 环境变量后重启。");
      } else {
        setError(errMsg);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl overflow-hidden animate-fade-in flex flex-col" style={{ boxShadow: "var(--shadow-sm)" }}>
      <div className="px-6 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <span
            className="w-7 h-7 rounded-lg flex items-center justify-center text-xs"
            style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}
          >
            问
          </span>
          <h3 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
            命理问答
          </h3>
        </div>
        <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          基于命盘数据 · AI 解读
        </span>
      </div>

      <div className="px-5 py-4 max-h-[600px] overflow-y-auto flex-1" style={{ minHeight: 120 }}>
        {messages.length === 0 && !loading && (
          <div className="text-center py-6">
            <p className="text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              向命理师提问，深入了解你的命盘
            </p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              基于你的八字数据，AI 将给出针对性解读
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 ${msg.role === "user" ? "flex justify-end" : ""}`}
          >
            {msg.role === "assistant" ? (
              <div className="pr-8">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <span className="text-xs" style={{ color: "var(--accent)" }}>☯</span>
                  <span className="text-xs font-medium" style={{ color: "var(--accent)" }}>命理师</span>
                </div>
                <div
                  className="markdown-body"
                  style={{ color: "var(--text-secondary)" }}
                >
                  <ReactMarkdown remarkPlugins={[RemarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            ) : (
              <div className="max-w-[80%]">
                <div
                  className="text-sm leading-relaxed px-4 py-2.5 rounded-2xl rounded-br-md whitespace-pre-wrap"
                  style={{
                    background: "var(--bg-elevated)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {msg.content}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="mb-4 pr-8">
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-xs" style={{ color: "var(--accent)" }}>☯</span>
              <span className="text-xs font-medium" style={{ color: "var(--accent)" }}>命理师</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--accent)", animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--accent)", animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--accent)", animationDelay: "300ms" }} />
              </div>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>正在思考...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="px-5 py-2 border-t border-[var(--border)] shrink-0">
          <p className="text-xs" style={{ color: "var(--danger)" }}>{error}</p>
        </div>
      )}

      {showQuick && messages.length === 0 && (
        <div className="px-5 py-3 border-t border-[var(--border)] shrink-0">
          <p className="text-xs mb-2.5" style={{ color: "var(--text-muted)" }}>快捷提问</p>
          <div className="flex flex-wrap gap-2">
            {QUICK_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="text-xs px-3.5 py-1.5 rounded-full transition-all duration-200 hover:scale-[1.03] hover:shadow-md disabled:opacity-50 disabled:hover:scale-100"
                style={{
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  color: "var(--text-secondary)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.color = "var(--accent)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="px-5 py-3 border-t border-[var(--border)] shrink-0 sticky bottom-0 bg-[var(--bg-card)]">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题... (Enter 发送，Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none text-sm px-3.5 py-2.5 rounded-xl focus:outline-none transition-colors"
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              maxHeight: 100,
            }}
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: "var(--text-primary)",
              color: "var(--bg-primary)",
            }}
          >
            发送
          </button>
        </div>
      </div>

      <style jsx>{`
        .markdown-body {
          line-height: 1.625;
          font-size: 0.875rem;
        }
        .markdown-body :global(h1),
        .markdown-body :global(h2),
        .markdown-body :global(h3) {
          color: var(--accent);
          margin-top: 1rem;
          margin-bottom: 0.5rem;
          font-weight: 600;
        }
        .markdown-body :global(h1) { font-size: 1.25rem; }
        .markdown-body :global(h2) { font-size: 1.125rem; }
        .markdown-body :global(h3) { font-size: 1rem; }
        .markdown-body :global(p) {
          line-height: 1.625;
          font-size: 0.875rem;
          margin-bottom: 0.5rem;
        }
        .markdown-body :global(strong) {
          font-weight: 600;
          color: var(--text-primary);
        }
        .markdown-body :global(em) {
          font-style: italic;
        }
        .markdown-body :global(ul),
        .markdown-body :global(ol) {
          padding-left: 1rem;
          margin-top: 0.25rem;
          margin-bottom: 0.5rem;
        }
        .markdown-body :global(ul) {
          list-style-type: disc;
        }
        .markdown-body :global(ol) {
          list-style-type: decimal;
        }
        .markdown-body :global(li) {
          margin-top: 0.25rem;
          margin-bottom: 0.25rem;
          font-size: 0.875rem;
        }
        .markdown-body :global(code) {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          background: var(--bg-secondary);
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-size: 0.75rem;
        }
        .markdown-body :global(pre) {
          background: var(--bg-secondary);
          border-radius: 0.75rem;
          padding: 1rem;
          overflow-x: auto;
          margin-top: 0.5rem;
          margin-bottom: 0.5rem;
        }
        .markdown-body :global(pre code) {
          background: transparent;
          padding: 0;
          font-size: 0.75rem;
        }
        .markdown-body :global(blockquote) {
          border-left: 2px solid var(--accent);
          padding-left: 1rem;
          font-style: italic;
          font-size: 0.875rem;
          opacity: 0.9;
          margin-top: 0.5rem;
          margin-bottom: 0.5rem;
        }
        .markdown-body :global(hr) {
          border-top: 1px solid var(--border);
          margin-top: 1rem;
          margin-bottom: 1rem;
        }
        .markdown-body :global(a) {
          color: var(--accent);
          text-decoration: underline;
        }
        .markdown-body :global(a:hover) {
          opacity: 0.8;
        }
        .markdown-body :global(table) {
          width: 100%;
          font-size: 0.875rem;
          border-collapse: collapse;
          margin-top: 0.5rem;
          margin-bottom: 0.5rem;
        }
        .markdown-body :global(th) {
          background: var(--bg-secondary);
          padding: 0.5rem 0.75rem;
          text-align: left;
          font-weight: 500;
          border-bottom: 1px solid var(--border);
        }
        .markdown-body :global(td) {
          padding: 0.5rem 0.75rem;
          border-bottom: 1px solid var(--border);
        }
      `}</style>
    </div>
  );
}
