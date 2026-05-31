"use client";

import { useState, useEffect } from "react";
import { useAnalysisStore } from "@/stores/analysisStore";
import { submitAnalysis } from "@/lib/api";
import {
  WUXING_COLORS,
  WUXING_BG,
  SCHOOL_OPTIONS,
} from "@/lib/constants";

export default function BirthForm() {
  const { submitPaipan, paipanResult, paipanLoading, startAnalysis, status } = useAnalysisStore();

  const [form, setForm] = useState({
    gender: "男",
    solarDate: "",
    solarTime: "",
    school: "ziping",
  });
  const [error, setError] = useState("");
  const [showPaipan, setShowPaipan] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  const isSubmitting = status === "submitting" || paipanLoading;

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError("");
  }

  async function handlePaipan(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!form.solarDate) {
      setError("请选择出生日期");
      return;
    }

    const solarDatetime = form.solarTime
      ? `${form.solarDate} ${form.solarTime}`
      : form.solarDate;

    try {
      await submitPaipan({
        性别: form.gender,
        阳历: solarDatetime,
      });
      setShowPaipan(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "排盘失败");
    }
  }

  async function handleDeepAnalysis() {
    if (!paipanResult || paipanResult.status !== "completed") return;

    const solarDatetime = form.solarTime
      ? `${form.solarDate} ${form.solarTime}`
      : form.solarDate;

    try {
      const resp = await submitAnalysis({
        性别: paipanResult.性别,
        八字: paipanResult.八字,
        日主: paipanResult.日主,
        阳历: solarDatetime,
        生肖: paipanResult.生肖,
        school: form.school,
      });
      window.location.href = `/analyze/${resp.analysis_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    }
  }

  return (
    <div>
      {!hydrated && (
        <div
          className="mb-4 px-4 py-3 rounded-xl text-sm"
          style={{ background: "var(--warning-dim)", color: "var(--gold-text)" }}
        >
          页面加载中，请稍候...
        </div>
      )}

      <form onSubmit={handlePaipan} className="space-y-5">
        <div>
          <label
            className="block text-[11px] font-semibold mb-2.5 tracking-[0.1em]"
            style={{ color: "var(--text-muted)" }}
          >
            性别
          </label>
          <div className="flex gap-2">
            {["男", "女"].map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => handleChange("gender", g)}
                className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                style={
                  form.gender === g
                    ? {
                        background: "var(--accent)",
                        color: "#FFFFFF",
                        boxShadow: "0 2px 8px rgba(138,59,42,0.2)",
                      }
                    : {
                        background: "var(--bg-hover)",
                        border: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                      }
                }
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label
              className="block text-[11px] font-semibold mb-2.5 tracking-[0.1em]"
              style={{ color: "var(--text-muted)" }}
            >
              出生日期 <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              type="date"
              value={form.solarDate}
              placeholder="YYYY-MM-DD"
              onChange={(e) => {
                handleChange("solarDate", e.target.value);
                setShowPaipan(false);
              }}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200"
              style={{
                background: "var(--bg-hover)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
          <div>
            <label
              className="block text-[11px] font-semibold mb-2.5 tracking-[0.1em]"
              style={{ color: "var(--text-muted)" }}
            >
              出生时间
            </label>
            <input
              type="time"
              value={form.solarTime}
              placeholder="HH:MM"
              onChange={(e) => {
                handleChange("solarTime", e.target.value);
                setShowPaipan(false);
              }}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200"
              style={{
                background: "var(--bg-hover)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
        </div>

        {error && (
          <div
            className="px-4 py-3 rounded-xl text-sm font-medium"
            style={{ background: "var(--danger-dim)", color: "var(--danger)" }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
          style={{
            background: "var(--accent)",
            color: "#FFFFFF",
            boxShadow: "0 2px 12px rgba(138,59,42,0.2)",
          }}
        >
          {paipanLoading ? "排盘中..." : "排盘"}
        </button>
      </form>

      {showPaipan && paipanResult && paipanResult.status === "completed" && (
        <div
          className="mt-8 pt-8 animate-fade-in"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <div className="flex items-center justify-between mb-6">
            <h3
              className="text-sm font-bold tracking-[0.06em]"
              style={{ color: "var(--text-primary)" }}
            >
              八字命盘
            </h3>
            <span
              className="text-xs px-2.5 py-1 rounded-lg"
              style={{ color: "var(--accent)", background: "var(--accent-dim)" }}
            >
              {paipanResult.生肖} · {paipanResult.日主}日主
            </span>
          </div>

          <div className="overflow-x-auto mb-6">
            <div className="grid grid-cols-4 gap-2.5">
              {paipanResult.pillars.map((p: { position: string; gan: string; zhi: string; wuxing_gan: string; wuxing_zhi: string }, idx: number) => {
                const isDay = idx === 2;
                return (
                  <div
                    key={p.position}
                    className="flex flex-col items-center gap-1 py-5 rounded-xl relative"
                    style={{
                      background: isDay ? "var(--accent-dim)" : "var(--bg-hover)",
                      border: isDay ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                    }}
                  >
                    {isDay && (
                      <span
                        className="absolute -top-2 left-1/2 -translate-x-1/2 text-[9px] font-bold px-2 py-0.5 rounded-full"
                        style={{ background: "var(--accent)", color: "#FFFFFF" }}
                      >
                        日主
                      </span>
                    )}
                    <span
                      className="text-[10px] font-semibold mb-2 tracking-wider"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {p.position}
                    </span>
                    <span
                      className="text-[22px] font-bold leading-none"
                      style={{ color: p.wuxing_gan ? WUXING_COLORS[p.wuxing_gan] : "inherit" }}
                    >
                      {p.gan || "—"}
                    </span>
                    <span
                      className="w-5 my-2"
                      style={{ height: "1px", background: isDay ? "var(--accent)" : "var(--border)" }}
                    />
                    <span
                      className="text-[22px] font-bold leading-none"
                      style={{ color: p.wuxing_zhi ? WUXING_COLORS[p.wuxing_zhi] : "inherit" }}
                    >
                      {p.zhi || "—"}
                    </span>
                    <div className="flex gap-1 mt-2">
                      {p.gan && (
                        <span
                          className="text-[9px] px-1.5 py-0.5 rounded-md font-medium"
                          style={{
                            color: WUXING_COLORS[p.wuxing_gan] || "inherit",
                            background: WUXING_BG[p.wuxing_gan] || "transparent",
                          }}
                        >
                          {p.wuxing_gan}
                        </span>
                      )}
                      {p.zhi && (
                        <span
                          className="text-[9px] px-1.5 py-0.5 rounded-md font-medium"
                          style={{
                            color: WUXING_COLORS[p.wuxing_zhi] || "inherit",
                            background: WUXING_BG[p.wuxing_zhi] || "transparent",
                          }}
                        >
                          {p.wuxing_zhi}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mb-6">
            <label
              className="block text-[11px] font-semibold mb-2.5 tracking-[0.1em]"
              style={{ color: "var(--text-muted)" }}
            >
              解读流派
            </label>
            <div className="grid grid-cols-3 gap-2">
              {SCHOOL_OPTIONS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => handleChange("school", s.value)}
                  className="p-3 rounded-xl text-left transition-all duration-200"
                  style={
                    form.school === s.value
                      ? {
                          borderColor: "var(--accent)",
                          borderWidth: "1.5px",
                          background: "var(--accent-dim)",
                          borderStyle: "solid",
                        }
                      : {
                          background: "var(--bg-hover)",
                          border: "1px solid var(--border)",
                        }
                  }
                >
                  <div
                    className="text-xs font-bold"
                    style={{
                      color:
                        form.school === s.value
                          ? "var(--accent)"
                          : "var(--text-primary)",
                    }}
                  >
                    {s.label}
                  </div>
                  <div
                    className="text-[10px] mt-1 leading-snug"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {s.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={handleDeepAnalysis}
            disabled={status === "submitting" || status === "streaming"}
            className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] flex items-center justify-center gap-2"
            style={{
              background: "var(--accent)",
              color: "#FFFFFF",
              boxShadow: "0 4px 16px rgba(138,59,42,0.25)",
            }}
          >
            {status === "submitting" ? "提交中..." : "深度解读"}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
        </div>
      )}
    </div>
  );
}
