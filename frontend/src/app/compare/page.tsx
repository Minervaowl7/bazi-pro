"use client";

import { useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

interface HehunResult {
  compatibility_score: number;
  compatibility_note: string;
  pillar_diff: Array<{ position?: string; diff?: string }>;
  wuxing_overlap: Record<string, unknown>;
  yongshen_diff: Record<string, unknown>;
  relation_analysis: Array<{ type?: string; description?: string }>;
}

export default function ComparePage() {
  const [formA, setFormA] = useState({ bazi: "", dayMaster: "", gender: "男" });
  const [formB, setFormB] = useState({ bazi: "", dayMaster: "", gender: "女" });
  const [result, setResult] = useState<HehunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formA.bazi || !formA.dayMaster || !formB.bazi || !formB.dayMaster) {
      setError("请填写双方的八字和日主");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/v2/hehun`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          "八字A": formA.bazi, "日主A": formA.dayMaster, "性别A": formA.gender,
          "八字B": formB.bazi, "日主B": formB.dayMaster, "性别B": formB.gender,
        }),
      });
      const data = await res.json();
      if (data.status === "completed") {
        setResult(data.result);
      } else {
        setError(data.error?.message || "分析失败");
      }
    } catch {
      setError("无法连接服务器");
    }
    setLoading(false);
  }

  const scoreColor = result
    ? result.compatibility_score >= 80 ? "var(--success)"
      : result.compatibility_score >= 60 ? "var(--warning)"
        : "var(--danger)"
    : "var(--color-text-primary)";

  return (
    <div className="min-h-screen" style={{ background: "var(--background)" }}>
      <div className="w-full px-6 md:px-12 lg:px-16 xl:px-24 py-8">
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            ← 返回首页
          </Link>
          <h1 className="text-lg font-bold" style={{ color: "var(--color-scholar-blue)", fontFamily: "var(--font-serif)" }}>
            八字合婚
          </h1>
          <div />
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {[{ label: "甲方", form: formA, setForm: setFormA }, { label: "乙方", form: formB, setForm: setFormB }].map(({ label, form, setForm }) => (
            <div
              key={label}
              className="p-6 rounded-xl"
              style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow)" }}
            >
              <h3 className="text-sm font-bold mb-4" style={{ color: "var(--color-scholar-blue)" }}>{label}</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>八字（空格分隔四柱）</label>
                  <input
                    value={form.bazi}
                    onChange={(e) => setForm({ ...form, bazi: e.target.value })}
                    placeholder="如：辛卯 庚子 壬申 辛亥"
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{ background: "var(--color-bg-panel)", border: "1px solid var(--color-border)", color: "var(--color-text-primary)" }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>日主</label>
                    <input
                      value={form.dayMaster}
                      onChange={(e) => setForm({ ...form, dayMaster: e.target.value })}
                      placeholder="如：壬"
                      className="w-full px-3 py-2 rounded-lg text-sm"
                      style={{ background: "var(--color-bg-panel)", border: "1px solid var(--color-border)", color: "var(--color-text-primary)" }}
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>性别</label>
                    <select
                      value={form.gender}
                      onChange={(e) => setForm({ ...form, gender: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg text-sm"
                      style={{ background: "var(--color-bg-panel)", border: "1px solid var(--color-border)", color: "var(--color-text-primary)" }}
                    >
                      <option value="男">男</option>
                      <option value="女">女</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          ))}

          <div className="md:col-span-2 flex items-center justify-center gap-4">
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-3 rounded-xl text-sm font-medium text-white disabled:opacity-50"
              style={{ background: "var(--color-scholar-blue)" }}
            >
              {loading ? "分析中..." : "合婚分析"}
            </button>
          </div>
        </form>

        {error && (
          <div className="text-center text-sm mb-6" style={{ color: "var(--danger)" }}>{error}</div>
        )}

        {result && (
          <div className="space-y-6">
            <div className="text-center p-8 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow)" }}>
              <div className="text-[11px] uppercase tracking-widest mb-2" style={{ color: "var(--color-text-muted)" }}>兼容性评分</div>
              <div className="text-5xl font-bold mb-2" style={{ color: scoreColor }}>{result.compatibility_score}</div>
              <div className="text-sm" style={{ color: "var(--color-text-secondary)" }}>{result.compatibility_note}</div>
            </div>

            {result.relation_analysis && result.relation_analysis.length > 0 && (
              <div className="p-6 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--color-border)" }}>
                <h3 className="text-sm font-bold mb-4" style={{ color: "var(--color-scholar-blue)" }}>关系分析</h3>
                <div className="space-y-2">
                  {result.relation_analysis.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-xs px-2 py-0.5 rounded font-medium shrink-0" style={{ background: "var(--color-bg-panel)", color: "var(--color-text-secondary)" }}>
                        {r.type}
                      </span>
                      <span style={{ color: "var(--color-text-secondary)" }}>{r.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
