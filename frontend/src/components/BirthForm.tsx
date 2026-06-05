"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";
import {
  WUXING_COLORS,
  WUXING_BG,
  SCHOOL_OPTIONS,
} from "@/lib/constants";

const CITIES = [
  { name: "北京", lng: 116.40 }, { name: "上海", lng: 121.47 },
  { name: "广州", lng: 113.26 }, { name: "深圳", lng: 114.06 },
  { name: "成都", lng: 104.07 }, { name: "重庆", lng: 106.55 },
  { name: "武汉", lng: 114.30 }, { name: "杭州", lng: 120.15 },
  { name: "南京", lng: 118.78 }, { name: "天津", lng: 117.20 },
  { name: "西安", lng: 108.94 }, { name: "长沙", lng: 112.97 },
  { name: "沈阳", lng: 123.43 }, { name: "哈尔滨", lng: 126.63 },
  { name: "济南", lng: 117.00 }, { name: "青岛", lng: 120.38 },
  { name: "郑州", lng: 113.65 }, { name: "昆明", lng: 102.73 },
  { name: "兰州", lng: 103.83 }, { name: "乌鲁木齐", lng: 87.62 },
  { name: "拉萨", lng: 91.11 }, { name: "台北", lng: 121.56 },
  { name: "香港", lng: 114.17 }, { name: "澳门", lng: 113.55 },
];

export default function BirthForm() {
  const router = useRouter();
  const { submitPaipan, paipanResult, paipanLoading, startAnalysis, status } = useAnalysisStore();

  const [form, setForm] = useState({
    gender: "男",
    solarDate: "",
    solarTime: "",
    school: "ziping",
    city: "",
  });
  const [error, setError] = useState("");
  const [showPaipan, setShowPaipan] = useState(false);

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
      const cityLng = CITIES.find(c => c.name === form.city)?.lng;
      const analysisId = await startAnalysis({
        性别: paipanResult.性别,
        八字: paipanResult.八字,
        日主: paipanResult.日主,
        阳历: solarDatetime,
        生肖: paipanResult.生肖,
        school: form.school,
        ...(cityLng ? { longitude: cityLng } : {}),
      });
      router.push(`/analyze/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    }
  }

  return (
    <div>
      <form onSubmit={handlePaipan} className="space-y-5">
        <div>
          <label
            className="block text-xs font-medium mb-2 uppercase tracking-wider"
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
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  form.gender === g
                    ? ""
                    : "border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]"
                }`}
                style={
                  form.gender === g
                    ? { background: "var(--color-scholar-blue)", color: "#ffffff" }
                    : {}
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
              className="block text-xs font-medium mb-2 uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              出生日期{" "}
              <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              type="date"
              value={form.solarDate}
              placeholder="YYYY-MM-DD"
              autoComplete="bday"
              onChange={(e) => {
                handleChange("solarDate", e.target.value);
                setShowPaipan(false);
              }}
              className="w-full px-4 py-3 rounded-xl text-sm focus:outline-none transition-all duration-200"
              style={{
                background: "var(--bg-secondary)",
                border: "1.5px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 10,
              }}
            />
          </div>
          <div>
            <label
              className="block text-xs font-medium mb-2 uppercase tracking-wider"
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
              className="w-full px-4 py-3 rounded-xl text-sm focus:outline-none transition-all duration-200"
              style={{
                background: "var(--bg-secondary)",
                border: "1.5px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 10,
              }}
            />
          </div>
        </div>

        <div>
          <label
            className="block text-xs font-medium mb-2 uppercase tracking-wider"
            style={{ color: "var(--text-muted)" }}
          >
            出生城市（真太阳时校正）
          </label>
          <select
            value={form.city}
            onChange={(e) => handleChange("city", e.target.value)}
            className="w-full px-4 py-3 rounded-xl text-sm focus:outline-none transition-all duration-200"
            style={{
              background: "var(--bg-secondary)",
              border: "1.5px solid var(--border)",
              color: form.city ? "var(--text-primary)" : "var(--text-muted)",
              borderRadius: 10,
            }}
          >
            <option value="">不校正（默认北京时间）</option>
            {CITIES.map((c) => (
              <option key={c.name} value={c.name}>{c.name} (东经{c.lng.toFixed(1)}°)</option>
            ))}
          </select>
        </div>

        {error && (
          <p className="text-xs mt-1" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
          style={{
            background: "linear-gradient(135deg, var(--color-scholar-blue), #1a2d47)",
            color: "#ffffff",
            boxShadow: "0 4px 16px rgba(44,62,107,0.25)",
            letterSpacing: "0.04em",
          }}
        >
          {paipanLoading ? "排盘中…" : "排盘"}
        </button>
      </form>

      {showPaipan && paipanResult && paipanResult.status === "completed" && (
        <div
          className="mt-7 pt-7 border-t animate-fade-in"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center justify-between mb-5">
            <h3
              className="text-sm font-semibold tracking-wide"
              style={{ color: "var(--text-primary)" }}
            >
              八字命盘
            </h3>
            <span className="text-xs tabular-nums" style={{ color: "var(--text-muted)" }}>
              {paipanResult.生肖} · {paipanResult.日主}日主
            </span>
          </div>

          <div className="overflow-x-auto mb-5">
            <div className="grid grid-cols-4 gap-3">
              {(paipanResult.pillars || []).map((p) => (
                <div
                  key={p.position}
                  className="flex flex-col items-center gap-1 py-4 rounded-xl relative"
                  style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)" }}
                >
                  <span
                    className="text-[11px] font-medium mb-2 px-2 py-0.5 rounded-full"
                    style={{ color: "var(--text-muted)", background: "var(--bg-hover)" }}
                  >
                    {p.position}
                  </span>
                  <span
                    className="text-2xl font-bold leading-none"
                    style={{ color: p.wuxing_gan ? WUXING_COLORS[p.wuxing_gan] : "inherit" }}
                  >
                    {p.gan || "—"}
                  </span>
                  <span
                    className="w-6 my-1.5"
                    style={{ height: "1px", background: "var(--border)" }}
                  />
                  <span
                    className="text-2xl font-bold leading-none"
                    style={{ color: p.wuxing_zhi ? WUXING_COLORS[p.wuxing_zhi] : "inherit" }}
                  >
                    {p.zhi || "—"}
                  </span>
                  <div className="flex gap-1 mt-2">
                    {p.gan && (
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded"
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
                        className="text-[10px] px-1.5 py-0.5 rounded"
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
              ))}
            </div>
          </div>

          <div className="mb-5">
            <label
              className="block text-xs font-medium mb-2.5 uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              选择解读流派
            </label>
            <div className="grid grid-cols-3 gap-2">
              {SCHOOL_OPTIONS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => handleChange("school", s.value)}
                  className={`p-3 rounded-xl text-left transition-all duration-200 ${
                    form.school === s.value
                      ? ""
                      : "border border-[var(--border)] hover:border-[var(--text-muted)]"
                  }`}
                  style={
                    form.school === s.value
                      ? {
                          borderColor: "var(--water)",
                          borderWidth: "2px",
                          background: "rgba(96,165,250,0.06)",
                        }
                      : { background: "var(--bg-secondary)" }
                  }
                >
                  <div
                    className="text-xs font-semibold"
                    style={{
                      color:
                        form.school === s.value
                          ? "var(--water)"
                          : "var(--text-primary)",
                    }}
                  >
                    {s.label}
                  </div>
                  <div
                    className="text-[11px] mt-0.5"
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
            className="w-full py-3.5 rounded-xl font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] flex items-center justify-center gap-2"
            style={{
              background: "var(--text-primary)",
              color: "var(--bg-primary)",
              boxShadow: "0 6px 20px rgba(0,0,0,0.3)",
            }}
          >
            {status === "submitting" ? "提交中…" : "深度解读"}{" "}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>

          <p
            className="text-center text-[11px] mt-3"
            style={{ color: "var(--text-muted)", opacity: 0.6 }}
          >
            旺衰判定 · 格局筛查 · 喜用神推导 · 古籍引证
          </p>
        </div>
      )}
    </div>
  );
}