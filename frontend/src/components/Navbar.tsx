"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import SettingsModal from "./SettingsModal";
import { useTheme } from "./ThemeProvider";

const NAV_ITEMS = [
  { href: "/", label: "排盘" },
  { href: "/compare", label: "合婚" },
];

export default function Navbar() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center transition-colors duration-200"
        style={{
          background: scrolled
            ? "color-mix(in srgb, var(--bg) 92%, transparent)"
            : "transparent",
          backdropFilter: scrolled ? "blur(24px) saturate(1.3)" : "none",
          WebkitBackdropFilter: scrolled ? "blur(24px) saturate(1.3)" : "none",
          borderBottom: scrolled
            ? "1px solid var(--border)"
            : "1px solid transparent",
        }}
      >
        <div className="w-full max-w-[1200px] mx-auto px-5 flex items-center justify-between">
          {/* 品牌标识 */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div
              className="w-[30px] h-[30px] rounded-[7px] flex items-center justify-center text-white text-[15px] font-bold"
              style={{
                background:
                  "linear-gradient(135deg, var(--cinnabar), var(--gold))",
              }}
            >
              命
            </div>
            <span
              className="text-[14px] tracking-[0.5px]"
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 600,
                color: "var(--ink)",
              }}
            >
              八字命理
            </span>
          </Link>

          {/* 导航链接 */}
          <div className="flex items-center gap-1.5">
            {NAV_ITEMS.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="relative px-3 py-1.5 text-[13px] rounded-md transition-colors duration-150"
                  style={{
                    fontFamily: "var(--font-body)",
                    fontWeight: active ? 600 : 400,
                    color: active ? "var(--cinnabar)" : "var(--text-2)",
                    background: active
                      ? "rgba(201,100,66,0.06)"
                      : "transparent",
                  }}
                >
                  {item.label}
                  {active && (
                    <span
                      className="absolute bottom-[-1px] left-1/2 -translate-x-1/2 w-4 h-[2px] rounded-full"
                      style={{ background: "var(--cinnabar)" }}
                    />
                  )}
                </Link>
              );
            })}

            {/* 分隔线 */}
            <div
              className="w-px h-4 mx-1.5"
              style={{ background: "var(--border)" }}
            />

            {/* 功能按钮 */}
            <button
              onClick={() => setSettingsOpen(true)}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-150"
              style={{ color: "var(--text-2)" }}
              aria-label="设置"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>

            <button
              onClick={toggleTheme}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors duration-150"
              style={{ color: "var(--text-2)" }}
              aria-label="切换主题"
            >
              {theme === "light" ? (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              ) : (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </nav>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
