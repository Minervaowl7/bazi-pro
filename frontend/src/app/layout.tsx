import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import Navbar from "@/components/Navbar";

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
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider>
          <Navbar />
          <div className="pt-14">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
