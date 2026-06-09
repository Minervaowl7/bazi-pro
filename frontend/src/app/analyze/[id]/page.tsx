"use client";

import { useEffect, useRef, useState, useCallback, Component, ReactNode } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useAnalysisStore } from "@/stores/analysisStore";
import type { AnalysisResultData } from "@/lib/types";
import AnalysisProgress from "@/components/AnalysisProgress";
import BaziChartCard from "@/components/BaziChartCard";
import DailyFortuneCard from "@/components/DailyFortuneCard";
import ShareCard from "@/components/ShareCard";
import StrengthSlider from "@/components/StrengthSlider";
import ShishenEnergyChart from "@/components/ShishenEnergyChart";
import SchoolPanel from "@/components/SchoolPanel";
import SchoolComparePanel from "@/components/SchoolComparePanel";
import DayunTimeline from "@/components/DayunTimeline";
import GongweiPanel from "@/components/GongweiPanel";
import ShenShaPanel from "@/components/ShenShaPanel";
import DimensionAnalysisPanel from "@/components/DimensionAnalysisPanel";
import ZiweiPanel from "@/components/ZiweiPanel";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";
import ChatPanel from "@/components/ChatPanel";
import ExportPanel from "@/components/ExportPanel";
import LifeReport from "@/components/LifeReport";
import LlmOverview from "@/components/LlmOverview";
import { SCHOOL_OPTIONS_WITH_ALL, WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";
import { gsap, useGSAP } from "@/lib/gsap";

import ChartQuality, { type ChartQualityData } from "@/components/ChartQuality";

const SCHOOL_OPTIONS = SCHOOL_OPTIONS_WITH_ALL;

interface FallbackProps { children: ReactNode; fallback?: ReactNode; }
class ErrorBoundary extends Component<FallbackProps, { hasError: boolean; error?: Error }> {
  constructor(props: FallbackProps) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) { console.error("[ErrorBoundary]", error, info.componentStack); }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <section className="card p-8 text-center" style={{ margin: "2rem auto", maxWidth: 600 }}>
          <h3 style={{ color: "var(--danger)", marginBottom: 8 }}>渲染出错</h3>
          <p style={{ color: "var(--text-2)", fontSize: 14 }}>{this.state.error?.message || "未知错误"}</p>
          <button onClick={() => this.setState({ hasError: false, error: undefined })}
            style={{ marginTop: 16, padding: "8px 20px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface)", cursor: "pointer", color: "var(--ink)" }}>
            重试
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
function Safe({ children, fallback }: FallbackProps) { return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>; }

const RelationGraph = dynamic(() => import("@/components/RelationGraph").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section className="card">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>关系图谱</h3>
      </div>
      <div className="p-12 text-center text-sm" style={{ color: "var(--text-3)" }}>关系图谱加载中…</div>
    </section>
  ),
});

const LifeKlineChart = dynamic(() => import("@/components/LifeKlineChart").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section className="card">
      <div className="border-b border-[var(--border)] px-6 py-4">
        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>人生 K 线</h3>
      </div>
      <div className="p-12 text-center text-sm" style={{ color: "var(--text-3)" }}>K线图加载中…</div>
    </section>
  ),
});

const TABS = [
  { id: "bazi", label: "四柱命盘", icon: "☰" },
  { id: "dayun", label: "大运流年", icon: "⏱" },
  { id: "detail", label: "宫位神煞", icon: "◈" },
  { id: "ziwei", label: "紫微斗数", icon: "★" },
  { id: "deep", label: "深度分析", icon: "◉" },
  { id: "analysis", label: "流派解读", icon: "✦" },
  { id: "chat", label: "命理问答", icon: "☯" },
] as const;
type TabId = typeof TABS[number]["id"];

function SkeletonCard() {
  return (
    <section className="card p-7 mb-6 animate-pulse">
      <div className="h-5 w-32 mb-6 rounded" style={{ background: "var(--surface-2)" }} />
      <div className="grid grid-cols-4 gap-4">
        {[1,2,3,4].map(i=>(
          <div key={i} className="text-center p-6 border border-[var(--border-subtle)] rounded-xl" style={{ background: "var(--surface-2)" }}>
            <div className="h-3 w-16 mx-auto mb-4 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-14 w-14 mx-auto mb-3 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-14 w-14 mx-auto mb-3 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-12 mx-auto rounded" style={{ background: "var(--surface-2)" }} />
          </div>
        ))}
      </div>
    </section>
  );
}

function SkeletonNarration() {
  return (
    <div className="space-y-4 mb-6">
      {[1,2,3].map(i=>(
        <div key={i} className="card p-6 animate-pulse border-l-4" style={{ borderLeftColor: "var(--border-subtle)" }}>
          <div className="h-4 w-24 mb-4 rounded" style={{ background: "var(--surface-2)" }} />
          <div className="space-y-3">
            <div className="h-4 w-full rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-5/6 rounded" style={{ background: "var(--surface-2)" }} />
            <div className="h-4 w-4/6 rounded" style={{ background: "var(--surface-2)" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalyzePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const analysisId = params.id as string;
  const { status, result, error, analysisId: storeAnalysisId, birthInput, fetchResult, startAnalysis, reset } = useAnalysisStore();
  const prevIdRef = useRef<string | null>(null);
  const [activeTab, setActiveTabRaw] = useState<TabId>(() => {
    const tabParam = searchParams.get("tab") as TabId | null;
    return tabParam && TABS.some(t => t.id === tabParam) ? tabParam : "bazi";
  });
  const setActiveTab = useCallback((tab: TabId) => {
    setActiveTabRaw(tab);
    router.replace(`/analyze/${analysisId}?tab=${tab}`, { scroll: false });
  }, [router, analysisId]);
  const [selectedSchool, setSelectedSchool] = useState("ziping");
  const [schoolDropdownOpen, setSchoolDropdownOpen] = useState(false);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tabContentRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const [loadTimeout, setLoadTimeout] = useState(false);

  const statusRef = useRef(status);
  useEffect(() => { statusRef.current = status; }, [status]);

  // analysisId 变化时重置 loadTimeout，防止旧分析的超时状态污染新分析
  // eslint-disable-next-line react-hooks/set-state-in-effect -- 分析 ID 变化是明确的重置时机
  useEffect(() => { setLoadTimeout(false); }, [analysisId]);

  useEffect(() => {
    if (!analysisId) return;
    // 15 秒加载超时保护 — 防止无限骨架屏（不依赖 status，避免状态变化重置计时器）
    const timer = setTimeout(() => {
      const s = statusRef.current;
      if (s !== "completed" && s !== "failed") {
        setLoadTimeout(true);
      }
    }, 15000);
    return () => clearTimeout(timer);
  }, [analysisId]);

  useEffect(() => {
    if (!analysisId) return;
    const fetchAndLog = (id: string) => {
      fetchResult(id).catch((err) => {
        console.error("[AnalyzePage] fetchResult failed:", err);
      });
    };
    if (analysisId !== prevIdRef.current) {
      prevIdRef.current = analysisId;
      if (analysisId !== storeAnalysisId) { reset(); fetchAndLog(analysisId); }
    } else if (status === "idle") { fetchAndLog(analysisId); }
  }, [analysisId, status, storeAnalysisId, fetchResult, reset]);
  useEffect(() => {
    if (!analysisId || status !== "polling") return;
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    pollTimerRef.current = setInterval(() => {
      const s = statusRef.current;
      if (s === "completed" || s === "failed") {
        if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
        return;
      }
      fetchResult(analysisId).catch(() => {});
    }, 5000);
    return () => { if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; } };
  }, [analysisId, status, fetchResult]);

  useEffect(() => {
    if (!schoolDropdownOpen) return;
    const handler = () => setSchoolDropdownOpen(false);
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [schoolDropdownOpen]);

  const handleReanalyze = useCallback(async () => {
    if (!birthInput) return;
    try {
      const newId = await startAnalysis({ ...birthInput, school: selectedSchool });
      router.push(`/analyze/${newId}`);
    } catch (err) {
      console.error("[AnalyzePage] reanalyze failed:", err);
    }
  }, [birthInput, selectedSchool, startAnalysis, router]);

  const handleGenerateReport = useCallback(() => {
    router.push(`/report/${analysisId}`);
  }, [analysisId, router]);

  const analysisResult = result?.result as AnalysisResultData | undefined;
  const narration = (result as Record<string,unknown>|null)?.narration as Record<string,unknown>|undefined;
  const isLoading = status==="submitting"||status==="streaming"||status==="polling";

  const strength = analysisResult?.strength;
  const wangshuai = strength?.wangshuai;
  const pattern = analysisResult?.pattern;
  const yongshen = analysisResult?.yongshen;
  const tiaohou = analysisResult?.tiaohou;
  const schoolAnalyses = analysisResult?.school_analyses as Record<string,unknown>|undefined;
  const currentSchool = (analysisResult?.school as string)||"ziping";
  const isCompareMode = currentSchool==="all";

  useGSAP(() => {
    if (!analysisResult || prefersReducedMotion) return;
    const targets = gsap.utils.toArray("[data-pill]");
    if (!targets.length) return;
    gsap.from(targets, {
      y: -20,
      autoAlpha: 0,
      stagger: 0.08,
      duration: 0.5,
      ease: "back.out(1.2)",
    });
  }, { scope: containerRef, dependencies: [analysisResult] });

  useGSAP(() => {
    if (!analysisResult || prefersReducedMotion) return;
    const targets = gsap.utils.toArray("[data-action-bar]");
    if (!targets.length) return;
    gsap.from(targets, {
      x: -30,
      autoAlpha: 0,
      duration: 0.5,
    });
  }, { scope: containerRef, dependencies: [analysisResult] });

  useGSAP(() => {
    if (prefersReducedMotion) return;
    if (!tabContentRef.current) return;
    gsap.from(tabContentRef.current, {
      autoAlpha: 0,
      y: 20,
      duration: 0.4,
    });
  }, { scope: containerRef, dependencies: [activeTab], revertOnUpdate: true });

  return (
    <ErrorBoundary fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
        <section className="card p-8 text-center" style={{ maxWidth: 500 }}>
          <h3 style={{ color: "var(--danger)", fontSize: 18, fontWeight: 700, marginBottom: 8 }}>页面渲染出错</h3>
          <p style={{ color: "var(--text-2)", fontSize: 14, marginBottom: 16 }}>分析结果渲染时发生异常，请重试或返回首页。</p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
            <button onClick={() => window.location.reload()}
              style={{ padding: "10px 24px", borderRadius: 10, border: "1px solid var(--border)", background: "var(--surface)", cursor: "pointer", color: "var(--ink)", fontSize: 14 }}>
              重试
            </button>
            <button onClick={() => window.location.href = "/"}
              style={{ padding: "10px 24px", borderRadius: 10, border: "none", background: "var(--scholar-blue)", cursor: "pointer", color: "#fff", fontSize: 14 }}>
              返回首页
            </button>
          </div>
        </section>
      </div>
    }>
    <div ref={containerRef} className="min-h-screen" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-[960px] mx-auto pb-10 px-6">

        {/* ===== 操作栏 ===== */}
        {analysisResult && (
          <div data-action-bar className="flex items-center gap-2.5 mb-7 flex-wrap">
            <div className="relative">
              <button
                onClick={(e)=>{e.stopPropagation();setSchoolDropdownOpen(!schoolDropdownOpen);}}
                className="flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
                style={{ color:"var(--text-2)", background:"var(--surface)" }}
              >
                {SCHOOL_OPTIONS.find(s=>s.value===currentSchool)?.label||"传统子平"}
                <svg aria-hidden="true" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"
                  style={{transform:schoolDropdownOpen?"rotate(180deg)":"none",transition:"transform 0.2s"}}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              {schoolDropdownOpen && (
                <div
                  className="card absolute left-0 top-full mt-1.5 w-60 z-50 overflow-hidden"
                >
                  {SCHOOL_OPTIONS.map(s=>(
                    <button key={s.value}
                      onClick={()=>{setSelectedSchool(s.value);setSchoolDropdownOpen(false);}}
                      className="w-full px-5 py-2.5 text-left transition-colors hover:bg-[var(--surface-2)]"
                      style={{fontSize:13,background:selectedSchool===s.value?"var(--cinnabar-light)":"transparent"}}
                    >
                      <div className="font-medium" style={{color:selectedSchool===s.value?"var(--wx-water)":"var(--ink)"}}>{s.label}</div>
                      <div style={{fontSize:11,color:"var(--text-4)"}}>{s.desc}</div>
                    </button>
                  ))}
                  <div style={{borderTop:"1px solid var(--border)"}}>
                    <button onClick={()=>{setSchoolDropdownOpen(false);handleReanalyze();}}
                      disabled={!birthInput||isLoading}
                      className="w-full px-5 py-2.5 font-medium disabled:opacity-50 transition-colors hover:bg-[var(--surface-2)]"
                      style={{fontSize:13,color:"var(--wx-water)"}}
                    >
                      以「{SCHOOL_OPTIONS.find(s=>s.value===selectedSchool)?.label}」重新分析
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button onClick={handleGenerateReport}
              className="flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
              style={{ color:"var(--text-2)", background:"var(--surface)" }}
            >
              <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              详批报告
            </button>

            <ExportPanel analysisId={analysisId} result={analysisResult} narration={narration} />
            <ShareCard result={analysisResult} />
          </div>
        )}

        {/* 加载状态 */}
        {isLoading && <AnalysisProgress />}

        {status==="failed" && (
          <section className="card p-6 mb-6" style={{ border: "1px solid var(--danger)" }}>
            <h3 className="font-bold text-base mb-2" style={{ color: "var(--danger)" }}>分析失败</h3>
            <p className="text-[15px]" style={{ color: "var(--text-2)" }}>{error||"未知错误"}</p>
          </section>
        )}

        {/* 骨架屏 */}
        {(isLoading || (status !== "completed" && status !== "failed" && !analysisResult)) && (
          <>
            {loadTimeout ? (
              <section className="card p-6 mb-6" style={{ border: "1px solid var(--warning)" }}>
                <h3 className="font-bold text-base mb-2" style={{ color: "var(--warning)" }}>加载缓慢</h3>
                <p className="text-[15px] mb-4" style={{ color: "var(--text-2)" }}>
                  分析结果加载已超过 15 秒，可能是首次启动需要加载古籍索引，请耐心等待或重试。
                </p>
                <button onClick={() => { setLoadTimeout(false); useAnalysisStore.setState({ status: "idle" }); }}
                  className="px-4 py-2 rounded-lg text-sm font-medium"
                  style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--ink)", cursor: "pointer" }}>
                  重新加载
                </button>
              </section>
            ) : !isLoading ? (
              <section className="card p-5 mb-6 flex items-center gap-3">
                <span className="w-2 h-2 shrink-0 animate-pulse" style={{ background: "var(--wx-water)" }} />
                <span className="text-[15px]" style={{ color: "var(--text-3)" }}>正在加载分析结果…</span>
              </section>
            ) : null}
            {!loadTimeout && <><SkeletonCard /><SkeletonNarration /></>}
          </>
        )}

        {/* ===== 分析结果（带 Tab 分页）===== */}
        {analysisResult ? (
          <Safe fallback={
            <section className="card p-8 text-center">
              <h3 className="font-bold text-base mb-2" style={{ color: "var(--danger)" }}>渲染出错</h3>
              <p className="text-[15px]" style={{ color: "var(--text-2)" }}>分析结果渲染时发生异常，请刷新页面重试。</p>
            </section>
          }>
          <>
            {/* 核心摘要条 — 始终可见 */}
            <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-6 gap-3 mb-8">
              {[
                {label:"旺衰",value:wangshuai?.verdict||"—"},
                {label:"格局",value:pattern?.pattern||"—"},
                {label:"用神",value:yongshen?.yongshen||"—",bg:"var(--wx-wood-bg)"},
                {label:"喜神",value:(yongshen?.xishen||[]).join(" ")||"—",bg:"var(--wx-water-bg)"},
                {label:"忌神",value:(yongshen?.jishen||[]).join(" ")||"—",bg:"var(--wx-fire-bg)"},
              ].map((item:{label:string;value:string;bg?:string})=>(
                <div data-pill key={item.label} className="card text-center relative overflow-hidden p-4 px-3" style={{ background: item.bg || "var(--surface)" }}>
                  {/* 顶部金线 */}
                  <div style={{
                    position:"absolute",top:0,left:"20%",right:"20%",height:1,
                    background:"linear-gradient(90deg,transparent,var(--gold),transparent)",
                    opacity:0.4,
                  }} />
                  <div className="mb-1.5 text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--text-3)" }}>{item.label}</div>
                  <div className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                    {item.value.split("").map((ch,i)=>{
                      const wx = GAN_WUXING[ch] || ZHI_WUXING[ch] || (["金","木","水","火","土"].includes(ch) ? ch : "");
                      const color = wx ? WUXING_COLORS[wx] : "var(--ink)";
                      return (
                        <span key={i} style={{color,marginRight:1}}>{ch}</span>
                      );
                    })}
                  </div>
                </div>
              ))}
              {tiaohou?.has_tiaohou&&(
                <div data-pill className="card text-center relative overflow-hidden p-4 px-3" style={{ background: "rgba(197,165,90,0.04)" }}>
                  <div className="absolute top-0 left-[20%] right-[20%] h-px opacity-40" style={{ background: "linear-gradient(90deg,transparent,var(--gold),transparent)" }} />
                  <div className="mb-1.5 text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--gold)" }}>调候</div>
                  <div className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                    {(tiaohou.tiaohou_gan||[]).map((ch,i)=>{
                      const wx = GAN_WUXING[ch] || "";
                      const color = wx ? WUXING_COLORS[wx] : "var(--gold)";
                      return <span key={i} style={{color,marginRight:2}}>{ch}</span>;
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* 命书 — LLM 润色的人生报告 */}
            {analysisResult?.life_report && (
              <LifeReport
                content={analysisResult.life_report as string}
                isLlmGenerated={true}
              />
            )}
            {!analysisResult?.life_report && analysisResult?.llm_overview && (
              <LifeReport
                content={analysisResult.llm_overview as string}
                isLlmGenerated={true}
              />
            )}

            {/* Tab 导航栏 — 分段控制器 */}
            <div className="relative mb-8">
            <div role="tablist" aria-label="分析结果分区" className="flex gap-0.5 p-[3px] overflow-auto scrollbar-none" style={{ background: "var(--surface-2)", border: "0.5px solid var(--border)", borderRadius: "var(--r)" }} onKeyDown={(e)=>{
              const idx=TABS.findIndex(t=>t.id===activeTab);
              if(e.key==="ArrowRight"||e.key==="ArrowDown"){e.preventDefault();setActiveTab(TABS[(idx+1)%TABS.length].id);}
              else if(e.key==="ArrowLeft"||e.key==="ArrowUp"){e.preventDefault();setActiveTab(TABS[(idx-1+TABS.length)%TABS.length].id);}
              else if(e.key==="Home"){e.preventDefault();setActiveTab(TABS[0].id);}
              else if(e.key==="End"){e.preventDefault();setActiveTab(TABS[TABS.length-1].id);}
            }}>
              {TABS.map(tab=>{
                const isActive=activeTab===tab.id;
                return (
                  <button key={tab.id}
                    role="tab"
                    aria-selected={isActive}
                    tabIndex={isActive?0:-1}
                    onClick={()=>setActiveTab(tab.id)}
                    className="flex-1 py-2.5 px-1.5 text-[13px] text-center rounded-md cursor-pointer relative transition-all duration-150"
                    style={{
                      fontWeight: isActive ? 600 : 500,
                      fontFamily: "var(--font-body)",
                      color: isActive ? "var(--ink)" : "var(--text-3)",
                      background: isActive ? "var(--surface)" : "transparent",
                      boxShadow: isActive ? "var(--shadow-xs)" : "none",
                    }}
                  >
                    <span aria-hidden="true" style={{marginRight:5,fontSize:14}}>{tab.icon}</span>{tab.label}
                  </button>
                );
              })}
            </div>
            {/* 右侧滚动提示渐变 */}
            <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none sm:hidden" style={{ background: "linear-gradient(to left, var(--surface-2), transparent)" }} />
            </div>

            {/* Tab 内容区 */}
            <div ref={tabContentRef} className="space-y-10">
              {/* Tab 1: 四柱命盘 */}
              {activeTab==="bazi"&&(
                <div>
                  <BaziChartCard result={analysisResult} />

                  {analysisResult?.chart_quality && <ChartQuality data={analysisResult.chart_quality as unknown as ChartQualityData} />}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <StrengthSlider
                      strength={analysisResult?.strength}
                      dayMaster={analysisResult?.validation?.day_master}
                    />
                    <ShishenEnergyChart result={analysisResult} />
                  </div>

                  <Safe fallback={
                    <section className="card p-10 text-center">
                      <span className="text-sm" style={{ color: "var(--text-3)" }}>关系图谱暂不可用</span>
                    </section>
                  }>
                    <RelationGraph result={analysisResult} />
                  </Safe>

                  {pattern?.reason && (
                    <section className="card">
                      <div className="border-b border-[var(--border)] px-6 py-4">
                        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>格局判定依据</h3>
                        {pattern.confidence!==undefined&&(
                          <span className="tabular-nums ml-3" style={{fontSize:13,color:"var(--text-4)"}}>{(pattern.confidence*100).toFixed(0)}%</span>
                        )}
                      </div>
                      <div className="p-7">
                        <p className="text-[15px] leading-relaxed" style={{ color: "var(--text-2)" }}>{pattern.reason}</p>
                        {pattern.confidence!==undefined&&(
                          <div className="mt-4 flex items-center gap-3">
                            <div className="flex-1 h-2 overflow-hidden" style={{background:"var(--surface-2)"}}>
                              <div className="h-full" style={{
                                width:`${Math.min(pattern.confidence*100,100)}%`,
                                transition:"width 0.7s",
                                background:pattern.confidence>=0.8?"var(--success)":pattern.confidence>=0.6?"var(--warning)":"var(--danger)",
                              }}/>
                            </div>
                          </div>
                        )}
                      </div>
                    </section>
                  )}
                </div>
              )}

              {/* Tab 2: 大运流年 */}
              {activeTab==="dayun"&&(
                <div>
                  <DayunTimeline result={analysisResult} />

                  <Safe fallback={
                    <section className="card p-10 text-center">
                      <span className="text-sm" style={{ color: "var(--text-3)" }}>K线图暂不可用</span>
                    </section>
                  }>
                    <LifeKlineChart analysisId={analysisId} />
                  </Safe>

                  <DailyFortuneCard analysisId={analysisId} />
                </div>
              )}

              {/* Tab 3: 宫位神煞 */}
              {activeTab==="detail"&&(
                <div>
                  <GongweiPanel result={analysisResult} />
                  <ShenShaPanel result={analysisResult} />
                </div>
              )}

              {/* Tab 4: 紫微斗数 */}
              {activeTab==="ziwei"&&(
                <div>
                  {analysisResult?.ziwei ? (
                    <section className="card p-6">
                      <div className="border-b border-[var(--border)] pb-3 mb-4">
                        <h3 className="font-bold text-base" style={{ fontFamily: "var(--font-display)" }}>紫微斗数命盘</h3>
                      </div>
                      <ZiweiPanel data={analysisResult.ziwei as Record<string, unknown>} />
                    </section>
                  ) : (
                    <section className="card p-6">
                      <p className="text-[15px]" style={{ color: "var(--text-3)" }}>紫微斗数数据不可用（需安装 iztro-py 依赖）</p>
                    </section>
                  )}
                </div>
              )}

              {/* Tab 5: 深度分析 */}
              {activeTab==="deep"&&(
                <div className="space-y-8">
                  <DimensionAnalysisPanel
                    dimension="marriage"
                    data={(analysisResult?.marriage_analysis as Record<string,unknown>)||{}}
                    narration={typeof narration?.marriage==="string"?narration.marriage:""}
                  />
                  <DimensionAnalysisPanel
                    dimension="health"
                    data={(analysisResult?.health_analysis as Record<string,unknown>)||{}}
                    narration={typeof narration?.health==="string"?narration.health:""}
                  />
                  <DimensionAnalysisPanel
                    dimension="wealth"
                    data={(analysisResult?.wealth_analysis as Record<string,unknown>)||{}}
                    narration={typeof narration?.wealth==="string"?narration.wealth:""}
                  />
                  <DimensionAnalysisPanel
                    dimension="family"
                    data={(analysisResult?.family_analysis as Record<string,unknown>)||{}}
                    narration={typeof narration?.family==="string"?narration.family:""}
                  />
                </div>
              )}

              {/* Tab 6: 流派解读 */}
              {activeTab==="analysis"&&(
                <div style={{maxWidth:860,marginLeft:"auto",marginRight:"auto"}}>
                  {analysisResult?.llm_overview && <LlmOverview content={analysisResult.llm_overview as string} />}
                  {isCompareMode&&schoolAnalyses?<SchoolComparePanel schoolAnalyses={schoolAnalyses}/>:<SchoolPanel result={analysisResult} narration={narration}/>}
                </div>
              )}

              {/* Tab 7: 命理问答 */}
              {activeTab==="chat"&&(
                <div>
                  <ChatPanel analysisId={analysisId} school={currentSchool === "all" ? "ziping" : currentSchool} />
                </div>
              )}
            </div>
          </>
          </Safe>
        ):null}

        {status==="completed"&&!analysisResult&&result?.status==="completed"&&(
          <section className="card p-6">
            <p className="text-[15px]" style={{ color: "var(--text-2)" }}>分析已完成，但无详细结果数据。</p>
          </section>
        )}
      </div>
    </div>
    </ErrorBoundary>
  );
}
