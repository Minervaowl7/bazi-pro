"use client";

import BirthForm from "@/components/BirthForm";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div
      className="min-h-screen flex items-center justify-center relative"
      style={{ background: "#FAF9F6" }}
    >
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-lg px-6 py-12">
        <div className="mb-10 text-center">
          <div
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium mb-6"
            style={{
              background: "var(--gold-dim)",
              color: "var(--gold)",
              letterSpacing: "0.08em",
              border: "1px solid rgba(193,154,66,0.15)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: "var(--gold)" }}
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
            className="text-sm leading-relaxed"
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
            boxShadow: "var(--shadow-md)",
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
    </div>
  );
}
