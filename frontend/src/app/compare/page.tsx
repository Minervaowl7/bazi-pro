"use client";

import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";

interface HistoryItem {
  id: string;
  bazi: string;
  day_master: string;
  gender: string;
  created_at: string;
}

interface HehunResult {
  compatibility_score: number;
  compatibility_note: string;
  pillar_diff: Array<{ position?: string; diff?: string }>;
  wuxing_overlap: Record<string, unknown>;
  yongshen_diff: Record<string, unknown>;
  relation_analysis: Array<{ type?: string; description?: string }>;
}

function PersonForm({ label, form, setForm, history, idPrefix }: {
  label: string;
  form: { bazi: string; dayMaster: string; gender: string };
  setForm: (f: { bazi: string; dayMaster: string; gender: string }) => void;
  history: HistoryItem[];
  idPrefix: string;
}) {
  return (
    <div className="p-6 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow)" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold" style={{ color: "var(--scholar-blue)" }}>{label}</h3>
        <div className="flex gap-1">
          {["男", "女"].map((g) => (
            <button
              key={g} type="button"
              aria-pressed={form.gender === g}
              onClick={() => setForm({ ...form, gender: g })}
              className="px-2.5 py-1 rounded-md text-xs font-medium transition-all"
              style={{
                background: form.gender === g ? "var(--scholar-blue)" : "var(--surface-2)",
                color: form.gender === g ? "#fff" : "var(--text-3)",
                border: form.gender === g ? "none" : "1px solid var(--border)",
              }}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {history.length > 0 && (
        <div className="mb-4">
          <label className="block text-[11px] mb-1.5 uppercase tracking-wider" style={{ color: "var(--text-3)" }}>
            从历史记录选择
          </label>
          <select
            onChange={(e) => {
              const item = history.find(h => h.id === e.target.value);
              if (item) setForm({ bazi: item.bazi, dayMaster: item.day_master, gender: item.gender || form.gender });
            }}
            className="w-full px-3 py-2 rounded-lg text-xs"
            style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--ink)" }}
          >
            <option value="">手动输入</option>
            {history.map((h) => (
              <option key={h.id} value={h.id}>{h.bazi} ({h.day_master}日主)</option>
            ))}
          </select>
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label htmlFor={`${idPrefix}-bazi`} className="block text-[11px] mb-1.5 uppercase tracking-wider" style={{ color: "var(--text-3)" }}>
            八字（空格分隔四柱）
          </label>
          <input
            id={`${idPrefix}-bazi`}
            value={form.bazi}
            onChange={(e) => setForm({ ...form, bazi: e.target.value })}
            placeholder="如：辛卯 庚子 壬申 辛亥"
            className="w-full px-3 py-2.5 rounded-lg text-sm"
            style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--ink)" }}
          />
        </div>
        <div>
          <label htmlFor={`${idPrefix}-dayMaster`} className="block text-[11px] mb-1.5 uppercase tracking-wider" style={{ color: "var(--text-3)" }}>
            日主
          </label>
          <input
            id={`${idPrefix}-dayMaster`}
            value={form.dayMaster}
            onChange={(e) => setForm({ ...form, dayMaster: e.target.value })}
            placeholder="如：壬"
            className="w-full px-3 py-2.5 rounded-lg text-sm"
            style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--ink)" }}
          />
        </div>
      </div>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "var(--success)" : score >= 60 ? "var(--warning)" : "var(--danger)";

  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle cx="60" cy="60" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" className="transition-all duration-1000" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums" style={{ color }}>{score}</span>
        <span className="text-[10px] mt-0.5" style={{ color: "var(--text-3)" }}>兼容度</span>
      </div>
    </div>
  );
}

export default function ComparePage() {
  const [formA, setFormA] = useState({ bazi: "", dayMaster: "", gender: "男" });
  const [formB, setFormB] = useState({ bazi: "", dayMaster: "", gender: "女" });
  const [result, setResult] = useState<HehunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/v2/history`)
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : (data.analyses || []);
        setHistory(list);
      })
      .catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError(err?.error?.message || err?.detail || `请求失败 (${res.status})`);
        return;
      }
      const data = await res.json();
      if (data.status === "completed") {
        setResult(data.result);
      } else {
        setError(data.error?.message || "分析失败");
      }
    } catch {
      setError("无法连接服务器");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)]" style={{ background: "var(--bg)" }}>
      <div className="w-full px-6 md:px-12 lg:px-16 xl:px-24 py-10">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-2xl md:text-3xl font-bold mb-2"
            style={{ color: "var(--ink)", fontFamily: "var(--font-display)" }}>
            八字合婚
          </h1>
          <p className="text-sm" style={{ color: "var(--text-3)" }}>
            基于五行生克、日主关系、用神互补的确定性兼容度分析
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <PersonForm label="甲方" form={formA} setForm={setFormA} history={history} idPrefix="personA" />
            <PersonForm label="乙方" form={formB} setForm={setFormB} history={history} idPrefix="personB" />
          </div>

          {error && (
            <div className="text-center text-sm mb-6 p-3 rounded-lg"
              style={{ background: "rgba(220,38,38,0.06)", color: "var(--danger)", border: "1px solid rgba(220,38,38,0.15)" }}>
              {error}
            </div>
          )}

          <div className="flex justify-center">
            <button
              type="submit"
              disabled={loading}
              className="px-10 py-3 rounded-xl text-sm font-medium text-white disabled:opacity-50 transition-all active:scale-[0.97]"
              style={{ background: "var(--scholar-blue)", boxShadow: "0 2px 12px rgba(44,62,107,0.3)" }}
            >
              {loading ? "分析中..." : "合婚分析"}
            </button>
          </div>
        </form>

        {/* Results */}
        {result && (
          <div className="mt-12 space-y-6 animate-fade-in">
            {/* Score */}
            <div className="p-8 rounded-xl text-center"
              style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow)" }}>
              <ScoreRing score={result.compatibility_score} />
              <p className="text-sm mt-4" style={{ color: "var(--text-2)" }}>
                {result.compatibility_note}
              </p>
            </div>

            {/* Relation analysis */}
            {result.relation_analysis && result.relation_analysis.length > 0 && (
              <div className="p-6 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
                <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-2)" }}>关系分析</h3>
                <div className="space-y-2.5">
                  {result.relation_analysis.map((r, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <span className="text-[11px] px-2 py-0.5 rounded-md font-medium shrink-0"
                        style={{ background: "var(--cinnabar-light)", color: "var(--cinnabar)" }}>
                        {r.type}
                      </span>
                      <span className="text-sm" style={{ color: "var(--text-2)" }}>{r.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pillar diff */}
            {result.pillar_diff && result.pillar_diff.length > 0 && (
              <div className="p-6 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
                <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-2)" }}>四柱对比</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {result.pillar_diff.map((p, i) => (
                    <div key={i} className="text-center p-3 rounded-lg" style={{ background: "var(--surface-2)" }}>
                      <div className="text-[11px] mb-1" style={{ color: "var(--text-3)" }}>{p.position}</div>
                      <div className="text-xs font-medium" style={{ color: "var(--ink)" }}>{p.diff || "—"}</div>
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
