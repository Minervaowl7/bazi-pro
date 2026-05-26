import { create } from "zustand";
import {
  type AnalysisResult,
  type BirthInput,
  type SSEEvent,
  getAnalysis,
  submitAnalysis,
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
  status: "idle" | "submitting" | "streaming" | "completed" | "failed";
  progress: ProgressStep[];
  result: AnalysisResult | null;
  error: string | null;

  setBirthInput: (input: BirthInput) => void;
  startAnalysis: (input: BirthInput) => Promise<string>;
  fetchResult: (analysisId: string) => Promise<void>;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  birthInput: null,
  analysisId: null,
  status: "idle",
  progress: [],
  result: null,
  error: null,

  setBirthInput: (input) => set({ birthInput: input }),

  startAnalysis: async (input) => {
    set({ status: "submitting", error: null, progress: [], result: null });
    try {
      const resp = await submitAnalysis(input);
      set({ analysisId: resp.analysis_id, status: "streaming", birthInput: input });

      const es = subscribeSSE(
        resp.analysis_id,
        (event: SSEEvent) => {
          if (event.event === "progress") {
            const step = event.data as unknown as ProgressStep;
            set((state) => ({ progress: [...state.progress, step] }));
          } else if (event.event === "done") {
            es.close();
            get().fetchResult(resp.analysis_id);
          }
        },
        () => {
          es.close();
          setTimeout(() => get().fetchResult(resp.analysis_id), 1000);
        },
      );

      return resp.analysis_id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "未知错误";
      set({ status: "failed", error: msg });
      throw e;
    }
  },

  fetchResult: async (analysisId) => {
    try {
      const data = await getAnalysis(analysisId);
      set({ result: data, status: data.status === "failed" ? "failed" : "completed" });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "获取结果失败";
      set({ status: "failed", error: msg });
    }
  },

  reset: () =>
    set({
      birthInput: null,
      analysisId: null,
      status: "idle",
      progress: [],
      result: null,
      error: null,
    }),
}));
