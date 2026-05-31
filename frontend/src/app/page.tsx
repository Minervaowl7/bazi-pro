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
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 30% 20%, rgba(96,165,250,0.03) 0%, transparent 70%), radial-gradient(ellipse 50% 40% at 75% 75%, rgba(74,222,128,0.02) 0%, transparent 60%)",
          }}
        />

        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none select-none"
          style={{
            fontSize: "clamp(180px, 25vw, 320px)",
            color: "var(--text-muted)",
            opacity: 0.015,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: "-0.05em",
          }}
        >
          命
        </div>

        <div className="w-full max-w-lg relative z-[1]">
          <div className="mb-10">
            <div
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium mb-6"
              style={{
                background: "var(--bg-hover)",
                color: "var(--text-secondary)",
                letterSpacing: "0.08em",
                border: "1px solid var(--border)",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: "var(--water)" }}
              />
              确定性计算引擎
            </div>
            <h1
              className="text-4xl md:text-5xl font-bold tracking-wide mb-4 leading-tight"
              style={{ color: "var(--text-primary)" }}
            >
              八字排盘
            </h1>
            <p
              className="text-sm leading-relaxed max-w-sm"
              style={{ color: "var(--text-muted)" }}
            >
              输入出生时辰，即刻排盘 · 深度解读
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

          <div
            className="flex items-center justify-center gap-6 mt-8 pt-6"
            style={{ borderTop: "1px solid var(--border-subtle)" }}
          >
            {["古籍引证", "零幻觉", "三大流派"].map((text, i) => (
              <span key={text} className="flex items-center gap-6">
                {i > 0 && (
                  <span
                    className="w-px h-3"
                    style={{ background: "var(--border)" }}
                  />
                )}
                <span
                  className="text-[11px] whitespace-nowrap"
                  style={{ color: "var(--text-muted)", opacity: 0.7 }}
                >
                  {text}
                </span>
              </span>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
