"use client";

import BirthForm from "@/components/BirthForm";
import HistorySidebar from "@/components/HistorySidebar";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div className="flex min-h-screen">
      <HistorySidebar />
      <main className="flex-1 flex items-center justify-center p-6 md:p-8 relative overflow-hidden">
        <div className="absolute top-6 right-6 z-10">
          <ThemeToggle />
        </div>

        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, var(--accent) 0%, transparent 50%), radial-gradient(circle at 80% 70%, var(--accent) 0%, transparent 45%)",
          }}
        />

        <div className="w-full max-w-lg relative z-[1]">
          <div className="mb-10">
            <div
              className="inline-block px-3 py-1 rounded-full text-xs font-medium mb-5"
              style={{
                background: "var(--accent-dim)",
                color: "var(--accent)",
                letterSpacing: "0.08em",
              }}
            >
              确定性计算引擎
            </div>
            <h1
              className="text-4xl md:text-5xl font-bold tracking-wide mb-4 leading-tight"
              style={{ color: "var(--text-primary)" }}
            >
              八字排盘
            </h1>
            <p
              className="text-sm leading-relaxed max-w-xs"
              style={{ color: "var(--text-muted)" }}
            >
              输入出生时辰，即刻排盘·深度解读
            </p>
          </div>

          <div
            className="rounded-2xl p-6 md:p-8"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              boxShadow: "var(--shadow)",
            }}
          >
            <BirthForm />
          </div>

          <div className="flex items-center justify-center gap-6 mt-8 pt-6" style={{ borderTop: "1px solid var(--border)", opacity: 0.45 }}>
            <span className="text-[11px] whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
              古籍引证
            </span>
            <span className="w-1 h-1 rounded-full" style={{ background: "var(--text-muted)" }} />
            <span className="text-[11px] whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
              零幻觉
            </span>
            <span className="w-1 h-1 rounded-full" style={{ background: "var(--text-muted)" }} />
            <span className="text-[11px] whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
              三大流派
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}