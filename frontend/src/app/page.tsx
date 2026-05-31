"use client";

import BirthForm from "@/components/BirthForm";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div className="min-h-screen" style={{ background: "var(--background)" }}>
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      <main className="flex items-center justify-center min-h-screen p-6 md:p-8">
        <div className="w-full max-w-md relative z-[1]">
          <div className="mb-8 text-center">
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: "var(--color-scholar-blue)", fontFamily: "var(--font-serif)" }}
            >
              八字排盘
            </h1>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              输入出生时辰，即刻排盘 · 深度解读
            </p>
          </div>

          <div
            className="p-6 md:p-8 rounded-2xl"
            style={{
              background: "var(--surface)",
              boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
              border: "1px solid var(--color-border)",
            }}
          >
            <BirthForm />
          </div>

          <div className="flex items-center justify-center gap-8 mt-6">
            {["古籍引证", "零幻觉", "三大流派"].map((text) => (
              <span
                key={text}
                className="text-[11px] tracking-wider"
                style={{ color: "var(--color-text-muted)" }}
              >
                {text}
              </span>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
