"use client";

import { type ReactNode, useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";

interface SectionProps {
  children: ReactNode;
  /** 层级：hero=首屏大卡, primary=主内容, secondary=次级, tertiary=技术细节 */
  level?: "hero" | "primary" | "secondary" | "tertiary";
  /** 标题 */
  title?: string;
  /** 标题右侧的额外内容 */
  titleExtra?: ReactNode;
  /** 自定义类名 */
  className?: string;
  /** 是否启用入场动画 */
  animate?: boolean;
  /** 折叠状态（用于 accordion） */
  collapsible?: boolean;
  defaultOpen?: boolean;
}

const levelStyles: Record<string, React.CSSProperties> = {
  hero: {
    background: "var(--surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-lg)",
    boxShadow: "var(--shadow-lg)",
    padding: "40px 48px",
  },
  primary: {
    background: "var(--surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-md)",
    padding: "32px 36px",
  },
  secondary: {
    background: "var(--surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-sm)",
    padding: "24px 28px",
  },
  tertiary: {
    background: "var(--surface-warm)",
    border: "1px solid var(--color-border-subtle)",
    borderRadius: "var(--radius-sm)",
    boxShadow: "var(--shadow-xs)",
    padding: "20px 24px",
  },
};

export default function Section({
  children,
  level = "primary",
  title,
  titleExtra,
  className = "",
  animate = true,
  collapsible = false,
  defaultOpen = true,
}: SectionProps) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!animate || !ref.current) return;
    gsap.from(ref.current, {
      autoAlpha: 0,
      y: 20,
      duration: 0.5,
      ease: "power2.out",
      scrollTrigger: {
        trigger: ref.current,
        start: "top 92%",
        once: true,
      },
    });
  }, { scope: ref });

  const style = levelStyles[level] || levelStyles.primary;

  return (
    <section
      ref={ref}
      className={`mb-6 ${className}`}
      style={style}
    >
      {title && (
        <div
          className="flex items-center justify-between mb-4"
          style={{
            borderBottom: "1px solid var(--color-border-subtle)",
            paddingBottom: "12px",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: level === "hero" ? 22 : 18,
              fontWeight: 700,
              color: "var(--color-text-primary)",
              letterSpacing: "-0.01em",
              lineHeight: 1.3,
            }}
          >
            {title}
          </h2>
          {titleExtra}
        </div>
      )}
      {children}
    </section>
  );
}
