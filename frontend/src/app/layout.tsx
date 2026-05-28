import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Noto_Serif_SC } from "next/font/google";

const notoSerifSC = Noto_Serif_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "八字排盘 · 命理解读",
  description: "确定性八字命理分析引擎 · 古籍引证 · 零幻觉",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning className={notoSerifSC.variable}>
      <body className="antialiased" style={{ fontFamily: "var(--font-serif), 'Noto Serif SC', 'Source Han Serif SC', serif" }}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
