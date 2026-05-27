"use client";

import BirthForm from "@/components/BirthForm";
import HistorySidebar from "@/components/HistorySidebar";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div className="flex min-h-screen">
      <HistorySidebar />
      <main className="flex-1 flex items-center justify-center p-8 relative">
        <div className="absolute top-6 right-6">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-lg animate-fade-in">
          <div className="text-center mb-12">
            <h1
              className="text-5xl font-bold tracking-wide mb-4"
              style={{ color: "var(--accent)", fontFamily: '"Noto Serif SC", serif' }}
            >
              八字排盘
            </h1>
            <p
              className="text-sm leading-relaxed"
              style={{ color: "var(--text-muted)" }}
            >
              输入出生时辰，即刻排盘 · 深度解读
            </p>
          </div>

          <div
            className="rounded-2xl p-8"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              boxShadow: "var(--shadow)",
            }}
          >
            <BirthForm />
          </div>

          <div className="text-center mt-10 space-y-1.5">
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              基于确定性计算引擎 · 古籍引证 · 零幻觉
            </p>
            <p className="text-xs" style={{ color: "var(--text-muted)", opacity: 0.5 }}>
              仅供传统文化学习与参考
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
