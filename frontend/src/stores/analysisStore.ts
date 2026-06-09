import { create } from "zustand";
import {
  type AnalysisResult,
  type BirthInput,
  type PaipanInput,
  type PaipanResult,
  type SSEEvent,
  getAnalysis,
  submitAnalysis,
  submitPaipan,
  subscribeSSE,
} from "@/lib/api";

export interface ProgressStep {
  step: string;
  name: string;
  status: string;
  message: string;
}

interface AnalysisState {
  birthInput: BirthInput | null;
  analysisId: string | null;
  status: "idle" | "submitting" | "streaming" | "polling" | "completed" | "failed";
  progress: ProgressStep[];
  result: AnalysisResult | null;
  error: string | null;
  paipanResult: PaipanResult | null;
  paipanLoading: boolean;
  _sseRef: EventSource | null;

  setBirthInput: (input: BirthInput) => void;
  startAnalysis: (input: BirthInput) => Promise<string>;
  fetchResult: (analysisId: string, _retries?: number) => Promise<void>;
  submitPaipan: (input: PaipanInput) => Promise<void>;
  reset: () => void;
  closeSSE: () => void;
}

let _generation = 0; // 防止 SSE fallback 竞态
let _sseTimeoutId: ReturnType<typeof setTimeout> | null = null; // 15s 超时定时器

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  birthInput: null,
  analysisId: null,
  status: "idle",
  progress: [],
  result: null,
  error: null,
  paipanResult: null,
  paipanLoading: false,
  _sseRef: null,

  setBirthInput: (input) => set({ birthInput: input }),

  closeSSE: () => {
    const ref = get()._sseRef;
    if (ref) {
      ref.close();
      set({ _sseRef: null });
    }
    if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
  },

  startAnalysis: async (input) => {
    // 关闭之前的 SSE 连接
    const prevSse = get()._sseRef;
    if (prevSse) { prevSse.close(); }

    const gen = ++_generation;
    set({ status: "submitting", error: null, progress: [], result: null, _sseRef: null });
    try {
      const resp = await submitAnalysis(input);
      // Guard against race condition from double-click
      if (get().status !== "submitting") return "";
      set({ analysisId: resp.analysis_id, status: "streaming", birthInput: input });

      const es = subscribeSSE(
        resp.analysis_id,
        (event: SSEEvent) => {
          if (event.event === "progress") {
            if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
            const step = event.data as unknown as ProgressStep;
            set((state) => ({ progress: [...state.progress, step] }));
          } else if (event.event === "done") {
            if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
            es.close();
            set({ _sseRef: null });
            get().fetchResult(resp.analysis_id);
          } else if (event.event === "error") {
            if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
            es.close();
            set({ _sseRef: null });
            const data = event.data as Record<string, unknown>;
            const msg = (data?.message as string) || "分析过程出错";
            set({ status: "failed", error: msg });
          }
        },
        () => {
          if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
          es.close();
          set({ _sseRef: null });
          const current = get();
          if (current.status === "streaming" && _generation === gen) {
            set({ status: "polling" });
            setTimeout(() => {
              if (_generation === gen) get().fetchResult(resp.analysis_id);
            }, 1000);
          }
        },
      );

      // 15秒无进度事件 → 自动轮询（防止 SSE 连接成功但无事件）
      _sseTimeoutId = setTimeout(() => {
        _sseTimeoutId = null;
        if (_generation === gen && get().progress.length === 0 && get().status === "streaming") {
          es.close();
          set({ _sseRef: null, status: "polling" });
          setTimeout(() => {
            if (_generation === gen) get().fetchResult(resp.analysis_id);
          }, 500);
        }
      }, 15000);

      set({ _sseRef: es });
      return resp.analysis_id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "未知错误";
      set({ status: "failed", error: msg });
      throw e;
    }
  },

  fetchResult: async (analysisId, _retries = 0) => {
    let retries = _retries;
    const maxPollMs = 60000;
    const start = Date.now();
    while (true) {
      try {
        const data = await getAnalysis(analysisId);
        const hasResult = data.result && typeof data.result === "object" && Object.keys(data.result as Record<string, unknown>).length > 0;
        if (data.status === "completed" && !hasResult) {
          if (retries >= 8 || Date.now() - start > maxPollMs) {
            set({ status: "failed", error: "分析超时，请稍后重试" });
            return;
          }
          await new Promise((r) => setTimeout(r, 1500 * Math.pow(1.5, retries)));
          retries++;
          continue;
        }
        const failedError = data.error
          || (data.result && typeof data.result === "object" ? (data.result as Record<string, unknown>).error as string || undefined : undefined)
          || "分析过程出错";
        set({ result: data, status: data.status === "failed" ? "failed" : "completed", error: data.status === "failed" ? failedError : null });
        return;
      } catch (e) {
        const msg = e instanceof Error ? e.message : "获取结果失败";
        if (retries < 5 && Date.now() - start < maxPollMs) {
          await new Promise((r) => setTimeout(r, 2000));
          retries++;
          continue;
        }
        set({ status: "failed", error: msg });
        return;
      }
    }
  },

  submitPaipan: async (input) => {
    set({ paipanLoading: true, paipanResult: null });
    try {
      const result = await submitPaipan(input);
      set({ paipanResult: result, paipanLoading: false });
    } catch (e) {
      set({ paipanLoading: false });
      throw e;
    }
  },

  reset: () => {
    const ref = get()._sseRef;
    if (ref) { ref.close(); }
    if (_sseTimeoutId) { clearTimeout(_sseTimeoutId); _sseTimeoutId = null; }
    set({
      birthInput: null,
      analysisId: null,
      status: "idle",
      progress: [],
      result: null,
      error: null,
      paipanResult: null,
      paipanLoading: false,
      _sseRef: null,
    });
  },
}));
