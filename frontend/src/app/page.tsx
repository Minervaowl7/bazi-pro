"use client";

import BirthForm from "@/components/BirthForm";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div className="min-h-screen">
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      <main className="flex items-center justify-center min-h-screen p-6 md:p-8">
        <div className="w-full max-w-md relative z-[1]">
          <div className="mb-10 text-center">
            <h1
              className="text-3xl md:text-4xl font-bold tracking-wide mb-3"
              style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}
            >
              八字排盘
            </h1>
            <p
              className="text-sm"
              style={{ color: "var(--color-text-muted)" }}
            >
              输入出生时辰，即刻排盘 · 深度解读
            </p>
          </div>

          <div
            className="p-6 md:p-8 border"
            style={{
              background: "var(--surface)",
              borderColor: "var(--color-border)",
            }}
          >
            <BirthForm />
          </div>

          <div
            className="flex items-center justify-center gap-6 mt-8 pt-6 border-t"
            style={{ borderColor: "var(--color-border)" }}
          >
            {["古籍引证", "零幻觉", "三大流派"].map((text, i) => (
              <span key={text} className="flex items-center gap-6">
                {i > 0 && (
                  <span className="w-px h-3" style={{ background: "var(--color-border)" }} />
                )}
                <span
                  className="text-[10px] uppercase tracking-widest whitespace-nowrap"
                  style={{ color: "var(--color-text-muted)", fontFamily: "var(--font-sans)" }}
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
