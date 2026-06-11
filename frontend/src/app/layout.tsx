import type { Metadata } from "next";
import { Noto_Serif_SC } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import Navbar from "@/components/Navbar";

const notoSerifSC = Noto_Serif_SC({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-serif-loaded",
  display: "swap",
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  metadataBase: new URL("https://bazi.pro"),
  title: "八字排盘 · 确定性命理引擎 | 古法排盘 · 智能解读",
  description:
    "2964 条古籍条文驱动的八字排盘引擎。子平、盲派、新派三大流派并行分析，六层格局筛查，喜用神推导，每一步均可追溯至古籍原文。零 LLM 依赖的确定性计算核心。",
  keywords: [
    "八字排盘", "命理分析", "四柱推命", "子平真诠", "盲派命理", "新派八字",
    "格局筛查", "喜用神", "古籍检索", "旺衰判定", "十神推导", "紫微斗数",
  ],
  icons: { icon: "/favicon.svg" },
  openGraph: {
    title: "八字排盘 · 确定性命理引擎",
    description:
      "算析分离架构，核心计算零 LLM 依赖。三大流派对比分析，2964 条古籍条文驱动，每一步推导皆可追溯至古籍原文。",
    type: "website",
    locale: "zh_CN",
    siteName: "八字排盘 · 确定性命理引擎",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "八字排盘 · 确定性命理引擎" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "八字排盘 · 确定性命理引擎",
    description:
      "子平、盲派、新派三大流派并行分析。六层格局筛查，喜用神推导，古籍条文驱动。",
    images: ["/og.png"],
  },
  other: { "theme-color": "#f5f2eb" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className={notoSerifSC.variable} suppressHydrationWarning data-scroll-behavior="smooth">
      <body className="antialiased">
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--surface)] focus:text-[var(--ink)] focus:border focus:border-[var(--border)]" style={{top:8,left:8}}>跳到主要内容</a>
        <ThemeProvider>
          <Navbar />
          {/* Navbar 滚动检测哨兵 — IntersectionObserver 观测此元素 */}
          <div id="scroll-sentinel" aria-hidden="true" style={{ position: "absolute", top: 0, left: 0, width: 1, height: 1, pointerEvents: "none" }} />
          <main id="main-content" className="pt-14">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
