"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeProvider";
import SettingsModal from "@/components/SettingsModal";

const NAV_ITEMS=[{href:"/",label:"排盘"},{href:"/compare",label:"合婚"}];

export default function Navbar() {
  const pathname=usePathname();
  const isAnalyzePage=pathname?.startsWith("/analyze");
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <>
      <nav
        className="fixed top-0 left-0 w-full z-50 flex items-center justify-between px-6 sm:px-8 lg:px-12 h-14"
        style={{
          background:"color-mix(in srgb,var(--surface)90%,transparent)",
          backdropFilter:"blur(16px)",
          WebkitBackdropFilter:"blur(16px)",
          borderBottom:"1px solid var(--color-border)",
        }}
      >
        <Link href="/" className="font-bold shrink-0" style={{fontSize:16,color:"var(--color-scholar-blue)",fontFamily:"var(--font-serif)"}}>
          八字排盘
        </Link>

        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(item=>{
            const isActive=pathname===item.href||(item.href!=="/"&&pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative px-5 py-2 font-medium transition-colors duration-150"
                style={{
                  fontSize:14,
                  color:isActive?"var(--color-ink)":"var(--color-text-muted)",
                  borderBottom:`${isActive?"2px solid var(--color-scholar-blue)":"none"}`,
                }}
              >
                {item.label}
              </Link>
            );
          })}
          {isAnalyzePage && (
            <span
              className="relative px-5 py-2 font-medium"
              style={{fontSize:14,color:"var(--color-ink)",borderBottom:"2px solid var(--color-scholar-blue)"}}
            >
              分析
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            aria-label="LLM 设置"
            onClick={() => setSettingsOpen(true)}
            className="flex items-center justify-center transition-colors duration-150"
            style={{
              width: 34, height: 34,
              background: "transparent",
              border: "1px solid transparent",
              cursor: "pointer",
              color: "var(--color-text-muted)",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "var(--bg-hover)"; e.currentTarget.style.borderColor = "var(--color-border-subtle)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "transparent"; }}
          >
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
          <ThemeToggle />
        </div>
      </nav>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
