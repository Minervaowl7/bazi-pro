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
import ZiweiPanel from "@/components/ZiweiPanel";
import ChatPanel from "@/components/ChatPanel";
import ExportPanel from "@/components/ExportPanel";
import { SCHOOL_OPTIONS_WITH_ALL, WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";

import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import ChartQuality, { type ChartQualityData } from "@/components/ChartQuality";

function LlmOverview({ content }: { content: string }) {
  return (
    <section style={{ background: "var(--surface)", border: "1px solid var(--color-border)", boxShadow: "var(--shadow-sm)", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ borderBottom: "1px solid var(--color-border-subtle)", padding: "18px 28px" }} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, var(--color-scholar-blue), #1a365d)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 8px rgba(45,62,95,0.2)" }}>
            <span style={{ fontSize: 15, color: "#fff" }}>✦</span>
          </div>
          <div>
            <h3 className="font-bold" style={{ fontSize: 16, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)", letterSpacing: "0.02em" }}>AI 命盘总览</h3>
            <p style={{ fontSize: 12, color: "var(--color-text-faint)", marginTop: 2 }}>基于确定性计算数据 · LLM 深度解读</p>
          </div>
        </div>
      </div>
      <div className="llm-overview-body" style={{ padding: "28px", color: "var(--color-text-secondary)", lineHeight: 1.85, fontSize: 15 }}>
        <ReactMarkdown remarkPlugins={[RemarkGfm]}>{content}</ReactMarkdown>
      </div>
      <style jsx>{`
        .llm-overview-body :global(h2) { color: var(--color-scholar-blue); font-size: 1.2rem; font-weight: 700; font-family: var(--font-serif); margin-top: 1.8rem; margin-bottom: 0.8rem; padding-bottom: 0.4rem; border-bottom: 1px solid var(--color-border-subtle); }
        .llm-overview-body :global(h2:first-child) { margin-top: 0; }
        .llm-overview-body :global(h3) { color: var(--color-text-primary); font-size: 1.05rem; font-weight: 600; margin-top: 1.2rem; margin-bottom: 0.5rem; }
        .llm-overview-body :global(p) { margin-bottom: 0.7rem; }
        .llm-overview-body :global(strong) { color: var(--color-text-primary); font-weight: 700; }
        .llm-overview-body :global(ul), .llm-overview-body :global(ol) { padding-left: 1.3rem; margin: 0.5rem 0; }
        .llm-overview-body :global(li) { margin: 0.3rem 0; line-height: 1.7; }
        .llm-overview-body :global(blockquote) { border-left: 3px solid var(--color-scholar-blue); padding-left: 1rem; opacity: 0.85; margin: 0.7rem 0; }
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

  return (
    <div style={{minHeight:"100vh",background:"var(--background)"}}>
      <main style={{width:"100%",paddingTop:72,paddingBottom:40,paddingLeft:20,paddingRight:20}}>

        {/* ===== 操作栏 ===== */}
        {analysisResult && (
          <div className="flex items-center gap-2.5 mb-7 flex-wrap">
            <div className="relative">
              <button
                onClick={(e)=>{e.stopPropagation();setSchoolDropdownOpen(!schoolDropdownOpen);}}
                className="flex items-center gap-1.5 px-3.5 py-2 font-medium border transition-colors"
                style={{
                  fontSize:13,
                  color:"var(--color-text-secondary)",
                  background:"var(--surface)",
                  borderColor:"var(--color-border)",
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
                  style={{background:"var(--surface)",border:"1px solid var(--color-border)",boxShadow:"var(--shadow-lg)"}}
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
          <section className="p-6 mb-6 border" style={{background:"var(--surface)",borderColor:"var(--danger)"}}>
            <h3 className="font-bold mb-2" style={{fontSize:16,color:"var(--danger)"}}>分析失败</h3>
            <p style={{fontSize:15,color:"var(--color-text-secondary)"}}>{error||"未知错误"}</p>
          </section>
        )}

        {/* 骨架屏 */}
        {(isLoading || (status !== "completed" && status !== "failed" && !analysisResult)) && (
          <>
            {!isLoading && (
              <section className="p-5 mb-6 flex items-center gap-3 border" style={{background:"var(--surface)",borderColor:"var(--color-border)"}}>
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
                {label:"用神",value:yongshen?.yongshen||"—",bg:"rgba(45,125,91,0.06)"},
                {label:"喜神",value:(yongshen?.xishen||[]).join(" ")||"—",bg:"rgba(53,94,133,0.05)"},
                {label:"忌神",value:(yongshen?.jishen||[]).join(" ")||"—",bg:"rgba(196,60,44,0.06)"},
              ].map((item:{label:string;value:string;bg?:string})=>(
                <div key={item.label} className="text-center p-4 border" style={{
                  background:item.bg||"var(--surface)",
                  borderColor:"var(--color-border)",
                }}>
                  <div className="mb-1.5 font-semibold uppercase tracking-wider" style={{fontSize:11,color:"var(--color-text-faint)",letterSpacing:"0.08em"}}>{item.label}</div>
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
                <div className="text-center p-4 border" style={{background:"rgba(184,146,63,0.04)",borderColor:"var(--color-border)"}}>
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
              background:"var(--bg-secondary)",
              border:"1px solid var(--color-border)",
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
                      cursor:"pointer",
                      boxShadow:isActive?"0 1px 3px rgba(28,25,23,0.08)":"none",
                    }}
                  >
                    <span aria-hidden="true" style={{marginRight:6,fontSize:16}}>{tab.icon}</span>{tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab 内容区 */}
            <div className="space-y-10">
              {/* Tab 1: 四柱命盘 */}
              {activeTab==="bazi"&&(
                <div className="space-y-10 stagger-in">
                  <BaziChartCard result={analysisResult} />

                  {analysisResult?.chart_quality && <ChartQuality data={analysisResult.chart_quality as unknown as ChartQualityData} />}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <StrengthSlider
                      verdict={wangshuai?.verdict}
                      dayMaster={analysisResult?.validation?.day_master}
                      deling={analysisResult?.strength?.deling}
                      dedi={analysisResult?.strength?.dedi}
                      deshi={analysisResult?.strength?.deshi}
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
                <div className="space-y-10 stagger-in">
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
                <div className="space-y-10 stagger-in">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <GongweiPanel result={analysisResult} />
                    <ShenShaPanel result={analysisResult} />
                  </div>
                </div>
              )}

              {/* Tab 4: 紫微斗数 */}
              {activeTab==="ziwei"&&(
                <div className="stagger-in">
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

              {/* Tab 5: 流派解读 */}
              {activeTab==="analysis"&&(
                <div className="space-y-10 stagger-in" style={{maxWidth:860,marginLeft:"auto",marginRight:"auto"}}>
                  {analysisResult?.llm_overview && <LlmOverview content={analysisResult.llm_overview as string} />}
                  {isCompareMode&&schoolAnalyses?<SchoolComparePanel schoolAnalyses={schoolAnalyses}/>:<SchoolPanel result={analysisResult} narration={narration}/>}
                </div>
              )}

              {/* Tab 5: 命理问答 */}
              {activeTab==="chat"&&(
                <div className="stagger-in">
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
