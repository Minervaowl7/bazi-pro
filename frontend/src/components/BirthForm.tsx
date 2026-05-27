"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";

const WUXING_COLORS: Record<string, string> = {
  木: "var(--wood)",
  火: "var(--fire)",
  土: "var(--earth)",
  金: "var(--metal)",
  水: "var(--water)",
};

const WUXING_BG: Record<string, string> = {
  木: "rgba(34,197,94,0.12)",
  火: "rgba(239,68,68,0.12)",
  土: "rgba(234,179,8,0.12)",
  金: "rgba(245,158,11,0.12)",
  水: "rgba(59,130,246,0.12)",
};

const SCHOOL_OPTIONS = [
  { value: "ziping", label: "子平真诠", desc: "格局用神 · 正统子平" },
  { value: "qiongtong", label: "穷通宝鉴", desc: "调候为先 · 月令调候" },
  { value: "zitong", label: "滴天髓", desc: "旺衰扶抑 · 阴阳流通" },
];

export default function BirthForm() {
  const router = useRouter();
  const { submitPaipan, paipanResult, paipanLoading, startAnalysis, status } = useAnalysisStore();

  const [form, setForm] = useState({
    gender: "男",
    solarDate: "",
    solarTime: "",
    school: "ziping",
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
      const analysisId = await startAnalysis({
        性别: paipanResult.性别,
        八字: paipanResult.八字,
        日主: paipanResult.日主,
        阳历: solarDatetime,
        生肖: paipanResult.生肖,
        school: form.school,
      });
      router.push(`/analyze/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    }
  }

  return (
    <div>
      <form onSubmit={handlePaipan} className="space-y-6">
        <div>
          <label
            className="block text-sm font-medium mb-2"
            style={{ color: "var(--text-secondary)" }}
          >
            性别
          </label>
          <div className="flex gap-3">
            {["男", "女"].map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => handleChange("gender", g)}
                className={`flex-1 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  form.gender === g
                    ? ""
                    : "border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]"
                }`}
                style={
                  form.gender === g
                    ? { background: "var(--accent)", color: "var(--bg-primary)" }
                    : {}
                }
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              出生日期{" "}
              <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              type="date"
              value={form.solarDate}
              onChange={(e) => {
                handleChange("solarDate", e.target.value);
                setShowPaipan(false);
              }}
              className="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 transition-all duration-200"
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              出生时间
            </label>
            <input
              type="time"
              value={form.solarTime}
              onChange={(e) => {
                handleChange("solarTime", e.target.value);
                setShowPaipan(false);
              }}
              className="w-full px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 transition-all duration-200"
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
        </div>

        {error && (
          <p className="text-xs mt-1" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-xl font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110"
          style={{
            background: "var(--accent)",
            color: "var(--bg-primary)",
          }}
        >
          {paipanLoading ? "排盘中..." : "排盘"}
        </button>
      </form>

      {showPaipan && paipanResult && paipanResult.status === "completed" && (
        <div
          className="mt-8 pt-8 border-t animate-fade-in"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center justify-between mb-6">
            <h3
              className="text-base font-semibold"
              style={{ color: "var(--accent)" }}
            >
              八字命盘
            </h3>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              {paipanResult.生肖} · {paipanResult.日主}日主
            </span>
          </div>

          <div className="overflow-x-auto mb-6">
            <table className="w-full text-center">
              <thead>
                <tr
                  className="text-xs uppercase tracking-wider"
                  style={{ color: "var(--text-muted)", background: "var(--bg-secondary)" }}
                >
                  <th className="py-2.5 px-3 w-14"></th>
                  {paipanResult.pillars.map((p) => (
                    <th key={p.position} className="py-2.5 px-3 font-medium">
                      {p.position}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-3 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    天干
                  </td>
                  {paipanResult.pillars.map((p) => (
                    <td key={p.position} className="py-3 px-2">
                      {p.gan ? (
                        <span
                          className="text-2xl font-bold"
                          style={{
                            color: p.wuxing_gan
                              ? WUXING_COLORS[p.wuxing_gan]
                              : "inherit",
                          }}
                        >
                          {p.gan}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr style={{ borderTop: "1px solid var(--border)" }}>
                  <td
                    className="py-3 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    地支
                  </td>
                  {paipanResult.pillars.map((p) => (
                    <td key={p.position} className="py-3 px-2">
                      {p.zhi ? (
                        <span
                          className="text-2xl font-bold"
                          style={{
                            color: p.wuxing_zhi
                              ? WUXING_COLORS[p.wuxing_zhi]
                              : "inherit",
                          }}
                        >
                          {p.zhi}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr style={{ borderTop: "1px solid var(--border)", background: "var(--bg-secondary)" }}>
                  <td
                    className="py-2.5 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    五行
                  </td>
                  {paipanResult.pillars.map((p) => (
                    <td key={p.position} className="py-2.5 px-2">
                      <div className="flex flex-col items-center gap-1">
                        {p.gan && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-md"
                            style={{
                              color: WUXING_COLORS[p.wuxing_gan] || "inherit",
                              background:
                                WUXING_BG[p.wuxing_gan] || "transparent",
                            }}
                          >
                            {p.wuxing_gan}
                          </span>
                        )}
                        {p.zhi && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-md"
                            style={{
                              color: WUXING_COLORS[p.wuxing_zhi] || "inherit",
                              background:
                                WUXING_BG[p.wuxing_zhi] || "transparent",
                            }}
                          >
                            {p.wuxing_zhi}
                          </span>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mb-6">
            <label
              className="block text-sm font-medium mb-3"
              style={{ color: "var(--text-secondary)" }}
            >
              选择解读流派
            </label>
            <div className="grid grid-cols-3 gap-3">
              {SCHOOL_OPTIONS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => handleChange("school", s.value)}
                  className={`p-4 rounded-xl text-left transition-all duration-200 ${
                    form.school === s.value
                      ? ""
                      : "border border-[var(--border)] hover:border-[var(--text-muted)]"
                  }`}
                  style={
                    form.school === s.value
                      ? {
                          borderColor: "var(--accent)",
                          borderWidth: "2px",
                          background: "var(--accent-dim)",
                        }
                      : { background: "var(--bg-secondary)" }
                  }
                >
                  <div
                    className="text-sm font-medium"
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
                    className="text-xs mt-1"
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
            className="w-full py-3.5 rounded-xl font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110 flex items-center justify-center gap-2"
            style={{
              background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
              color: "var(--bg-primary)",
            }}
          >
            {status === "submitting" ? "提交中..." : "深度解读"}{" "}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>

          <p
            className="text-center text-xs mt-4"
            style={{ color: "var(--text-muted)" }}
          >
            旺衰判定 · 格局筛查 · 喜用神推导 · 古籍引证
          </p>
        </div>
      )}
    </div>
  );
}
