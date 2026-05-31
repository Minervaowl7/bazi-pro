"use client";

import BirthForm from "@/components/BirthForm";
import { ThemeToggle } from "@/components/ThemeProvider";

export default function Home() {
  return (
    <div className="min-h-[100dvh] flex flex-col relative overflow-hidden">
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(138,59,42,0.04), transparent 70%)",
        }}
      />

      <header className="flex items-center justify-between px-6 py-5 relative z-10">
        <div className="flex items-center gap-3">
          <span
            className="text-lg font-bold tracking-[0.15em]"
            style={{ color: "var(--accent)" }}
          >
            命理
          </span>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{
              background: "var(--accent-dim)",
              color: "var(--accent)",
              border: "1px solid rgba(138,59,42,0.12)",
            }}
          >
            v2
          </span>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-16 relative z-10">
        <div className="w-full max-w-[440px]">
          <div className="mb-12">
            <h1
              className="text-5xl font-bold tracking-[0.08em] mb-4 leading-[1.1]"
              style={{ color: "var(--text-primary)" }}
            >
              八字排盘
            </h1>
            <p
              className="text-[15px] leading-relaxed max-w-[320px]"
              style={{ color: "var(--text-muted)" }}
            >
              输入出生时辰，即刻排盘解读
            </p>
          </div>

          <div
            className="rounded-2xl p-7"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 8px 32px rgba(0,0,0,0.03)",
            }}
          >
            <BirthForm />
          </div>

          <div
            className="flex items-center justify-center gap-8 mt-10"
          >
            {[
              { label: "古籍引证", icon: "典" },
              { label: "零幻觉", icon: "真" },
              { label: "三派参断", icon: "流" },
            ].map((item, i) => (
              <div key={item.label} className="flex items-center gap-3">
                {i > 0 && (
                  <span
                    className="w-px h-4 -ml-3"
                    style={{ background: "var(--border)" }}
                  />
                )}
                <div className="flex items-center gap-2">
                  <span
                    className="w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-bold"
                    style={{
                      background: "var(--accent-dim)",
                      color: "var(--accent)",
                    }}
                  >
                    {item.icon}
                  </span>
                  <span
                    className="text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {item.label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
