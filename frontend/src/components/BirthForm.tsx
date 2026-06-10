"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAnalysisStore } from "@/stores/analysisStore";
import { WUXING_COLORS, WUXING_BG, SCHOOL_OPTIONS } from "@/lib/constants";

// 与 server/true_solar_time.py CHINA_CITIES 同步（38 城市）
const CITIES = [
  { name: "北京", lng: 116.40 }, { name: "上海", lng: 121.47 },
  { name: "广州", lng: 113.26 }, { name: "深圳", lng: 114.06 },
  { name: "成都", lng: 104.07 }, { name: "重庆", lng: 106.55 },
  { name: "武汉", lng: 114.30 }, { name: "杭州", lng: 120.15 },
  { name: "南京", lng: 118.78 }, { name: "天津", lng: 117.20 },
  { name: "西安", lng: 108.94 }, { name: "长沙", lng: 112.97 },
  { name: "沈阳", lng: 123.43 }, { name: "哈尔滨", lng: 126.63 },
  { name: "大连", lng: 121.62 }, { name: "济南", lng: 117.00 },
  { name: "青岛", lng: 120.38 }, { name: "郑州", lng: 113.65 },
  { name: "昆明", lng: 102.73 }, { name: "兰州", lng: 103.83 },
  { name: "太原", lng: 112.55 }, { name: "合肥", lng: 117.28 },
  { name: "福州", lng: 119.30 }, { name: "厦门", lng: 118.10 },
  { name: "南昌", lng: 115.89 }, { name: "长春", lng: 125.32 },
  { name: "石家庄", lng: 114.51 }, { name: "贵阳", lng: 106.71 },
  { name: "南宁", lng: 108.37 }, { name: "海口", lng: 110.35 },
  { name: "呼和浩特", lng: 111.75 }, { name: "乌鲁木齐", lng: 87.62 },
  { name: "拉萨", lng: 91.11 }, { name: "银川", lng: 106.27 },
  { name: "西宁", lng: 101.77 }, { name: "台北", lng: 121.56 },
  { name: "香港", lng: 114.17 }, { name: "澳门", lng: 113.55 },
];

const SHICHEN_OPTIONS = [
  { label: "子时 (23:00-01:00)", value: "23:00" },
  { label: "丑时 (01:00-03:00)", value: "01:00" },
  { label: "寅时 (03:00-05:00)", value: "03:00" },
  { label: "卯时 (05:00-07:00)", value: "05:00" },
  { label: "辰时 (07:00-09:00)", value: "07:00" },
  { label: "巳时 (09:00-11:00)", value: "09:00" },
  { label: "午时 (11:00-13:00)", value: "11:00" },
  { label: "未时 (13:00-15:00)", value: "13:00" },
  { label: "申时 (15:00-17:00)", value: "15:00" },
  { label: "酉时 (17:00-19:00)", value: "17:00" },
  { label: "戌时 (19:00-21:00)", value: "19:00" },
  { label: "亥时 (21:00-23:00)", value: "21:00" },
];

export default function BirthForm() {
  const router = useRouter();
  const { submitPaipan, paipanResult, paipanLoading, startAnalysis, status } = useAnalysisStore();

  const [form, setForm] = useState({ gender: "男", name: "", solarDate: "", shichen: "", school: "ziping", city: "", cityLng: 0 });
  const [error, setError] = useState("");
  const [showPaipan, setShowPaipan] = useState(false);

  const [cityInput, setCityInput] = useState("");
  const [cityOpen, setCityOpen] = useState(false);
  const [cityFilter, setCityFilter] = useState("");
  const cityRef = useRef<HTMLDivElement>(null);
  const cityInputRef = useRef<HTMLInputElement>(null);

  const isSubmitting = status === "submitting" || paipanLoading;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (cityRef.current && !cityRef.current.contains(e.target as Node)) setCityOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredCities = cityFilter ? CITIES.filter(c => c.name.includes(cityFilter)) : CITIES;

  const handleCitySelect = useCallback((name: string, lng: number) => {
    setCityInput(name);
    setForm(prev => ({ ...prev, city: name, cityLng: lng }));
    setCityOpen(false);
    setCityFilter("");
    setShowPaipan(false);
  }, []);

  function handleChange(field: string, value: string | number) {
    setForm(prev => ({ ...prev, [field]: value }));
    setError("");
  }

  async function handlePaipan(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.solarDate) { setError("请选择出生日期"); return; }
    const solarDatetime = form.shichen ? `${form.solarDate} ${form.shichen}` : form.solarDate;
    try {
      await submitPaipan({ 性别: form.gender, 阳历: solarDatetime });
      setShowPaipan(true);
    } catch (err) { setError(err instanceof Error ? err.message : "排盘失败"); }
  }

  async function handleDeepAnalysis() {
    if (!paipanResult || paipanResult.status !== "completed") return;
    const solarDatetime = form.shichen ? `${form.solarDate} ${form.shichen}` : form.solarDate;
    try {
      const analysisId = await startAnalysis({
        性别: paipanResult.性别, 八字: paipanResult.八字, 日主: paipanResult.日主,
        阳历: solarDatetime, 生肖: paipanResult.生肖, school: form.school,
        name: form.name || undefined,
        ...(form.cityLng ? { longitude: form.cityLng } : {}),
      });
      router.push(`/analyze/${analysisId}`);
    } catch (err) { setError(err instanceof Error ? err.message : "提交失败"); }
  }

  return (
    <div>
      <form onSubmit={handlePaipan} className="space-y-3.5">
        {/* 性别 */}
        <div>
          <label className="form-label">性别</label>
          <div className="flex gap-2 mt-1.5">
            {["男", "女"].map(g => (
              <button key={g} type="button" onClick={() => handleChange("gender", g)}
                className={`form-input flex-1 text-center cursor-pointer transition-all duration-200 ${
                  form.gender === g ? "font-medium" : ""
                }`}
                style={{
                  color: form.gender === g ? "var(--cinnabar)" : "var(--text-2)",
                  background: form.gender === g ? "var(--cinnabar-light)" : "transparent",
                  borderColor: form.gender === g ? "var(--cinnabar)" : "var(--border)",
                }}
              >{g}</button>
            ))}
          </div>
        </div>

        {/* 姓名 */}
        <div>
          <label className="form-label">姓名 <span className="text-[10px] font-normal" style={{ color: "var(--text-4)" }}>选填，留空显示"命主"</span></label>
          <input type="text" value={form.name} placeholder="请输入姓名" autoComplete="name" className="form-input mt-1.5"
            onChange={e => handleChange("name", e.target.value)} />
        </div>

        {/* 出生日期 + 出生时辰 */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="form-label">出生日期 <span style={{ color: "var(--danger)" }}>*</span></label>
            <input type="date" value={form.solarDate} autoComplete="bday" className="form-input mt-1.5"
              onChange={e => { handleChange("solarDate", e.target.value); setShowPaipan(false); }} />
          </div>
          <div>
            <label className="form-label">出生时辰</label>
            <select value={form.shichen} className="form-input mt-1.5"
              style={{ color: form.shichen ? "var(--ink)" : "var(--text-3)" }}
              onChange={e => { handleChange("shichen", e.target.value); setShowPaipan(false); }}>
              <option value="">不确定时辰</option>
              {SHICHEN_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
        </div>

        {/* 城市搜索 */}
        <div>
          <label className="form-label">出生城市（真太阳时校正）</label>
          <div ref={cityRef} className="relative mt-1.5">
            <input ref={cityInputRef} type="text" value={cityInput} placeholder="输入城市名搜索…" autoComplete="off" className="form-input"
              onFocus={() => setCityOpen(true)}
              onChange={e => { setCityInput(e.target.value); setCityFilter(e.target.value); setCityOpen(true); if (!e.target.value) setForm(prev => ({ ...prev, city: "", cityLng: 0 })); }} />
            {cityOpen && (
              <div role="listbox" className="absolute top-full left-0 right-1 mt-1 max-h-[200px] overflow-y-auto" style={{ zIndex: "var(--z-dropdown)", background: "var(--surface)", border: "0.5px solid var(--border)", borderRadius: "var(--r-sm)", boxShadow: "0 8px 24px rgba(0,0,0,0.08)" }}>
                {filteredCities.length === 0 && <div className="px-3 py-2 text-[13px]" style={{ color: "var(--text-3)" }}>无匹配城市</div>}
                {filteredCities.map(c => (
                  <div key={c.name} role="option" aria-selected={form.city === c.name} onClick={() => handleCitySelect(c.name, c.lng)}
                    className="flex items-center justify-between px-3 py-2 cursor-pointer text-[13px] hover-row"
                    style={{ color: "var(--ink)", background: form.city === c.name ? "var(--cinnabar-light)" : "transparent" }}>
                    <span>{c.name}</span>
                    <span className="text-[11px]" style={{ color: "var(--text-3)" }}>东经{c.lng.toFixed(1)}°</span>
                  </div>
                ))}
                <div className="px-3 py-1.5 text-[11px] border-t" style={{ color: "var(--text-4)", borderColor: "var(--border-subtle)" }}>
                  {cityFilter ? `${filteredCities.length} 个匹配` : `全部 ${CITIES.length} 个城市`}
                </div>
              </div>
            )}
          </div>
        </div>

        {error && <p className="text-xs" style={{ color: "var(--danger)" }}>{error}</p>}

        {/* 提交按钮 */}
        <button type="submit" disabled={isSubmitting}
          className="form-input text-center font-semibold tracking-[0.1em] hover-lift disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ height: 42, background: "linear-gradient(135deg, var(--cinnabar), #a8503a)", color: "#fff", boxShadow: "0 2px 12px rgba(201,100,66,0.2)" }}>
          {paipanLoading ? "排盘中…" : "排盘"}
        </button>
      </form>

      {/* 排盘结果 */}
      {showPaipan && paipanResult && paipanResult.status === "completed" && (
        <div className="mt-7 pt-7 animate-fade-in" style={{ borderTop: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold tracking-wide" style={{ color: "var(--ink)" }}>八字命盘</h3>
            <span className="text-xs tabular-nums" style={{ color: "var(--text-3)" }}>{paipanResult.生肖} · {paipanResult.日主}日主</span>
          </div>
          <div className="overflow-x-auto mb-5">
            <div className="grid grid-cols-4 gap-3">
              {(paipanResult.pillars || []).map(p => (
                <div key={p.position} className="flex flex-col items-center gap-1 py-4 rounded-xl" style={{ background: "var(--surface-2)", border: "1px solid var(--border)" }}>
                  <span className="text-[11px] font-medium mb-2 px-2 py-0.5 rounded-full" style={{ color: "var(--text-3)", background: "var(--surface-2)" }}>{p.position}</span>
                  <span className="text-2xl font-bold leading-none" style={{ color: p.wuxing_gan ? WUXING_COLORS[p.wuxing_gan] : "inherit" }}>{p.gan || "—"}</span>
                  <span className="w-6 my-1.5" style={{ height: "1px", background: "var(--border)" }} />
                  <span className="text-2xl font-bold leading-none" style={{ color: p.wuxing_zhi ? WUXING_COLORS[p.wuxing_zhi] : "inherit" }}>{p.zhi || "—"}</span>
                  <div className="flex gap-1 mt-2">
                    {p.gan && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ color: WUXING_COLORS[p.wuxing_gan] || "inherit", background: WUXING_BG[p.wuxing_gan] || "transparent" }}>{p.wuxing_gan}</span>}
                    {p.zhi && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ color: WUXING_COLORS[p.wuxing_zhi] || "inherit", background: WUXING_BG[p.wuxing_zhi] || "transparent" }}>{p.wuxing_zhi}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mb-5">
            <label className="form-label">选择解读流派</label>
            <div className="grid grid-cols-3 gap-2 mt-1.5">
              {SCHOOL_OPTIONS.map(s => (
                <button key={s.value} type="button" onClick={() => handleChange("school", s.value)}
                  className="p-3 rounded-xl text-left transition-all duration-200"
                  style={{ border: form.school === s.value ? "2px solid var(--wx-water)" : "1px solid var(--border)", background: form.school === s.value ? "rgba(46,92,138,0.06)" : "var(--surface-2)" }}>
                  <div className="text-xs font-semibold" style={{ color: form.school === s.value ? "var(--wx-water)" : "var(--ink)" }}>{s.label}</div>
                  <div className="text-[11px] mt-0.5" style={{ color: "var(--text-3)" }}>{s.desc}</div>
                </button>
              ))}
            </div>
          </div>
          <button type="button" onClick={handleDeepAnalysis} disabled={status === "submitting" || status === "streaming"}
            className="w-full py-3.5 rounded-xl font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] flex items-center justify-center gap-2"
            style={{ background: "var(--ink)", color: "var(--bg)", boxShadow: "0 6px 20px rgba(0,0,0,0.3)" }}>
            {status === "submitting" ? "提交中…" : "深度解读"}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
          <p className="text-center text-[11px] mt-3" style={{ color: "var(--text-3)", opacity: 0.6 }}>旺衰判定 · 格局筛查 · 喜用神推导 · 古籍引证</p>
        </div>
      )}
    </div>
  );
}
