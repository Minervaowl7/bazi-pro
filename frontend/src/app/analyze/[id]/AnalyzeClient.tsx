"use client";

import { useEffect, useRef, useState, useCallback, useMemo, Component, ReactNode } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useAnalysisStore } from "@/stores/analysisStore";
import type { AnalysisResultData } from "@/lib/types";
import AnalysisProgress from "@/components/AnalysisProgress";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";
import { useOnlineStatus } from "@/lib/useOnlineStatus";
import { SCHOOL_OPTIONS_WITH_ALL } from "@/lib/constants";
import { gsap, useGSAP } from "@/lib/gsap";

import ActionBar from "@/components/analyze/ActionBar";
import ErrorState from "@/components/analyze/ErrorState";
import SummaryPills from "@/components/analyze/SummaryPills";
import { SkeletonCard, SkeletonNarration } from "@/components/analyze/Skeletons";
import { TAB_ICONS, MOBILE_TAB_ICONS, TABS, type TabId } from "@/components/analyze/tabConfig";
import BaziTab from "@/components/analyze/tabs/BaziTab";
import DayunTab from "@/components/analyze/tabs/DayunTab";
import DetailTab from "@/components/analyze/tabs/DetailTab";
import ZiweiTab from "@/components/analyze/tabs/ZiweiTab";
import DeepTab from "@/components/analyze/tabs/DeepTab";
import AnalysisTab from "@/components/analyze/tabs/AnalysisTab";
import ChatTab from "@/components/analyze/tabs/ChatTab";

const SCHOOL_OPTIONS = SCHOOL_OPTIONS_WITH_ALL;

/* ===== ErrorBoundary ===== */
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
            style={{ marginTop: 16, padding: "8px 20px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface)", cursor: "pointer", color: "var(--ink)" }}>重试</button>
        </section>
      );
    }
    return this.props.children;
  }
}
function Safe({ children, fallback }: FallbackProps) { return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>; }

/* ===== 按需加载 ===== */
const LifeReport = dynamic(() => import("@/components/LifeReport"), {
  ssr: false,
  loading: () => (
    <section className="card animate-pulse">
      <div className="border-b border-[var(--border)] px-6 py-4"><div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} /></div>
      <div className="p-6 space-y-3">{[1, 2, 3, 4, 5].map((i) => (<div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />))}</div>
    </section>
  ),
});

/* ===== 移动端底部 Tab 导航栏 ===== */
function MobileTabBar({ activeTab, onTabChange }: { activeTab: TabId; onTabChange: (tab: TabId) => void }) {
  return (
    <nav aria-label="移动端分析导航" className="fixed bottom-0 left-0 right-0 sm:hidden"
      style={{ zIndex: 45, background: "color-mix(in srgb, var(--surface) 92%, transparent)", backdropFilter: "blur(24px) saturate(1.3)", WebkitBackdropFilter: "blur(24px) saturate(1.3)", borderTop: "0.5px solid var(--border)", paddingBottom: "env(safe-area-inset-bottom, 0px)" }}>
      <div className="flex">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button key={tab.id} aria-selected={isActive} role="tab" onClick={() => onTabChange(tab.id)}
              className="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 transition-colors"
              style={{ minHeight: 52, color: isActive ? "var(--cinnabar)" : "var(--text-3)", background: isActive ? "var(--cinnabar-light)" : "transparent" }}>
              {MOBILE_TAB_ICONS[tab.id]}
              <span className="text-[10px] leading-tight" style={{ fontWeight: isActive ? 600 : 400, fontFamily: "var(--font-body)" }}>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

/* ===== 主页面 ===== */
export default function AnalyzeClient() {
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
  const setActiveTab = useCallback((tab: TabId) => { setActiveTabRaw(tab); router.replace(`/analyze/${analysisId}?tab=${tab}`, { scroll: false }); }, [router, analysisId]);
  const [selectedSchool, setSelectedSchool] = useState("ziping");
  const [schoolDropdownOpen, setSchoolDropdownOpen] = useState(false);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tabContentRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const isOnline = useOnlineStatus();
  const [loadTimeout, setLoadTimeout] = useState(false);

  const statusRef = useRef(status);
  useEffect(() => { statusRef.current = status; }, [status]);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setLoadTimeout(false); }, [analysisId]);
  useEffect(() => { if (!analysisId) return; const timer = setTimeout(() => { const s = statusRef.current; if (s !== "completed" && s !== "failed") setLoadTimeout(true); }, 15000); return () => clearTimeout(timer); }, [analysisId]);

  useEffect(() => {
    if (!analysisId) return;
    const fetchAndLog = (id: string) => { fetchResult(id).catch((err) => { console.error("[AnalyzePage] fetchResult failed:", err); if (useAnalysisStore.getState().status !== "failed") useAnalysisStore.setState({ status: "failed", error: err instanceof Error ? err.message : "获取分析结果失败" }); }); };
    if (analysisId !== prevIdRef.current) { prevIdRef.current = analysisId; if (analysisId !== storeAnalysisId) { reset(); fetchAndLog(analysisId); } }
    else if (status === "idle") { fetchAndLog(analysisId); }
  }, [analysisId, status, storeAnalysisId, fetchResult, reset]);

  useEffect(() => {
    if (!analysisId || status !== "polling") return;
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    pollTimerRef.current = setInterval(() => { const s = statusRef.current; if (s === "completed" || s === "failed") { if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; } return; } fetchResult(analysisId).catch((err) => console.warn("[poll]", err)); }, 5000);
    return () => { if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; } };
  }, [analysisId, status, fetchResult]);

  useEffect(() => { if (!schoolDropdownOpen) return; const handler = () => setSchoolDropdownOpen(false); document.addEventListener("click", handler); return () => document.removeEventListener("click", handler); }, [schoolDropdownOpen]);

  const handleReanalyze = useCallback(async () => { if (!birthInput) return; try { const newId = await startAnalysis({ ...birthInput, school: selectedSchool }); router.push(`/analyze/${newId}`); } catch (err) { console.error("[AnalyzePage] reanalyze failed:", err); } }, [birthInput, selectedSchool, startAnalysis, router]);
  const handleRetryFetch = useCallback(() => { useAnalysisStore.setState({ status: "idle" }); fetchResult(analysisId).catch(() => {}); }, [analysisId, fetchResult]);

  const analysisResult = result?.result as AnalysisResultData | undefined;
  const narration = (result as Record<string, unknown> | null)?.narration as Record<string, unknown> | undefined;
  const isLoading = status === "submitting" || status === "streaming" || status === "polling";

  const ziweiParams = useMemo(() => {
    if (!birthInput?.阳历) return undefined;
    const parts = birthInput.阳历.split(/[\sT]/);
    const solar_date = parts[0];
    let hour = 0;
    if (parts[1]) { const h = parseInt(parts[1].split(":")[0], 10); if (!isNaN(h)) hour = h; }
    return { solar_date, hour, gender: birthInput.性别 === "女" ? 0 : 1 };
  }, [birthInput]);

  const wangshuai = analysisResult?.strength?.wangshuai;
  const pattern = analysisResult?.pattern;
  const yongshen = analysisResult?.yongshen;
  const tiaohou = analysisResult?.tiaohou;
  const schoolAnalyses = analysisResult?.school_analyses as Record<string, unknown> | undefined;
  const currentSchool = (analysisResult?.school as string) || "ziping";
  const isCompareMode = currentSchool === "all";

  /* GSAP 动画 */
  useGSAP(() => { if (!analysisResult || prefersReducedMotion) return; const t = gsap.utils.toArray("[data-pill]"); if (t.length) gsap.from(t, { y: -20, autoAlpha: 0, stagger: 0.08, duration: 0.5, ease: "back.out(1.2)" }); }, { scope: containerRef, dependencies: [analysisResult] });
  useGSAP(() => { if (!analysisResult || prefersReducedMotion) return; const t = gsap.utils.toArray("[data-action-bar]"); if (t.length) gsap.from(t, { x: -30, autoAlpha: 0, duration: 0.5 }); }, { scope: containerRef, dependencies: [analysisResult] });
  useGSAP(() => { if (prefersReducedMotion || !tabContentRef.current) return; gsap.from(tabContentRef.current, { autoAlpha: 0, y: 20, duration: 0.4 }); }, { scope: containerRef, dependencies: [activeTab], revertOnUpdate: true });

  return (
    <ErrorBoundary fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
        <section className="card p-8 text-center" style={{ maxWidth: 500 }}>
          <h3 style={{ color: "var(--danger)", fontSize: 18, fontWeight: 700, marginBottom: 8 }}>页面渲染出错</h3>
          <p style={{ color: "var(--text-2)", fontSize: 14, marginBottom: 16 }}>分析结果渲染时发生异常，请重试或返回首页。</p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
            <button onClick={() => window.location.reload()} style={{ padding: "10px 24px", borderRadius: 10, border: "1px solid var(--border)", background: "var(--surface)", cursor: "pointer", color: "var(--ink)", fontSize: 14 }}>重试</button>
            <button onClick={() => { window.location.href = "/"; }} style={{ padding: "10px 24px", borderRadius: 10, border: "none", background: "var(--scholar-blue)", cursor: "pointer", color: "#fff", fontSize: 14 }}>返回首页</button>
          </div>
        </section>
      </div>
    }>
    <div ref={containerRef} className="min-h-screen" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-[960px] mx-auto pb-20 sm:pb-10 px-4 sm:px-6">

        {/* 操作栏 */}
        {analysisResult && (
          <ActionBar analysisId={analysisId} result={analysisResult} narration={narration} currentSchool={currentSchool}
            selectedSchool={selectedSchool} setSelectedSchool={setSelectedSchool} schoolDropdownOpen={schoolDropdownOpen}
            setSchoolDropdownOpen={setSchoolDropdownOpen} isLoading={isLoading} birthInput={birthInput}
            onReanalyze={handleReanalyze} onGenerateReport={() => router.push(`/report/${analysisId}`)} schoolOptions={SCHOOL_OPTIONS} />
        )}

        {isLoading && <AnalysisProgress />}

        {/* 网络断开提示 */}
        {!isOnline && (
          <section className="flex items-center gap-3 px-4 py-3 mb-6 rounded-lg animate-fade-in" style={{ background: "rgba(197,165,90,0.10)", border: "1px solid rgba(197,165,90,0.25)" }} role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="1" y1="1" x2="23" y2="23" /><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" /><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" /><path d="M10.71 5.05A16 16 0 0 1 22.56 9" /><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" /><path d="M8.53 16.11a6 6 0 0 1 6.95 0" /><line x1="12" y1="20" x2="12.01" y2="20" /></svg>
            <div><p className="text-sm font-medium" style={{ color: "var(--warning)" }}>网络连接已断开</p><p className="text-xs mt-0.5" style={{ color: "var(--text-3)" }}>部分功能可能无法正常使用，请检查网络后刷新页面</p></div>
          </section>
        )}

        {/* 分析失败 */}
        {status === "failed" && (
          <ErrorState error={error || "未知错误"} birthInput={birthInput} selectedSchool={selectedSchool}
            onReanalyze={(input, school) => { startAnalysis({ ...input, school } as never).catch(() => {}); }}
            onRetryFetch={handleRetryFetch} />
        )}

        {/* 骨架屏 */}
        {(isLoading || (status !== "completed" && status !== "failed" && !analysisResult)) && (
          <>
            {loadTimeout ? (
              <section className="card p-6 mb-6" style={{ border: "1px solid var(--warning)" }}>
                <h3 className="font-bold text-base mb-2" style={{ color: "var(--warning)" }}>加载缓慢</h3>
                <p className="text-[15px] mb-4" style={{ color: "var(--text-2)" }}>分析结果加载已超过 15 秒，可能是首次启动需要加载古籍索引，请耐心等待或重试。</p>
                <button onClick={() => { setLoadTimeout(false); useAnalysisStore.setState({ status: "idle" }); }} className="px-4 py-2 rounded-lg text-sm font-medium" style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--ink)", cursor: "pointer" }}>重新加载</button>
              </section>
            ) : !isLoading ? (
              <section className="card p-5 mb-6 flex items-center gap-3"><span className="w-2 h-2 shrink-0 animate-pulse" style={{ background: "var(--wx-water)" }} /><span className="text-[15px]" style={{ color: "var(--text-3)" }}>正在加载分析结果…</span></section>
            ) : null}
            {!loadTimeout && <><SkeletonCard /><SkeletonNarration /></>}
          </>
        )}

        {/* ===== 分析结果 ===== */}
        {analysisResult ? (
          <Safe fallback={<section className="card p-8 text-center"><h3 className="font-bold text-base mb-2" style={{ color: "var(--danger)" }}>渲染出错</h3><p className="text-[15px]" style={{ color: "var(--text-2)" }}>分析结果渲染时发生异常，请刷新页面重试。</p></section>}>
          <>
            <SummaryPills wangshuaiVerdict={wangshuai?.verdict} patternName={pattern?.pattern} yongshen={yongshen?.yongshen}
              xishen={yongshen?.xishen} jishen={yongshen?.jishen} hasTiaohou={tiaohou?.has_tiaohou} tiaohouGan={tiaohou?.tiaohou_gan} />

            {analysisResult?.life_report && <LifeReport content={analysisResult.life_report as string} isLlmGenerated={true} />}
            {!analysisResult?.life_report && analysisResult?.llm_overview && <LifeReport content={analysisResult.llm_overview as string} isLlmGenerated={true} />}

            {/* Tab 导航栏 */}
            <div className="relative mb-8 hidden sm:block">
              <div role="tablist" aria-label="分析结果分区" className="flex gap-0.5 p-[3px] overflow-auto scrollbar-none"
                style={{ background: "var(--surface-2)", border: "0.5px solid var(--border)", borderRadius: "var(--r)" }}
                onKeyDown={(e) => { const idx = TABS.findIndex(t => t.id === activeTab); if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); setActiveTab(TABS[(idx + 1) % TABS.length].id); } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); setActiveTab(TABS[(idx - 1 + TABS.length) % TABS.length].id); } else if (e.key === "Home") { e.preventDefault(); setActiveTab(TABS[0].id); } else if (e.key === "End") { e.preventDefault(); setActiveTab(TABS[TABS.length - 1].id); } }}>
                {TABS.map((tab) => { const isActive = activeTab === tab.id; return (
                  <button key={tab.id} id={`tab-${tab.id}`} role="tab" aria-selected={isActive} tabIndex={isActive ? 0 : -1} onClick={() => setActiveTab(tab.id)}
                    className="flex-1 py-2.5 px-1.5 text-[13px] text-center rounded-md cursor-pointer relative transition-all duration-150"
                    style={{ fontWeight: isActive ? 600 : 500, fontFamily: "var(--font-body)", color: isActive ? "var(--ink)" : "var(--text-3)", background: isActive ? "var(--surface)" : "transparent", boxShadow: isActive ? "var(--shadow-xs)" : "none" }}>
                    <span aria-hidden="true" className="inline-flex items-center" style={{ marginRight: 5 }}>{TAB_ICONS[tab.id]}</span>{tab.label}
                  </button>
                ); })}
              </div>
              <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none sm:hidden" style={{ background: "linear-gradient(to left, var(--surface-2), transparent)" }} />
            </div>

            {/* Tab 内容区 */}
            <div ref={tabContentRef} className="space-y-6 sm:space-y-10">
              <div role="tabpanel" aria-labelledby="tab-bazi" style={activeTab === "bazi" ? undefined : { visibility: "hidden", height: 0, overflow: "hidden", position: "absolute" }}><BaziTab result={analysisResult} /></div>
              <div role="tabpanel" aria-labelledby="tab-dayun" style={{ display: activeTab === "dayun" ? "block" : "none" }}><DayunTab result={analysisResult} analysisId={analysisId} ziweiParams={ziweiParams} /></div>
              <div role="tabpanel" aria-labelledby="tab-detail" style={activeTab === "detail" ? undefined : { visibility: "hidden", height: 0, overflow: "hidden", position: "absolute" }}><DetailTab result={analysisResult} /></div>
              <div role="tabpanel" aria-labelledby="tab-ziwei" style={{ display: activeTab === "ziwei" ? "block" : "none" }}><ZiweiTab result={analysisResult} /></div>
              <div role="tabpanel" aria-labelledby="tab-deep" style={{ display: activeTab === "deep" ? "block" : "none" }}><DeepTab result={analysisResult} narration={narration} /></div>
              <div role="tabpanel" aria-labelledby="tab-analysis" style={{ display: activeTab === "analysis" ? "block" : "none" }}><AnalysisTab result={analysisResult} narration={narration} isCompareMode={isCompareMode} schoolAnalyses={schoolAnalyses} /></div>
              <div role="tabpanel" aria-labelledby="tab-chat" style={{ display: activeTab === "chat" ? "block" : "none" }}><ChatTab analysisId={analysisId} school={currentSchool === "all" ? "ziping" : currentSchool} /></div>
            </div>

            <MobileTabBar activeTab={activeTab} onTabChange={setActiveTab} />
          </>
          </Safe>
        ) : null}

        {status === "completed" && !analysisResult && result?.status === "completed" && (
          <section className="card p-6"><p className="text-[15px]" style={{ color: "var(--text-2)" }}>分析已完成，但无详细结果数据。</p></section>
        )}
      </div>
    </div>
    </ErrorBoundary>
  );
}
