"use client";

import { type ReactNode } from "react";
import ShareCard from "@/components/ShareCard";
import dynamic from "next/dynamic";

const ExportPanel = dynamic(() => import("@/components/ExportPanel"), { ssr: false });

import type { BirthInput } from "@/lib/api";

interface ActionBarProps {
  analysisId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any;
  narration?: Record<string, unknown>;
  currentSchool: string;
  selectedSchool: string;
  setSelectedSchool: (s: string) => void;
  schoolDropdownOpen: boolean;
  setSchoolDropdownOpen: (open: boolean) => void;
  isLoading: boolean;
  birthInput: BirthInput | null;
  onReanalyze: () => void;
  onGenerateReport: () => void;
  schoolOptions: { value: string; label: string; desc: string }[];
}

export default function ActionBar({
  analysisId, result, narration, currentSchool, selectedSchool, setSelectedSchool,
  schoolDropdownOpen, setSchoolDropdownOpen, isLoading, birthInput, onReanalyze,
  onGenerateReport, schoolOptions,
}: ActionBarProps) {
  return (
    <div data-action-bar className="flex items-center gap-1.5 sm:gap-2.5 mb-5 sm:mb-7 flex-wrap">
      <div className="relative">
        <button onClick={(e) => { e.stopPropagation(); setSchoolDropdownOpen(!schoolDropdownOpen); }}
          aria-expanded={schoolDropdownOpen} aria-haspopup="true"
          className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-[12px] sm:text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
          style={{ color: "var(--text-2)", background: "var(--surface)" }}>
          {schoolOptions.find(s => s.value === currentSchool)?.label || "传统子平"}
          <svg aria-hidden="true" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"
            style={{ transform: schoolDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        {schoolDropdownOpen && (
          <div role="menu" className="card absolute left-0 top-full mt-1.5 w-60 overflow-hidden" style={{ zIndex: "var(--z-dropdown)" }}>
            {schoolOptions.map((s) => (
              <button key={s.value} role="menuitem" onClick={() => { setSelectedSchool(s.value); setSchoolDropdownOpen(false); }}
                className="w-full px-5 py-2.5 text-left transition-colors hover:bg-[var(--surface-2)]"
                style={{ fontSize: 13, background: selectedSchool === s.value ? "var(--cinnabar-light)" : "transparent" }}>
                <div className="font-medium" style={{ color: selectedSchool === s.value ? "var(--wx-water)" : "var(--ink)" }}>{s.label}</div>
                <div style={{ fontSize: 11, color: "var(--text-4)" }}>{s.desc}</div>
              </button>
            ))}
            <div style={{ borderTop: "1px solid var(--border)" }}>
              <button onClick={() => { setSchoolDropdownOpen(false); onReanalyze(); }} role="menuitem" disabled={!birthInput || isLoading}
                className="w-full px-5 py-2.5 font-medium disabled:opacity-50 transition-colors hover:bg-[var(--surface-2)]"
                style={{ fontSize: 13, color: "var(--wx-water)" }}>
                以「{schoolOptions.find(s => s.value === selectedSchool)?.label}」重新分析
              </button>
            </div>
          </div>
        )}
      </div>
      <button onClick={onGenerateReport} className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-[12px] sm:text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
        style={{ color: "var(--text-2)", background: "var(--surface)" }}>
        <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        详批报告
      </button>
      <ExportPanel analysisId={analysisId} result={result} narration={narration} />
      <ShareCard result={result} />
    </div>
  );
}
