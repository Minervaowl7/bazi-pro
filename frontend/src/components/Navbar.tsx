"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeProvider";
import SettingsModal from "@/components/SettingsModal";
import { gsap, useGSAP } from "@/lib/gsap";

const NAV_ITEMS = [{ href: "/", label: "排盘" }, { href: "/compare", label: "合婚" }];

export default function Navbar() {
  const containerRef = useRef<HTMLElement>(null);
  const pathname = usePathname();
  const isAnalyzePage = pathname?.startsWith("/analyze");
  const [settingsOpen, setSettingsOpen] = useState(false);

  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const { contextSafe } = useGSAP(
    () => {
      if (prefersReducedMotion) {
        gsap.set(containerRef.current, { autoAlpha: 1 });
      } else {
        gsap.from(containerRef.current, {
          y: -60,
          autoAlpha: 0,
          duration: 0.7,
          ease: "power3.out",
        });
      }
    },
    { scope: containerRef },
  );

  const handleLinkEnter = contextSafe((e: React.MouseEvent<HTMLAnchorElement>) => {
    if (prefersReducedMotion) return;
    gsap.to(e.currentTarget, { scale: 1.02, duration: 0.25, ease: "power2.out" });
  });

  const handleLinkLeave = contextSafe((e: React.MouseEvent<HTMLAnchorElement>) => {
    if (prefersReducedMotion) return;
    gsap.to(e.currentTarget, { scale: 1, duration: 0.2, ease: "power2.inOut" });
  });

  const handleSettingsEnter = contextSafe((e: React.MouseEvent<HTMLButtonElement>) => {
    gsap.to(e.currentTarget, {
      scale: 1.08,
      duration: 0.2,
      ease: "power2.out",
      overwrite: "auto",
    });
    e.currentTarget.style.background = "var(--bg-hover)";
    e.currentTarget.style.color = "var(--color-text-secondary)";
  });

  const handleSettingsLeave = contextSafe((e: React.MouseEvent<HTMLButtonElement>) => {
    gsap.to(e.currentTarget, {
      scale: 1,
      duration: 0.2,
      ease: "power2.inOut",
      overwrite: "auto",
    });
    e.currentTarget.style.background = "transparent";
    e.currentTarget.style.color = "var(--color-text-muted)";
  });

  const handleThemeToggleClick = contextSafe(() => {
    gsap.to("[data-gsap='theme-icon']", {
      rotation: "+=180",
      duration: 0.5,
      ease: "back.out(1.7)",
      overwrite: "auto",
    });
  });

  return (
    <>
      <nav
        ref={containerRef}
        className="fixed top-0 left-0 w-full z-50 flex items-center justify-between px-6 sm:px-8 lg:px-12 h-14"
        style={{
          visibility: "hidden",
          background: "color-mix(in srgb, var(--surface) 88%, transparent)",
          backdropFilter: "blur(20px) saturate(1.2)",
          WebkitBackdropFilter: "blur(20px) saturate(1.2)",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <Link href="/" className="font-bold shrink-0 flex items-center gap-2.5" style={{ fontSize: 15, color: "var(--color-scholar-blue)", fontFamily: "var(--font-serif)", letterSpacing: "-0.01em" }}>
          <span style={{
            width: 26, height: 26, borderRadius: 7,
            background: "linear-gradient(135deg, var(--color-cinnabar), var(--color-gold))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, color: "#fff", fontWeight: 700,
          }}>命</span>
          八字排盘
        </Link>

        <div className="flex items-center gap-0.5">
          {NAV_ITEMS.map(item => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative px-4 py-2 font-medium"
                style={{
                  fontSize: 13,
                  color: isActive ? "var(--color-ink)" : "var(--color-text-muted)",
                  borderRadius: 8,
                  background: isActive ? "rgba(45,62,95,0.04)" : "transparent",
                }}
                onMouseEnter={handleLinkEnter}
                onMouseLeave={handleLinkLeave}
              >
                {item.label}
                {isActive && (
                  <span style={{
                    position: "absolute",
                    bottom: 2,
                    left: "50%",
                    transform: "translateX(-50%)",
                    width: 16,
                    height: 2,
                    borderRadius: 1,
                    background: "var(--color-cinnabar)",
                    opacity: 0.7,
                  }} />
                )}
              </Link>
            );
          })}
          {isAnalyzePage && (
            <span
              className="relative px-4 py-2 font-medium"
              style={{
                fontSize: 13,
                color: "var(--color-ink)",
                borderRadius: 8,
                background: "rgba(45,62,95,0.04)",
              }}
            >
              分析
              <span style={{
                position: "absolute",
                bottom: 2,
                left: "50%",
                transform: "translateX(-50%)",
                width: 16,
                height: 2,
                borderRadius: 1,
                background: "var(--color-cinnabar)",
                opacity: 0.7,
              }} />
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            aria-label="LLM 设置"
            onClick={() => setSettingsOpen(true)}
            className="flex items-center justify-center"
            style={{
              width: 32, height: 32,
              background: "transparent",
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
              color: "var(--color-text-muted)",
            }}
            onMouseEnter={handleSettingsEnter}
            onMouseLeave={handleSettingsLeave}
          >
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
          <div
            data-gsap="theme-icon"
            onClick={handleThemeToggleClick}
            style={{ display: "inline-flex" }}
          >
            <ThemeToggle />
          </div>
        </div>
      </nav>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
