"use client";

import { type ReactNode } from "react";
import { Accordion, AccordionItem } from "@/components/ui/Accordion";

export interface MobileSection {
  title: string;
  defaultOpen?: boolean;
  content: ReactNode;
}

interface ResponsiveTabPanelProps {
  /** 桌面端内容（hidden on mobile） */
  desktop: ReactNode;
  /** 移动端 Accordion 分段 */
  mobileSections: MobileSection[];
  /** 可选 className 附加到桌面容器 */
  desktopClassName?: string;
}

/**
 * 统一桌面/移动端面板布局。
 * - 桌面端：`hidden sm:block` 直接渲染
 * - 移动端：`sm:hidden` Accordion 可折叠
 */
export default function ResponsiveTabPanel({
  desktop,
  mobileSections,
  desktopClassName,
}: ResponsiveTabPanelProps) {
  return (
    <>
      <div className={`hidden sm:block ${desktopClassName ?? ""}`}>{desktop}</div>
      <div className="sm:hidden">
        <Accordion>
          {mobileSections.map((s) => (
            <AccordionItem key={s.title} title={s.title} defaultOpen={s.defaultOpen}>
              {s.content}
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </>
  );
}
