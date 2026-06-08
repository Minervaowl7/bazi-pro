"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getHistory } from "@/lib/api";

interface HistoryItem {
  id: string;
  status: string;
  day_master?: string;
  pattern?: string;
  created_at?: string;
}

export default function HistorySidebar() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  const backendDownRef = useRef(false);

  async function loadHistory() {
    try {
      const data = await getHistory(1, 20);
      backendDownRef.current = false;
      const all = data.analyses || [];
      const seen = new Set<string>();
      const unique: HistoryItem[] = [];
      for (const item of all) {
        const key = `${item.day_master}|${item.pattern}|${item.status}`;
        if (!seen.has(key)) {
          seen.add(key);
          unique.push(item);
        }
      }
      setItems(unique.slice(0, 10));
    } catch {
      backendDownRef.current = true;
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory(); // eslint-disable-line react-hooks/set-state-in-effect
    const interval = setInterval(() => {
      if (!backendDownRef.current) {
        loadHistory();
      }
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  if (collapsed) {
    return (
      <div
        className="w-12 flex flex-col items-center pt-5 shrink-0"
        style={{
          borderRight: "1px solid var(--border)",
          background: "var(--surface-2)",
        }}
      >
        <button
          onClick={() => setCollapsed(false)}
          className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 hover:bg-[var(--surface-2)]"
          style={{ color: "var(--text-3)" }}
          title="展开"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </button>
      </div>
    );
  }

  return (
    <div
      className="w-56 flex flex-col shrink-0"
      style={{
        borderRight: "1px solid var(--border)",
        background: "var(--surface-2)",
      }}
    >
      <div
        className="px-4 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <span
          className="text-xs font-medium tracking-wide uppercase"
          style={{ color: "var(--text-3)" }}
        >
          历史记录
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={loadHistory}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200 hover:bg-[var(--surface-2)]"
            style={{ color: "var(--text-3)" }}
            title="刷新"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200 hover:bg-[var(--surface-2)]"
            style={{ color: "var(--text-3)" }}
            title="收起"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading && items.length === 0 ? (
          <div className="px-4 py-8 space-y-3">
            <div className="animate-shimmer h-3 w-20 rounded-md" />
            <div className="animate-shimmer h-3 w-14 rounded-md" />
            <div className="animate-shimmer h-3 w-16 rounded-md" />
          </div>
        ) : items.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-xs" style={{ color: "var(--text-3)" }}>
              暂无记录
            </p>
          </div>
        ) : (
          <div className="py-2">
            {items.map((item) => (
              <Link
                key={item.id}
                href={`/analyze/${item.id}`}
                className="block px-4 py-3 transition-all duration-200 rounded-r-lg mx-2 hover:bg-[var(--surface-2)]"
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className="text-xs font-medium"
                    style={{ color: "var(--ink)" }}
                  >
                    {item.day_master || "?"}日主
                  </span>
                  <span
                    className={`rounded-full shrink-0 ${
                      item.status === "completed"
                        ? ""
                        : item.status === "processing"
                          ? "animate-pulse"
                          : ""
                    }`}
                    style={{
                      width: 6,
                      height: 6,
                      backgroundColor:
                        item.status === "completed"
                          ? "var(--success)"
                          : item.status === "processing"
                            ? "var(--wx-water)"
                            : "var(--text-3)",
                    }}
                  />
                </div>
                <div
                  className="text-xs truncate"
                  style={{ color: "var(--text-3)" }}
                >
                  {item.pattern || item.id}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
      <div
        className="px-4 py-3"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <Link
          href="/"
          className="text-xs font-medium hover:text-[var(--cinnabar)] transition-colors duration-200"
          style={{ color: "var(--text-3)" }}
        >
          + 新分析
        </Link>
      </div>
    </div>
  );
}
