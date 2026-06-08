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
import ChatPanel from "@/components/ChatPanel";
import ExportPanel from "@/components/ExportPanel";
import { SCHOOL_OPTIONS_WITH_ALL, WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";
import { gsap, useGSAP } from "@/lib/gsap";

import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import ChartQuality, { type ChartQualityData } from "@/components/ChartQuality";

function LlmOverview({ content }: { content: string }) {
  return (
    <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-md)", borderRadius: "var(--radius-md)", overflow: "hidden" }}>
      <div style={{ borderBottom: "1px solid var(--color-border-subtle)", padding: "20px 32px" }} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div style={{ width: 36, height: 36, borderRadius: "50%", background: "linear-gradient(135deg, var(--color-cinnabar), #a04030)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 8px rgba(201,100,66,0.25)" }}>
            <span style={{ fontSize: 16, color: "#fff", fontFamily: "var(--font-serif)" }}>命</span>
          </div>
          <div>
            <h3 className="font-bold" style={{ fontSize: 18, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)", letterSpacing: "-0.01em" }}>命书</h3>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 2 }}>基于确定性计算 · 深度解读</p>
          </div>
        </div>
      </div>
      <div className="llm-overview-body" style={{ padding: "32px", color: "var(--color-text-secondary)", lineHeight: 1.75, fontSize: 16, fontFamily: "var(--font-serif)" }}>
        <ReactMarkdown remarkPlugins={[RemarkGfm]}>{content}</ReactMarkdown>
      </div>
      <style jsx>{`
        .llm-overview-body :global(h2) { color: var(--color-cinnabar); font-size: 1.25rem; font-weight: 700; font-family: var(--font-serif); margin-top: 2rem; margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--color-border-subtle); }
        .llm-overview-body :global(h2:first-child) { margin-top: 0; }
        .llm-overview-body :global(h3) { color: var(--color-text-primary); font-size: 1.1rem; font-weight: 600; font-family: var(--font-serif); margin-top: 1.4rem; margin-bottom: 0.6rem; }
        .llm-overview-body :global(p) { margin-bottom: 0.8rem; }
        .llm-overview-body :global(strong) { color: var(--color-text-primary); font-weight: 700; }
        .llm-overview-body :global(ul), .llm-overview-body :global(ol) { padding-left: 1.3rem; margin: 0.6rem 0; }
        .llm-overview-body :global(li) { margin: 0.3rem 0; line-height: 1.75; }
        .llm-overview-body :global(blockquote) { border-left: 3px solid var(--color-cinnabar); padding-left: 1rem; opacity: 0.9; margin: 0.8rem 0; font-style: italic; }
        .llm-overview-body :global(code) { background: var(--surface-warm); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
      `}</style>
    </section>
  );
}

const SCHOOL_OPTIONS = SCHOOL_OPTIONS_WITH_ALL;

interface FallbackProps { children: ReactNode; fallback?: ReactNode; }
class ErrorBoundary extends Component<FallbackProps, { hasError: boolean }> {
  constructor(props: FallbackProps) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() { if (this.state.hasError) return this.props.fallback || null; return this.props.children; }
}
function Safe({ children, fallback }: FallbackProps) { return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>; }

const RelationGraph = dynamic(() => import("@/components/RelationGraph").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)"}}>
      <div style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}}>
        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>关系图谱</h3>
      </div>
      <div className="p-12 text-center" style={{fontSize:14,color:"var(--color-text-muted)"}}>关系图谱加载中…</div>
    </section>
  ),
});

const LifeKlineChart = dynamic(() => import("@/components/LifeKlineChart").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)"}}>
      <div style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}}>
        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>人生 K 线</h3>
      </div>
      <div className="p-12 text-center" style={{fontSize:14,color:"var(--color-text-muted)"}}>K线图加载中…</div>
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
    <section className="p-7 mb-6 animate-pulse border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
      <div className="h-5 w-32 mb-6" style={{background:"var(--bg-hover)"}} />
      <div className="grid grid-cols-4 gap-4">
        {[1,2,3,4].map(i=>(
          <div key={i} className="text-center p-6 border" style={{background:"var(--bg-secondary)",borderColor:"var(--color-border-subtle)"}}>
            <div className="h-3 w-16 mx-auto mb-4" style={{background:"var(--bg-hover)"}} />
            <div className="h-14 w-14 mx-auto mb-3" style={{background:"var(--bg-hover)"}} />
            <div className="h-14 w-14 mx-auto mb-3" style={{background:"var(--bg-hover)"}} />
            <div className="h-4 w-12 mx-auto" style={{background:"var(--bg-hover)"}} />
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
        <div key={i} className="p-6 animate-pulse border-l-4" style={{background:"var(--surface)",borderLeftColor:"var(--color-border-subtle)",borderRight:"1px solid var(--color-border)",borderTop:"1px solid var(--color-border)",borderBottom:"1px solid var(--color-border)"}}>
          <div className="h-4 w-24 mb-4" style={{background:"var(--bg-hover)"}} />
          <div className="space-y-3">
            <div className="h-4 w-full" style={{background:"var(--bg-hover)"}} />
            <div className="h-4 w-5/6" style={{background:"var(--bg-hover)"}} />
            <div className="h-4 w-4/6" style={{background:"var(--bg-hover)"}} />
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
  const prefersReducedMotion = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (!analysisId) return;
    if (analysisId !== prevIdRef.current) {
      prevIdRef.current = analysisId;
      if (analysisId !== storeAnalysisId) { reset(); fetchResult(analysisId).catch(() => {}); }
    } else if (status === "idle") { fetchResult(analysisId).catch(() => {}); }
  }, [analysisId, status, storeAnalysisId, fetchResult, reset]);

  const statusRef = useRef(status);
  useEffect(() => { statusRef.current = status; }, [status]);
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
    } catch {}
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
    gsap.from("[data-pill]", {
      y: -20,
      autoAlpha: 0,
      stagger: 0.08,
      duration: 0.5,
      ease: "back.out(1.2)",
    });
  }, { scope: containerRef, dependencies: [analysisResult] });

  useGSAP(() => {
    if (!analysisResult || prefersReducedMotion) return;
    gsap.from("[data-action-bar]", {
      x: -30,
      autoAlpha: 0,
      duration: 0.5,
    });
  }, { scope: containerRef, dependencies: [analysisResult] });

  useGSAP(() => {
    if (prefersReducedMotion) return;
    gsap.from(tabContentRef.current, {
      autoAlpha: 0,
      y: 20,
      duration: 0.4,
    });
  }, { scope: containerRef, dependencies: [activeTab], revertOnUpdate: true });

  return (
    <div ref={containerRef} style={{minHeight:"100vh",background:"var(--background)"}}>
      <main style={{width:"100%",maxWidth:960,margin:"0 auto",paddingTop:72,paddingBottom:40,paddingLeft:24,paddingRight:24}}>

        {/* ===== 操作栏 ===== */}
        {analysisResult && (
          <div data-action-bar className="flex items-center gap-2.5 mb-7 flex-wrap">
            <div className="relative">
              <button
                onClick={(e)=>{e.stopPropagation();setSchoolDropdownOpen(!schoolDropdownOpen);}}
                className="flex items-center gap-1.5 px-3.5 py-2 font-medium border transition-colors"
                style={{
                  fontSize:13,
                  color:"var(--color-text-secondary)",
                  background:"var(--surface)",
                  borderColor:"var(--color-border)",
                  borderRadius:"var(--radius-sm)",
                }}
              >
                {SCHOOL_OPTIONS.find(s=>s.value===currentSchool)?.label||"传统子平"}
                <svg aria-hidden="true" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"
                  style={{transform:schoolDropdownOpen?"rotate(180deg)":"none",transition:"transform 0.2s"}}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              {schoolDropdownOpen && (
                <div
                  className="absolute left-0 top-full mt-1.5 w-60 z-50 overflow-hidden"
                  style={{background:"var(--surface)",border:"1px solid var(--color-border)",boxShadow:"var(--shadow-lg)",borderRadius:"var(--radius-md)"}}
                >
                  {SCHOOL_OPTIONS.map(s=>(
                    <button key={s.value}
                      onClick={()=>{setSelectedSchool(s.value);setSchoolDropdownOpen(false);}}
                      className="w-full px-5 py-2.5 text-left transition-colors hover:bg-[var(--bg-hover)]"
                      style={{fontSize:13,background:selectedSchool===s.value?"var(--accent-dim)":"transparent"}}
                    >
                      <div className="font-medium" style={{color:selectedSchool===s.value?"var(--el-water)":"var(--color-text-primary)"}}>{s.label}</div>
                      <div style={{fontSize:11,color:"var(--color-text-faint)"}}>{s.desc}</div>
                    </button>
                  ))}
                  <div style={{borderTop:"1px solid var(--color-border)"}}>
                    <button onClick={()=>{setSchoolDropdownOpen(false);handleReanalyze();}}
                      disabled={!birthInput||isLoading}
                      className="w-full px-5 py-2.5 font-medium disabled:opacity-50 transition-colors hover:bg-[var(--bg-hover)]"
                      style={{fontSize:13,color:"var(--el-water)"}}
                    >
                      以「{SCHOOL_OPTIONS.find(s=>s.value===selectedSchool)?.label}」重新分析
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button onClick={handleGenerateReport}
              className="flex items-center gap-1.5 px-3.5 py-2 font-medium border transition-colors"
              style={{
                fontSize:13,
                color:"var(--color-text-secondary)",
                background:"var(--surface)",
                borderColor:"var(--color-border)",
                borderRadius:"var(--radius-sm)",
              }}
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
          <section className="p-6 mb-6" style={{background:"var(--surface)",border:"1px solid var(--danger)",borderRadius:"var(--radius-md)",boxShadow:"var(--shadow-sm)"}}>
            <h3 className="font-bold mb-2" style={{fontSize:16,color:"var(--danger)"}}>分析失败</h3>
            <p style={{fontSize:15,color:"var(--color-text-secondary)"}}>{error||"未知错误"}</p>
          </section>
        )}

        {/* 骨架屏 */}
        {(isLoading || (status !== "completed" && status !== "failed" && !analysisResult)) && (
          <>
            {!isLoading && (
              <section className="p-5 mb-6 flex items-center gap-3" style={{background:"var(--surface)",border:"1px solid var(--color-border)",borderRadius:"var(--radius-md)",boxShadow:"var(--shadow-sm)"}}>
                <span className="w-2 h-2 shrink-0 animate-pulse" style={{background:"var(--el-water)"}} />
                <span style={{fontSize:15,color:"var(--color-text-muted)"}}>正在加载分析结果…</span>
              </section>
            )}
            <SkeletonCard /><SkeletonNarration />
          </>
        )}

        {/* ===== 分析结果（带 Tab 分页）===== */}
        {analysisResult ? (
          <>
            {/* 核心摘要条 — 始终可见 */}
            <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-6 gap-3 mb-8">
              {[
                {label:"旺衰",value:wangshuai?.verdict||"—"},
                {label:"格局",value:pattern?.pattern||"—"},
                {label:"用神",value:yongshen?.yongshen||"—",bg:"var(--el-wood-bg)"},
                {label:"喜神",value:(yongshen?.xishen||[]).join(" ")||"—",bg:"var(--el-water-bg)"},
                {label:"忌神",value:(yongshen?.jishen||[]).join(" ")||"—",bg:"var(--el-fire-bg)"},
              ].map((item:{label:string;value:string;bg?:string})=>(
                <div data-pill key={item.label} className="text-center p-4" style={{
                  background:item.bg||"var(--surface)",
                  border:"1px solid var(--color-border)",
                  borderRadius:"var(--radius-md)",
                  boxShadow:"var(--shadow-sm)",
                }}>
                  <div className="mb-1.5 font-semibold" style={{fontSize:12,color:"var(--color-text-muted)",fontFamily:"var(--font-serif)"}}>{item.label}</div>
                  <div className="font-bold" style={{fontSize:16}}>
                    {item.value.split("").map((ch,i)=>{
                      const wx = GAN_WUXING[ch] || ZHI_WUXING[ch] || (["金","木","水","火","土"].includes(ch) ? ch : "");
                      const color = wx ? WUXING_COLORS[wx] : "var(--color-text-primary)";
                      return (
                        <span key={i} style={{color,marginRight:1}}>{ch}</span>
                      );
                    })}
                  </div>
                </div>
              ))}
              {tiaohou?.has_tiaohou&&(
                <div data-pill className="text-center p-4 border" style={{background:"rgba(184,146,63,0.04)",borderColor:"var(--color-border)"}}>
                  <div className="mb-1.5 font-semibold uppercase tracking-wider" style={{fontSize:11,color:"var(--warning)",letterSpacing:"0.08em"}}>调候</div>
                  <div className="font-bold" style={{fontSize:15}}>
                    {(tiaohou.tiaohou_gan||[]).map((ch,i)=>{
                      const wx = GAN_WUXING[ch] || "";
                      const color = wx ? WUXING_COLORS[wx] : "var(--warning)";
                      return <span key={i} style={{color,marginRight:2}}>{ch}</span>;
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Tab 导航栏 — 分段控制器 */}
            <div role="tablist" aria-label="分析结果分区" onKeyDown={(e)=>{
              const idx=TABS.findIndex(t=>t.id===activeTab);
              if(e.key==="ArrowRight"||e.key==="ArrowDown"){e.preventDefault();setActiveTab(TABS[(idx+1)%TABS.length].id);}
              else if(e.key==="ArrowLeft"||e.key==="ArrowUp"){e.preventDefault();setActiveTab(TABS[(idx-1+TABS.length)%TABS.length].id);}
              else if(e.key==="Home"){e.preventDefault();setActiveTab(TABS[0].id);}
              else if(e.key==="End"){e.preventDefault();setActiveTab(TABS[TABS.length-1].id);}
            }} style={{
              display:"flex",
              gap:4,
              marginBottom:32,
              padding:4,
              background:"var(--surface-warm)",
              border:"1px solid var(--color-border)",
              borderRadius:"var(--radius-md)",
            }}>
              {TABS.map(tab=>{
                const isActive=activeTab===tab.id;
                return (
                  <button key={tab.id}
                    role="tab"
                    aria-selected={isActive}
                    tabIndex={isActive?0:-1}
                    onClick={()=>setActiveTab(tab.id)}
                    style={{
                      flex:1,
                      padding:"12px 8px",
                      fontSize:14,
                      fontWeight:600,
                      fontFamily:"var(--font-sans)",
                      color:isActive?"var(--color-ink)":"var(--color-text-muted)",
                      background:isActive?"var(--surface)":"transparent",
                      border:"none",
                      borderRadius:"var(--radius-sm)",
                      cursor:"pointer",
                      boxShadow:isActive?"var(--shadow-sm)":"none",
                      transition:"all 0.2s ease",
                    }}
                  >
                    <span aria-hidden="true" style={{marginRight:6,fontSize:16}}>{tab.icon}</span>{tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab 内容区 */}
            <div ref={tabContentRef} className="space-y-10">
              {/* Tab 1: 四柱命盘 */}
              {activeTab==="bazi"&&(
                <div className="space-y-10">
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
                    <section className="p-10 text-center border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
                      <span style={{fontSize:14,color:"var(--color-text-muted)"}}>关系图谱暂不可用</span>
                    </section>
                  }>
                    <RelationGraph result={analysisResult} />
                  </Safe>

                  {pattern?.reason && (
                    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)"}}>
                      <div style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}}>
                        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>格局判定依据</h3>
                        {pattern.confidence!==undefined&&(
                          <span className="tabular-nums ml-3" style={{fontSize:13,color:"var(--color-text-faint)"}}>{(pattern.confidence*100).toFixed(0)}%</span>
                        )}
                      </div>
                      <div className="p-7">
                        <p style={{fontSize:15,lineHeight:1.8,color:"var(--color-text-secondary)"}}>{pattern.reason}</p>
                        {pattern.confidence!==undefined&&(
                          <div className="mt-4 flex items-center gap-3">
                            <div className="flex-1 h-2 overflow-hidden" style={{background:"var(--bg-secondary)"}}>
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
                <div className="space-y-10">
                  <DayunTimeline result={analysisResult} />

                  <Safe fallback={
                    <section className="p-10 text-center border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
                      <span style={{fontSize:14,color:"var(--color-text-muted)"}}>K线图暂不可用</span>
                    </section>
                  }>
                    <LifeKlineChart analysisId={analysisId} />
                  </Safe>

                  <DailyFortuneCard analysisId={analysisId} />
                </div>
              )}

              {/* Tab 3: 宫位神煞 */}
              {activeTab==="detail"&&(
                <div className="space-y-10">
                  <GongweiPanel result={analysisResult} />
                </div>
              )}

              {/* Tab 4: 紫微斗数 */}
              {activeTab==="ziwei"&&(
                <div>
                  {analysisResult?.ziwei ? (
                    <section className="p-6 border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
                      <div style={{borderBottom:"2px solid var(--color-border-strong)",paddingBottom:12,marginBottom:16}}>
                        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>紫微斗数命盘</h3>
                      </div>
                      <ZiweiPanel data={analysisResult.ziwei as Record<string, unknown>} />
                    </section>
                  ) : (
                    <section className="p-6 border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
                      <p style={{fontSize:15,color:"var(--color-text-muted)"}}>紫微斗数数据不可用（需安装 iztro-py 依赖）</p>
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
                <div className="space-y-10" style={{maxWidth:860,marginLeft:"auto",marginRight:"auto"}}>
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
        ):null}

        {status==="completed"&&!analysisResult&&result?.status==="completed"&&(
          <section className="p-6 border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
            <p style={{fontSize:15,color:"var(--color-text-secondary)"}}>分析已完成，但无详细结果数据。</p>
          </section>
        )}
      </main>
    </div>
  );
}
