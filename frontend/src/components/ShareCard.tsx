"use client";

import { useRef, useState } from "react";
import { WUXING_COLORS, GAN_WUXING } from "@/lib/constants";

interface Props {
  result: Record<string, unknown>;
}

export default function ShareCard({ result }: Props) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [generating, setGenerating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [genError, setGenError] = useState("");

  const validation = result.validation as { day_master?: string; bazi?: string } | undefined;
  const dayMaster = validation?.day_master || "";

  const pattern = result.pattern as { pattern?: string } | undefined;
  const strength = result.strength as { wangshuai?: { verdict?: string } } | undefined;
  const yongshen = result.yongshen as { yongshen?: string; xishen?: string[] } | undefined;

  const shishen = result.shishen as { pillars?: Array<{ gan?: string; zhi?: string }> } | undefined;
  const pillars = shishen?.pillars || [];

  async function handleGenerate() {
    if (!cardRef.current) return;
    setGenerating(true);
    setGenError("");
    try {
      const mod = await import(/* webpackIgnore: true */ "html2pdf.js");
      const html2pdf = mod.default;
      const el = cardRef.current;
      const canvas: HTMLCanvasElement = await html2pdf()
        .set({ html2canvas: { scale: 2, useCORS: true } })
        .from(el)
        .toCanvas();
      const url = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = `八字命格_${dayMaster}日主.png`;
      link.href = url;
      link.click();
    } catch {
      setGenError("图片生成失败，请尝试截图保存");
    }
    setGenerating(false);
  }

  return (
    <>
      <button
        onClick={() => setShowPreview(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] bg-[var(--surface)] text-[var(--text-2)] hover:bg-[var(--surface-2)] transition-colors"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/>
        </svg>
        分享
      </button>

      {showPreview && (
        <div className="fixed inset-0 flex items-center justify-center p-4 bg-black/50" style={{ zIndex: "var(--z-overlay)" }} role="dialog" aria-modal="true" aria-label="分享卡片">
          <div className="w-full max-w-sm rounded-2xl overflow-hidden bg-[var(--surface)] border border-[var(--border)]">
            <div ref={cardRef} className="p-8" style={{ background: "linear-gradient(135deg, #1a1a2e 0%, #2c3e6b 100%)" }}>
              <div className="text-center mb-6">
                <div className="text-[10px] uppercase tracking-[0.2em] mb-2 text-white/50">
                  八字命格
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                  {pillars.map((p, i) => (
                    <div key={i} className="text-center">
                      <div className="text-lg font-bold" style={{ color: WUXING_COLORS[GAN_WUXING[p.gan || ""] || ""] || "#fff" }}>
                        {p.gan}
                      </div>
                      <div className="text-lg font-bold text-[#e8e8f0]">
                        {p.zhi}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-center mb-4">
                <div className="text-xl font-bold mb-1 text-white" style={{ fontFamily: "var(--font-display)" }}>
                  {dayMaster}日主 · {pattern?.pattern || "—"}
                </div>
                <div className="text-sm text-white/70">
                  {strength?.wangshuai?.verdict || ""} · 用神{yongshen?.yongshen || "—"}
                </div>
              </div>

              <div className="text-center pt-4 border-t border-white/10">
                <div className="text-[9px] uppercase tracking-[0.15em] text-white/40">
                  bazi-pro · 确定性命理引擎
                </div>
              </div>
            </div>

            {genError && (
              <div className="px-4 pb-2 text-xs text-[var(--danger)]">{genError}</div>
            )}
            <div className="p-4 flex gap-3">
              <button
                onClick={() => setShowPreview(false)}
                className="flex-1 py-2.5 rounded-lg text-xs font-medium border border-[var(--border)] text-[var(--text-2)] hover:bg-[var(--surface-2)] transition-colors"
              >
                关闭
              </button>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex-1 py-2.5 rounded-lg text-xs font-medium text-white disabled:opacity-50 bg-[var(--scholar-blue)] hover:opacity-90 transition-opacity"
              >
                {generating ? "生成中..." : "保存图片"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
