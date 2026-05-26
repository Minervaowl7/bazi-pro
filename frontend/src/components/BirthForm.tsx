"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";
import type { BirthInput } from "@/lib/api";

const TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];

export default function BirthForm() {
  const router = useRouter();
  const { startAnalysis, status } = useAnalysisStore();

  const [form, setForm] = useState({
    gender: "男",
    bazi: "",
    dayMaster: "",
    solarDate: "",
    solarTime: "",
  });
  const [error, setError] = useState("");

  const isSubmitting = status === "submitting";

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError("");
  }

  function inferDayMaster(bazi: string): string {
    const parts = bazi.trim().split(/\s+/);
    if (parts.length >= 3 && parts[2].length >= 1) {
      return parts[2][0];
    }
    return "";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const bazi = form.bazi.trim();
    if (!bazi) {
      setError("请输入八字");
      return;
    }

    const parts = bazi.split(/\s+/);
    if (parts.length !== 4) {
      setError("八字格式错误，请输入四柱（空格分隔），如：壬午 乙巳 丁亥 癸卯");
      return;
    }

    const dayMaster = form.dayMaster || inferDayMaster(bazi);
    if (!dayMaster || !TIANGAN.includes(dayMaster)) {
      setError("日主不合法，请检查八字第三柱天干");
      return;
    }

    const solarDatetime = form.solarDate
      ? `${form.solarDate} ${form.solarTime || "00:00"}`
      : "";

    const input: BirthInput = {
      性别: form.gender,
      八字: bazi,
      日主: dayMaster,
      阳历: solarDatetime,
    };

    try {
      const analysisId = await startAnalysis(input);
      router.push(`/analyze/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1.5">
          性别
        </label>
        <div className="flex gap-3">
          {["男", "女"].map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => handleChange("gender", g)}
              className={`px-5 py-2 rounded-lg text-sm transition-colors ${
                form.gender === g
                  ? "bg-[var(--accent)] text-[var(--bg-primary)] font-medium"
                  : "bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:bg-[var(--border)]"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1.5">
          八字（四柱，空格分隔）
        </label>
        <input
          type="text"
          value={form.bazi}
          onChange={(e) => {
            handleChange("bazi", e.target.value);
            const dm = inferDayMaster(e.target.value);
            if (dm) handleChange("dayMaster", dm);
          }}
          placeholder="壬午 乙巳 丁亥 癸卯"
          className="w-full px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] transition-colors font-mono"
        />
      </div>

      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1.5">
          日主（自动推导）
        </label>
        <input
          type="text"
          value={form.dayMaster}
          onChange={(e) => handleChange("dayMaster", e.target.value)}
          placeholder="自动从八字第三柱推导"
          className="w-full px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] transition-colors"
          maxLength={1}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm text-[var(--text-secondary)] mb-1.5">
            阳历日期（可选）
          </label>
          <input
            type="date"
            value={form.solarDate}
            onChange={(e) => handleChange("solarDate", e.target.value)}
            className="w-full px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
          />
        </div>
        <div>
          <label className="block text-sm text-[var(--text-secondary)] mb-1.5">
            出生时间（可选）
          </label>
          <input
            type="time"
            value={form.solarTime}
            onChange={(e) => handleChange("solarTime", e.target.value)}
            className="w-full px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
          />
        </div>
      </div>

      {error && (
        <p className="text-sm text-[var(--danger)]">{error}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? "正在提交..." : "开始分析"}
      </button>
    </form>
  );
}