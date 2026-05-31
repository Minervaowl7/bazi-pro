"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeProvider";

const NAV_ITEMS = [
  { href: "/", label: "排盘" },
  { href: "/compare", label: "合婚" },
];

export default function Navbar() {
  const pathname = usePathname();
  const isAnalyzePage = pathname?.startsWith("/analyze");

  return (
    <nav
      className="fixed top-0 left-0 w-full z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8 h-14"
      style={{
        background: "color-mix(in srgb, var(--surface) 90%, transparent)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <Link
        href="/"
        className="text-base font-bold shrink-0"
        style={{ color: "var(--color-scholar-blue)", fontFamily: "var(--font-serif)" }}
      >
        八字排盘
      </Link>

      <div className="flex items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className="px-4 py-2 text-xs font-medium uppercase tracking-widest transition-colors"
              style={{
                color: isActive ? "var(--color-scholar-blue)" : "var(--color-text-muted)",
                borderBottom: isActive ? "2px solid var(--color-scholar-blue)" : "2px solid transparent",
              }}
            >
              {item.label}
            </Link>
          );
        })}
        {isAnalyzePage && (
          <span
            className="px-4 py-2 text-xs font-medium uppercase tracking-widest"
            style={{ color: "var(--color-scholar-blue)", borderBottom: "2px solid var(--color-scholar-blue)" }}
          >
            分析
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <ThemeToggle />
      </div>
    </nav>
  );
}
