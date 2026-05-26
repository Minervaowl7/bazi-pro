"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getHistory, type HistoryItem } from "@/lib/api";

export default function HistorySidebar() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory(1, 10)
      .then((data) => setItems(data.analyses))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <aside className="w-64 bg-[var(--bg-secondary)] border-r border-[var(--border)] p-4 overflow-y-auto hidden lg:block">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-[var(--text-secondary)]">历史记录</h2>
        <Link href="/" className="text-xs text-[var(--accent)] hover:underline">
          新分析
        </Link>
      </div>

      {loading && (
        <div className="text-xs text-[var(--text-muted)] animate-pulse">加载中...</div>
      )}

      {!loading && items.length === 0 && (
        <div className="text-xs text-[var(--text-muted)]">暂无记录</div>
      )}

      <div className="space-y-2">
        {items.map((item) => (
          <Link
            key={item.id}
            href={`/analyze/${item.id}`}
            className="block p-3 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--bg-hover)] transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {item.day_master || "—"}日主
              </span>
              <span className={`text-xs ${item.status === "completed" ? "text-[var(--success)]" : item.status === "failed" ? "text-[var(--danger)]" : "text-[var(--warning)]"}`}>
                {item.status === "completed" ? "完成" : item.status === "failed" ? "失败" : "进行中"}
              </span>
            </div>
            {item.pattern && (
              <div className="text-xs text-[var(--text-secondary)]">{item.pattern}</div>
            )}
            {item.bazi && (
              <div className="text-xs text-[var(--text-muted)] font-mono mt-0.5">{item.bazi}</div>
            )}
            <div className="text-xs text-[var(--text-muted)] mt-1">
              {new Date(item.created_at).toLocaleDateString("zh-CN")}
            </div>
          </Link>
        ))}
      </div>
    </aside>
  );
}
