"use client";

import { useState, useRef, useCallback } from "react";

interface Props {
  analysisId: string;
  result: Record<string, unknown> | undefined;
  narration?: Record<string, unknown>;
}

const SECTION_TITLES: Record<string, string> = {
  overview: "命盘综述",
  strength: "旺衰分析",
  pattern: "格局判定",
  yongshen: "喜用神",
  tiaohou: "调候分析",
  elements: "五行力量",
  relations: "刑冲合害",
  personality: "性情推断",
  career: "事业方向",
};

export default function ExportPanel({ analysisId, result, narration }: Props) {
  const [showMenu, setShowMenu] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [copied, setCopied] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const buildReportContent = useCallback(() => {
    if (!result) return "";

    const validation = result.validation as { day_master?: string; bazi?: string; gender?: string; zodiac?: string } | undefined;
    const dayMaster = validation?.day_master || "";
    const bazi = validation?.bazi || "";
    const gender = validation?.gender || "";
    const zodiac = validation?.zodiac || "";

    const shishen = result.shishen as { pillars?: Array<{ position?: string; gan?: string; zhi?: string; shishen_gan?: string; shishen_zhi?: string; canggan?: Array<{ gan?: string }> }> } | undefined;
    const pillars = shishen?.pillars || [];

    const strength = result.strength as { wangshuai?: { verdict?: string; is_weak?: boolean; is_strong?: boolean }; deling?: { status?: string; score?: number }; dedi?: { score?: number }; deshi?: { score?: number } } | undefined;
    const wangshuai = strength?.wangshuai;

    const pattern = result.pattern as { pattern?: string; confidence?: number; reason?: string } | undefined;

    const yongshen = result.yongshen as { yongshen?: string; xishen?: string[]; jishen?: string[]; trace?: { method?: string; reason?: string } } | undefined;

    const elements = result.elements as { percent?: Record<string, number> } | undefined;
    const percent = elements?.percent || {};
    const wuxingOrder = ["木", "火", "土", "金", "水"];

    const tiaohou = result.tiaohou as { has_tiaohou?: boolean; tiaohou_gan?: string[] } | undefined;

    const relations = result.relations as Array<{ type?: string; description?: string }> | undefined;

    let text = `# 八字分析报告\n\n`;
    text += `**八字**: ${bazi}  \n`;
    text += `**日主**: ${dayMaster}  \n`;
    text += `**性别**: ${gender}  \n`;
    text += `**生肖**: ${zodiac}\n\n`;

    text += `## 四柱命盘\n\n`;
    text += `| | 年柱 | 月柱 | 日柱 | 时柱 |\n|---|------|------|------|------|\n`;
    text += `| 十神 | ${pillars[0]?.shishen_gan || "—"} | ${pillars[1]?.shishen_gan || "—"} | 日主 | ${pillars[3]?.shishen_gan || "—"} |\n`;
    text += `| 天干 | ${pillars[0]?.gan || "—"} | ${pillars[1]?.gan || "—"} | ${pillars[2]?.gan || "—"} | ${pillars[3]?.gan || "—"} |\n`;
    text += `| 地支 | ${pillars[0]?.zhi || "—"} | ${pillars[1]?.zhi || "—"} | ${pillars[2]?.zhi || "—"} | ${pillars[3]?.zhi || "—"} |\n`;
    text += `| 十神 | ${pillars[0]?.shishen_zhi || "—"} | ${pillars[1]?.shishen_zhi || "—"} | — | ${pillars[3]?.shishen_zhi || "—"} |\n\n`;

    text += `## 摘要\n\n`;
    text += `- **旺衰**: ${wangshuai?.verdict || "—"}\n`;
    text += `- **格局**: ${pattern?.pattern || "—"}\n`;
    text += `- **用神**: ${yongshen?.yongshen || "—"}\n\n`;

    text += `## 五行力量\n\n`;
    wuxingOrder.forEach((wx) => {
      const val = percent[wx] || 0;
      const bar = "█".repeat(Math.round(val / 5)) + "░".repeat(20 - Math.round(val / 5));
      text += `- **${wx}** ${val.toFixed(1)}% ${bar}\n`;
    });
    text += `\n`;

    text += `## 喜忌用神\n\n`;
    text += `- **用神**: ${yongshen?.yongshen || "—"}\n`;
    text += `- **喜神**: ${(yongshen?.xishen || []).join(" ") || "—"}\n`;
    text += `- **忌神**: ${(yongshen?.jishen || []).join(" ") || "—"}\n`;
    if (tiaohou?.has_tiaohou) {
      text += `- **调候**: ${(tiaohou.tiaohou_gan || []).join(" ")}\n`;
    }
    text += `\n`;

    if (relations && relations.length > 0) {
      text += `## 刑冲合害\n\n`;
      relations.forEach((r) => {
        text += `- **${r.type || ""}**: ${r.description || ""}\n`;
      });
      text += `\n`;
    }

    if (pattern?.reason) {
      text += `## 格局判定依据\n\n${pattern.reason}\n\n`;
    }

    if (narration && typeof narration === "object") {
      text += `## 详细解读\n\n`;
      for (const [key, value] of Object.entries(narration)) {
        const title = SECTION_TITLES[key] || key;
        if (typeof value === "string" && value.trim()) {
          text += `### ${title}\n\n${value}\n\n`;
        }
      }
    }

    return text;
  }, [result, narration]);

  async function handleExportPDF() {
    setExporting(true);
    setShowMenu(false);

    try {
      const innerEl = document.querySelector("main > div") as HTMLElement;
      if (!innerEl) return;

      const chatEl = innerEl.querySelector("[class*='ChatPanel'], [class*='chat-panel']") as HTMLElement;
      if (chatEl) chatEl.classList.add("no-print");

      const header = document.createElement("div");
      header.className = "print-header";
      header.innerHTML = `<div style="text-align:center;margin-bottom:20px;border-bottom:2px solid #6366f1;padding-bottom:16px;page-break-after:avoid;"><h1 style="font-size:24px;font-weight:700;color:#4f46e5;margin:0 0 8px;">八字分析报告</h1><p style="font-size:12px;color:#999;margin:0;">分析编号：${analysisId}</p></div>`;
      innerEl.insertBefore(header, innerEl.firstChild);

      document.querySelectorAll(".no-print-temp").forEach((el) => el.classList.remove("no-print-temp"));
      const sidebar = document.querySelector("[class*='HistorySidebar'], [class*='history-sidebar']");
      if (sidebar) sidebar.classList.add("no-print-temp");
      const toggleBtns = innerEl.querySelectorAll("button");
      toggleBtns.forEach((btn) => { if (!btn.closest(".no-print")) btn.classList.add("no-print-temp"); });

      await new Promise((r) => setTimeout(r, 200));
      window.print();

      setTimeout(() => {
        header.remove();
        if (chatEl) chatEl.classList.remove("no-print");
        document.querySelectorAll(".no-print-temp").forEach((el) => el.classList.remove("no-print-temp"));
        setExporting(false);
      }, 1000);
    } catch (err) {
      console.error("PDF export failed:", err);
      setExporting(false);
    }
  }

  async function handleCopyText() {
    const content = buildReportContent();
    if (!content) return;

    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setShowMenu(false);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = content;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setShowMenu(false);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={exporting}
        className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:shadow-sm disabled:opacity-50"
        style={{
          border: "1px solid var(--accent)",
          color: "var(--accent)",
          background: "transparent",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "var(--accent-dim)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "transparent";
        }}
      >
        {exporting ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.25" />
              <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <span>导出中...</span>
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>{copied ? "已复制" : "导出报告"}</span>
          </>
        )}
      </button>

      {showMenu && (
        <div
          className="absolute right-0 mt-2 w-44 rounded-xl shadow-lg overflow-hidden z-50 animate-fade-in"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
          }}
        >
          <button
            onClick={handleExportPDF}
            disabled={exporting}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-sm transition-colors"
            style={{ color: "var(--text-secondary)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--bg-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            导出为 PDF
          </button>
          <button
            onClick={handleCopyText}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-sm transition-colors"
            style={{ color: "var(--text-secondary)", borderTop: "1px solid var(--border)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--bg-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
            </svg>
            复制报告文本
          </button>
        </div>
      )}

      {showMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  );
}
