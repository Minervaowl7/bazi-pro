"use client";

import { useEffect, useRef, useState, useCallback, useMemo, Component, ReactNode } from "react";
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
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";
import { useOnlineStatus } from "@/lib/useOnlineStatus";
import { SCHOOL_OPTIONS_WITH_ALL, WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";
import { gsap, useGSAP } from "@/lib/gsap";
import { Accordion, AccordionItem } from "@/components/ui/Accordion";

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

/* ===== 按需加载：面板组件（减少首屏 JS 体积）===== */
function PanelSkeleton({ title, lines = 3 }: { title?: string; lines?: number }) {
  return (
    <section className="card animate-pulse">
      {title && (
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="h-5 w-24 rounded" style={{ background: "var(--surface-2)" }} />
        </div>
      )}
      <div className="p-6 space-y-3">
        {Array.from({ length: lines }, (_, i) => (
          <div key={i} className="h-4 rounded" style={{ background: "var(--surface-2)", width: `${85 - i * 10}%` }} />
        ))}
      </div>
    </section>
  );
}

const SchoolPanel = dynamic(() => import("@/components/SchoolPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="流派解读" />,
});

const SchoolComparePanel = dynamic(() => import("@/components/SchoolComparePanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="流派对比" lines={5} />,
});

const DayunTimeline = dynamic(() => import("@/components/DayunTimeline"), {
  ssr: false,
  loading: () => <PanelSkeleton title="大运流年" lines={4} />,
});

const GongweiPanel = dynamic(() => import("@/components/GongweiPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="宫位分析" />,
});

const ShenShaPanel = dynamic(() => import("@/components/ShenShaPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="神煞查盘" />,
});

const DimensionAnalysisPanel = dynamic(() => import("@/components/DimensionAnalysisPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="维度分析" />,
});

const ZiweiPanel = dynamic(() => import("@/components/ZiweiPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="紫微斗数" lines={6} />,
});

const ChatPanel = dynamic(() => import("@/components/ChatPanel"), {
  ssr: false,
  loading: () => <PanelSkeleton title="命理问答" lines={2} />,
});

const ExportPanel = dynamic(() => import("@/components/ExportPanel"), {
  ssr: false,
});

const LifeReport = dynamic(() => import("@/components/LifeReport"), {
  ssr: false,
  loading: () => <PanelSkeleton title="命书" lines={5} />,
});

const LlmOverview = dynamic(() => import("@/components/LlmOverview"), {
  ssr: false,
  loading: () => <PanelSkeleton title="AI 总览" lines={4} />,
});

/* Tab 图标 — 轻量内联 SVG，strokeWidth=1.5，14x14 视口 */
const TAB_ICONS: Record<string, React.JSX.Element> = {
  bazi: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>,
  dayun: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  detail: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>,
  ziwei: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  deep: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4"/><path d="M12 19v4"/><path d="M1 12h4"/><path d="M19 12h4"/></svg>,
  analysis: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>,
  chat: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
};

const TABS = [
  { id: "bazi", label: "四柱命盘" },
  { id: "dayun", label: "大运流年" },
  { id: "detail", label: "宫位神煞" },
  { id: "ziwei", label: "紫微斗数" },
  { id: "deep", label: "深度分析" },
  { id: "analysis", label: "流派解读" },
  { id: "chat", label: "命理问答" },
] as const;
type TabId = typeof TABS[number]["id"];

/* 移动端底部 Tab 图标（24x24 视口，strokeWidth=1.5，比桌面端更大） */
const MOBILE_TAB_ICONS: Record<string, React.JSX.Element> = {
  bazi: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>,
  dayun: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  detail: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>,
  ziwei: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  deep: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4"/><path d="M12 19v4"/><path d="M1 12h4"/><path d="M19 12h4"/></svg>,
  analysis: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>,
  chat: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
};

/** 移动端底部固定 Tab 导航栏 */
function MobileTabBar({ activeTab, onTabChange }: { activeTab: TabId; onTabChange: (tab: TabId) => void }) {
  return (
    <nav
      aria-label="移动端分析导航"
      className="fixed bottom-0 left-0 right-0 sm:hidden"
      style={{
        zIndex: 45,
        background: "color-mix(in srgb, var(--surface) 92%, transparent)",
        backdropFilter: "blur(24px) saturate(1.3)",
        WebkitBackdropFilter: "blur(24px) saturate(1.3)",
        borderTop: "0.5px solid var(--border)",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
      }}
    >
      <div className="flex">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              aria-selected={isActive}
              role="tab"
              onClick={() => onTabChange(tab.id)}
              className="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 transition-colors"
              style={{
                minHeight: 52,
                color: isActive ? "var(--cinnabar)" : "var(--text-3)",
                background: isActive ? "var(--cinnabar-light)" : "transparent",
              }}
            >
              {MOBILE_TAB_ICONS[tab.id]}
              <span
                className="text-[10px] leading-tight"
                style={{
                  fontWeight: isActive ? 600 : 400,
                  fontFamily: "var(--font-body)",
                }}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function SkeletonCard() {
  return (
    <section className="card p-7 mb-6 animate-pulse">
      <div className="h-5 w-32 mb-6 rounded" style={{ background: "var(--surface-2)" }} />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
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
  const isOnline = useOnlineStatus();
  const [loadTimeout, setLoadTimeout] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);

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
        if (useAnalysisStore.getState().status !== "failed") {
          useAnalysisStore.setState({
            status: "failed",
            error: err instanceof Error ? err.message : "获取分析结果失败",
          });
        }
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
      fetchResult(analysisId).catch((err) => console.warn("[poll]", err));
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

  // 从 birthInput 提取紫微排盘参数
  const ziweiParams = useMemo(() => {
    if (!birthInput?.阳历) return undefined;
    const solar = birthInput.阳历;
    // 解析 "YYYY-MM-DD HH:MM" 或 "YYYY-MM-DD HH"
    const parts = solar.split(/[\sT]/);
    const solar_date = parts[0];
    let hour = 0;
    if (parts[1]) {
      const h = parseInt(parts[1].split(":")[0], 10);
      if (!isNaN(h)) hour = h;
    }
    const gender = birthInput.性别 === "女" ? 0 : 1;
    return { solar_date, hour, gender };
  }, [birthInput]);

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
      <div className="w-full max-w-[960px] mx-auto pb-20 sm:pb-10 px-4 sm:px-6">

        {/* ===== 操作栏 ===== */}
        {analysisResult && (
          <div data-action-bar className="flex items-center gap-1.5 sm:gap-2.5 mb-5 sm:mb-7 flex-wrap">
            <div className="relative">
              <button
                onClick={(e)=>{e.stopPropagation();setSchoolDropdownOpen(!schoolDropdownOpen);}}
                className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-[12px] sm:text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
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
                  className="card absolute left-0 top-full mt-1.5 w-60 overflow-hidden"
                  style={{ zIndex: "var(--z-dropdown)" }}
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
              className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-[12px] sm:text-[13px] font-medium border border-[var(--border)] rounded-lg transition-colors"
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

        {/* 网络断开提示 */}
        {!isOnline && (
          <section
            className="flex items-center gap-3 px-4 py-3 mb-6 rounded-lg animate-fade-in"
            style={{
              background: "rgba(197,165,90,0.10)",
              border: "1px solid rgba(197,165,90,0.25)",
            }}
            role="alert"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
              <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <line x1="12" y1="20" x2="12.01" y2="20" />
            </svg>
            <div>
              <p className="text-sm font-medium" style={{ color: "var(--warning)" }}>
                网络连接已断开
              </p>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-3)" }}>
                部分功能可能无法正常使用，请检查网络后刷新页面
              </p>
            </div>
          </section>
        )}

        {/* 分析失败 */}
        {status==="failed" && (() => {
          const errorMsg = error || "未知错误";
          const isLlmError = errorMsg.includes("LLM") && (errorMsg.includes("未配置") || errorMsg.includes("503") || errorMsg.includes("not configured") || errorMsg.includes("不可用"));
          const isNetworkError = errorMsg.includes("fetch") || errorMsg.includes("network") || errorMsg.includes("网络") || errorMsg.includes("Failed to fetch") || errorMsg.includes("ECONNREFUSED");
          const handleRetry = () => {
            setShowErrorDetails(false);
            if (birthInput) {
              startAnalysis({ ...birthInput, school: selectedSchool }).catch(() => {});
            } else {
              useAnalysisStore.setState({ status: "idle" });
              fetchResult(analysisId).catch(() => {});
            }
          };
          return (
            <section
              className="card mb-6 overflow-hidden animate-fade-in"
              style={{ border: "1px solid var(--danger)" }}
              role="alert"
            >
              {/* 顶部色带 */}
              <div style={{ height: 3, background: "linear-gradient(90deg, var(--danger), var(--warning))" }} />
              <div className="p-6">
                <div className="flex items-start gap-4">
                  {/* 错误图标 */}
                  <div
                    className="shrink-0 flex items-center justify-center rounded-full"
                    style={{
                      width: 40, height: 40,
                      background: "rgba(201,100,66,0.10)",
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-base mb-1" style={{ color: "var(--danger)", fontFamily: "var(--font-display)" }}>
                      {isNetworkError ? "网络连接失败" : isLlmError ? "智能解读暂不可用" : "分析失败"}
                    </h3>
                    <p className="text-sm leading-relaxed" style={{ color: "var(--text-2)" }}>
                      {isNetworkError
                        ? "无法连接到分析服务，请检查网络连接后重试。"
                        : isLlmError
                          ? "LLM 智能解读服务未配置或暂时不可用，但核心命理计算（确定性推导）已完成，您仍可查看四柱命盘、旺衰、格局、用神等确定性分析结果。"
                          : errorMsg
                      }
                    </p>

                    {/* LLM 降级提示 */}
                    {isLlmError && (
                      <div
                        className="mt-3 flex items-start gap-2.5 px-3 py-2.5 rounded-md text-xs leading-relaxed"
                        style={{
                          background: "rgba(46,92,138,0.06)",
                          border: "1px solid rgba(46,92,138,0.12)",
                          color: "var(--text-2)",
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--wx-water)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="16" x2="12" y2="12" />
                          <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        <span>
                          核心计算结果（十神、旺衰、格局、用神、调候、刑冲合害等）均为确定性推导，不依赖 LLM。
                          如需智能解读，请在服务端配置 <code className="text-[11px] px-1 py-0.5 rounded" style={{ background: "var(--surface-2)", color: "var(--ink)" }}>LLM_API_KEY</code> 环境变量。
                        </span>
                      </div>
                    )}

                    {/* 操作按钮 */}
                    <div className="flex items-center gap-2.5 mt-4">
                      <button
                        onClick={handleRetry}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-[0.97]"
                        style={{
                          background: "var(--cinnabar)",
                          color: "#fff",
                          cursor: "pointer",
                          boxShadow: "0 1px 4px rgba(201,100,66,0.2)",
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="23 4 23 10 17 10" />
                          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                        </svg>
                        重新分析
                      </button>
                      <button
                        onClick={() => setShowErrorDetails(!showErrorDetails)}
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors"
                        style={{
                          color: "var(--text-3)",
                          background: "var(--surface-2)",
                          cursor: "pointer",
                        }}
                      >
                        <svg
                          width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                          style={{ transform: showErrorDetails ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                        {showErrorDetails ? "隐藏详情" : "查看详情"}
                      </button>
                    </div>

                    {/* 错误详情折叠面板 */}
                    {showErrorDetails && (
                      <div
                        className="mt-3 px-3 py-2.5 rounded-md text-xs font-mono leading-relaxed overflow-x-auto animate-fade-in"
                        style={{
                          background: "var(--surface-2)",
                          border: "1px solid var(--border-subtle)",
                          color: "var(--text-3)",
                          maxHeight: 160,
                          overflowY: "auto",
                          wordBreak: "break-all",
                        }}
                      >
                        {errorMsg}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>
          );
        })()}

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
            <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 mb-6 sm:mb-8">
              {[
                {label:"旺衰",value:wangshuai?.verdict||"—"},
                {label:"格局",value:pattern?.pattern||"—"},
                {label:"用神",value:yongshen?.yongshen||"—",bg:"var(--wx-wood-bg)"},
                {label:"喜神",value:(yongshen?.xishen||[]).join(" ")||"—",bg:"var(--wx-water-bg)"},
                {label:"忌神",value:(yongshen?.jishen||[]).join(" ")||"—",bg:"var(--wx-fire-bg)"},
              ].map((item:{label:string;value:string;bg?:string})=>(
                <div data-pill key={item.label} className="card text-center relative overflow-hidden p-3 sm:p-4 px-2 sm:px-3" style={{ background: item.bg || "var(--surface)" }}>
                  {/* 顶部金线 */}
                  <div style={{
                    position:"absolute",top:0,left:"20%",right:"20%",height:1,
                    background:"linear-gradient(90deg,transparent,var(--gold),transparent)",
                    opacity:0.4,
                  }} />
                  <div className="mb-1 sm:mb-1.5 text-[10px] sm:text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--text-3)" }}>{item.label}</div>
                  <div className="text-base sm:text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
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
                <div data-pill className="card text-center relative overflow-hidden p-3 sm:p-4 px-2 sm:px-3" style={{ background: "rgba(197,165,90,0.04)" }}>
                  <div className="absolute top-0 left-[20%] right-[20%] h-px opacity-40" style={{ background: "linear-gradient(90deg,transparent,var(--gold),transparent)" }} />
                  <div className="mb-1 sm:mb-1.5 text-[10px] sm:text-[11px] uppercase tracking-[0.06em]" style={{ color: "var(--gold)" }}>调候</div>
                  <div className="text-base sm:text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
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

            {/* Tab 导航栏 — 分段控制器（桌面端显示，移动端由底部 Tab 替代） */}
            <div className="relative mb-8 hidden sm:block">
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
                    <span aria-hidden="true" className="inline-flex items-center" style={{marginRight:5}}>{TAB_ICONS[tab.id]}</span>{tab.label}
                  </button>
                );
              })}
            </div>
            {/* 右侧滚动提示渐变 */}
            <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none sm:hidden" style={{ background: "linear-gradient(to left, var(--surface-2), transparent)" }} />
            </div>

            {/* Tab 内容区（桌面端直接展示，移动端用 AccordionItem 包裹实现可折叠） */}
            <div ref={tabContentRef} className="space-y-6 sm:space-y-10">
              {/* Tab 1: 四柱命盘 */}
              {activeTab==="bazi"&&(
                <>
                  {/* 桌面端：直接渲染 */}
                  <div className="hidden sm:block">
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
                  {/* 移动端：AccordionItem 可折叠 */}
                  <div className="sm:hidden">
                    <Accordion>
                      <AccordionItem title="四柱命盘" defaultOpen>
                        <BaziChartCard result={analysisResult} />
                        {analysisResult?.chart_quality && <ChartQuality data={analysisResult.chart_quality as unknown as ChartQualityData} />}
                      </AccordionItem>
                      <AccordionItem title="旺衰 & 十神" defaultOpen>
                        <StrengthSlider strength={analysisResult?.strength} dayMaster={analysisResult?.validation?.day_master} />
                        <div className="mt-4"><ShishenEnergyChart result={analysisResult} /></div>
                      </AccordionItem>
                      <AccordionItem title="关系图谱">
                        <Safe fallback={<p className="text-sm py-4 text-center" style={{ color: "var(--text-3)" }}>关系图谱暂不可用</p>}>
                          <RelationGraph result={analysisResult} />
                        </Safe>
                      </AccordionItem>
                      {pattern?.reason && (
                        <AccordionItem title="格局判定依据">
                          <p className="text-[14px] leading-relaxed" style={{ color: "var(--text-2)" }}>{pattern.reason}</p>
                          {pattern.confidence!==undefined&&(
                            <div className="mt-3 flex items-center gap-3">
                              <div className="flex-1 h-2 overflow-hidden" style={{background:"var(--surface-2)"}}>
                                <div className="h-full" style={{
                                  width:`${Math.min(pattern.confidence*100,100)}%`,
                                  transition:"width 0.7s",
                                  background:pattern.confidence>=0.8?"var(--success)":pattern.confidence>=0.6?"var(--warning)":"var(--danger)",
                                }}/>
                              </div>
                              <span className="text-xs tabular-nums" style={{color:"var(--text-4)"}}>{(pattern.confidence*100).toFixed(0)}%</span>
                            </div>
                          )}
                        </AccordionItem>
                      )}
                    </Accordion>
                  </div>
                </>
              )}

              {/* Tab 2: 大运流年 */}
              {activeTab==="dayun"&&(
                <>
                  <div className="hidden sm:block">
                    <DayunTimeline result={analysisResult} />
                    <Safe fallback={<section className="card p-10 text-center"><span className="text-sm" style={{ color: "var(--text-3)" }}>K线图暂不可用</span></section>}>
                      <LifeKlineChart analysisId={analysisId} />
                    </Safe>
                    <DailyFortuneCard analysisId={analysisId} />
                  </div>
                  <div className="sm:hidden">
                    <Accordion>
                      <AccordionItem title="大运流年" defaultOpen>
                  <DayunTimeline result={analysisResult} ziweiParams={ziweiParams} />
                      </AccordionItem>
                      <AccordionItem title="人生 K 线">
                        <Safe fallback={<p className="text-sm py-4 text-center" style={{ color: "var(--text-3)" }}>K线图暂不可用</p>}>
                          <LifeKlineChart analysisId={analysisId} />
                        </Safe>
                      </AccordionItem>
                      <AccordionItem title="今日运势">
                        <DailyFortuneCard analysisId={analysisId} />
                      </AccordionItem>
                    </Accordion>
                  </div>
                </>
              )}

              {/* Tab 3: 宫位神煞 */}
              {activeTab==="detail"&&(
                <>
                  <div className="hidden sm:block">
                    <GongweiPanel result={analysisResult} />
                    <ShenShaPanel result={analysisResult} />
                  </div>
                  <div className="sm:hidden">
                    <Accordion>
                      <AccordionItem title="宫位分析" defaultOpen>
                        <GongweiPanel result={analysisResult} />
                      </AccordionItem>
                      <AccordionItem title="神煞查盘" defaultOpen>
                        <ShenShaPanel result={analysisResult} />
                      </AccordionItem>
                    </Accordion>
                  </div>
                </>
              )}

              {/* Tab 4: 紫微斗数 */}
              {activeTab==="ziwei"&&(
                <>
                  <div className="hidden sm:block">
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
                  <div className="sm:hidden">
                    {analysisResult?.ziwei ? (
                      <Accordion>
                        <AccordionItem title="紫微斗数命盘" defaultOpen>
                          <ZiweiPanel data={analysisResult.ziwei as Record<string, unknown>} />
                        </AccordionItem>
                      </Accordion>
                    ) : (
                      <section className="card p-6">
                        <p className="text-[14px]" style={{ color: "var(--text-3)" }}>紫微斗数数据不可用（需安装 iztro-py 依赖）</p>
                      </section>
                    )}
                  </div>
                </>
              )}

              {/* Tab 5: 深度分析 */}
              {activeTab==="deep"&&(
                <>
                  <div className="hidden sm:block space-y-8">
                    <DimensionAnalysisPanel dimension="marriage" data={(analysisResult?.marriage_analysis as Record<string,unknown>)||{}} narration={typeof narration?.marriage==="string"?narration.marriage:""} />
                    <DimensionAnalysisPanel dimension="health" data={(analysisResult?.health_analysis as Record<string,unknown>)||{}} narration={typeof narration?.health==="string"?narration.health:""} />
                    <DimensionAnalysisPanel dimension="wealth" data={(analysisResult?.wealth_analysis as Record<string,unknown>)||{}} narration={typeof narration?.wealth==="string"?narration.wealth:""} />
                    <DimensionAnalysisPanel dimension="family" data={(analysisResult?.family_analysis as Record<string,unknown>)||{}} narration={typeof narration?.family==="string"?narration.family:""} />
                  </div>
                  <div className="sm:hidden">
                    <Accordion>
                      <AccordionItem title="婚姻感情" defaultOpen>
                        <DimensionAnalysisPanel dimension="marriage" data={(analysisResult?.marriage_analysis as Record<string,unknown>)||{}} narration={typeof narration?.marriage==="string"?narration.marriage:""} />
                      </AccordionItem>
                      <AccordionItem title="健康养生">
                        <DimensionAnalysisPanel dimension="health" data={(analysisResult?.health_analysis as Record<string,unknown>)||{}} narration={typeof narration?.health==="string"?narration.health:""} />
                      </AccordionItem>
                      <AccordionItem title="财富事业">
                        <DimensionAnalysisPanel dimension="wealth" data={(analysisResult?.wealth_analysis as Record<string,unknown>)||{}} narration={typeof narration?.wealth==="string"?narration.wealth:""} />
                      </AccordionItem>
                      <AccordionItem title="家庭六亲">
                        <DimensionAnalysisPanel dimension="family" data={(analysisResult?.family_analysis as Record<string,unknown>)||{}} narration={typeof narration?.family==="string"?narration.family:""} />
                      </AccordionItem>
                    </Accordion>
                  </div>
                </>
              )}

              {/* Tab 6: 流派解读 */}
              {activeTab==="analysis"&&(
                <>
                  <div className="hidden sm:block" style={{maxWidth:860,marginLeft:"auto",marginRight:"auto"}}>
                    {analysisResult?.llm_overview && <LlmOverview content={analysisResult.llm_overview as string} />}
                    {isCompareMode&&schoolAnalyses?<SchoolComparePanel schoolAnalyses={schoolAnalyses}/>:<SchoolPanel result={analysisResult} narration={narration}/>}
                  </div>
                  <div className="sm:hidden">
                    <Accordion>
                      {analysisResult?.llm_overview && (
                        <AccordionItem title="AI 总览" defaultOpen>
                          <LlmOverview content={analysisResult.llm_overview as string} />
                        </AccordionItem>
                      )}
                      <AccordionItem title="流派解读" defaultOpen>
                        {isCompareMode&&schoolAnalyses?<SchoolComparePanel schoolAnalyses={schoolAnalyses}/>:<SchoolPanel result={analysisResult} narration={narration}/>}
                      </AccordionItem>
                    </Accordion>
                  </div>
                </>
              )}

              {/* Tab 7: 命理问答 */}
              {activeTab==="chat"&&(
                <ChatPanel analysisId={analysisId} school={currentSchool === "all" ? "ziping" : currentSchool} />
              )}
            </div>

            {/* 移动端底部 Tab 导航 */}
            <MobileTabBar activeTab={activeTab} onTabChange={setActiveTab} />
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
