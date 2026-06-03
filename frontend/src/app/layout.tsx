import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "八字排盘 · 确定性命理引擎",
  description: "算析分离架构，核心计算零 LLM 依赖。十神推导、格局筛查、喜用神判定，每一步均可追溯到确定性规则与古籍原文。",
  keywords: ["八字", "命理", "排盘", "四柱", "子平", "盲派", "新派"],
  icons: { icon: "/favicon.svg" },
  openGraph: {
    title: "八字排盘 · 确定性命理引擎",
    description: "算析分离架构，核心计算零 LLM 依赖。三大流派对比分析。",
    type: "website",
  },
  other: { "theme-color": "#faf8f3" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" style={{colorScheme:"dark light"}} suppressHydrationWarning>
      <body className="antialiased">
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--surface)] focus:text-[var(--color-text-primary)] focus:border focus:border-[var(--color-border)]" style={{top:8,left:8}}>跳到主要内容</a>
        <ThemeProvider>
          <Navbar />
          <div id="main-content" className="pt-14">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
