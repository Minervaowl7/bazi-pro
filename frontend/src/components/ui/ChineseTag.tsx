"use client";

import { ReactNode } from "react";

type WuxingTagType = "wood" | "fire" | "earth" | "metal" | "water";

export type ChineseTagType =
  | "tiangan"
  | "dizhi"
  | "shishen"
  | WuxingTagType;

interface ChineseTagProps {
  type: ChineseTagType;
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const WUXING_STYLES: Record<WuxingTagType, { color: string; bg: string }> = {
  wood: { color: "var(--wood)", bg: "var(--wood-dim)" },
  fire: { color: "var(--fire)", bg: "var(--fire-dim)" },
  earth: { color: "var(--earth)", bg: "var(--earth-dim)" },
  metal: { color: "var(--metal)", bg: "var(--metal-dim)" },
  water: { color: "var(--water)", bg: "var(--water-dim)" },
};

export function ChineseTag({ type, children, className, style }: ChineseTagProps) {
  const base: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    lineHeight: 1,
  };

  let variant: React.CSSProperties;

  switch (type) {
    case "tiangan":
      variant = { padding: "8px 12px", borderRadius: 12, fontWeight: 700 };
      break;
    case "dizhi":
      variant = { padding: "8px 12px", borderRadius: 12, fontWeight: 700 };
      break;
    case "shishen":
      variant = {
        padding: "2px 8px",
        borderRadius: 6,
        fontSize: "0.75rem",
        fontWeight: 600,
        background: "var(--accent-dim)",
        color: "var(--accent)",
        border: "1px solid var(--gold-dim)",
      };
      break;
    default: {
      const w = WUXING_STYLES[type as WuxingTagType];
      variant = {
        padding: "2px 6px",
        borderRadius: 6,
        fontSize: "0.75rem",
        fontWeight: 600,
        color: w.color,
        background: w.bg,
      };
      break;
    }
  }

  return (
    <span className={className} style={{ ...base, ...variant, ...style }}>
      {children}
    </span>
  );
}
