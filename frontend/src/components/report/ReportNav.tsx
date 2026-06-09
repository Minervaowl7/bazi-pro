"use client";

import { useEffect, useState } from "react";

const CHAPTER_NUMBERS = ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌"];

interface NavItem {
  key: string;
  title: string;
}

interface ReportNavProps {
  items: NavItem[];
  activeKey?: string;
}

export default function ReportNav({ items, activeKey }: ReportNavProps) {
  const [active, setActive] = useState(activeKey || items[0]?.key || "");

  useEffect(() => {
    if (activeKey) setActive(activeKey);
  }, [activeKey]);

  const handleClick = (key: string) => {
    setActive(key);
    const el = document.getElementById(`chapter-${key}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <nav
      className="flex flex-col gap-1"
      style={{ minWidth: 140 }}
    >
      <div
        className="text-[10px] font-medium tracking-widest uppercase mb-3 px-3"
        style={{ color: "var(--text-4)" }}
      >
        目录
      </div>
      {items.map((item, i) => {
        const num = CHAPTER_NUMBERS[i] || String(i + 1);
        const isActive = active === item.key;
        return (
          <button
            key={item.key}
            onClick={() => handleClick(item.key)}
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all duration-200"
            style={{
              background: isActive
                ? "var(--cinnabar-light)"
                : "transparent",
              color: isActive ? "var(--cinnabar)" : "var(--text-2)",
            }}
          >
            <span
              className="flex-shrink-0 text-[11px] font-semibold"
              style={{
                fontFamily: "var(--font-display)",
                opacity: isActive ? 1 : 0.5,
              }}
            >
              {num}
            </span>
            <span
              className="text-xs font-medium"
              style={{
                fontFamily: "var(--font-display)",
              }}
            >
              {item.title}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
