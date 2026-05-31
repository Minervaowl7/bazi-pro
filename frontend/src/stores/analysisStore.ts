import { create } from "zustand";
import {
  type AnalysisResult,
  type BirthInput,
  type PaipanInput,
  type PaipanResult,
  getAnalysis,
  submitAnalysis,
  submitPaipan,
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
  paipanResult: PaipanResult | null;
  paipanLoading: boolean;

  setBirthInput: (input: BirthInput) => void;
  startAnalysis: (input: BirthInput) => Promise<string>;
  fetchResult: (analysisId: string) => Promise<void>;
  submitPaipan: (input: PaipanInput) => Promise<void>;
  reset: () => void;
}

const POLL_INTERVAL = 2000;
const MAX_POLLS = 150;

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  birthInput: null,
  analysisId: null,
  status: "idle",
  progress: [],
  result: null,
  error: null,
  paipanResult: null,
  paipanLoading: false,

  setBirthInput: (input) => set({ birthInput: input }),

  startAnalysis: async (input) => {
    set({ status: "submitting", error: null, progress: [], result: null });
    try {
      const resp = await submitAnalysis(input);
      set({ analysisId: resp.analysis_id, status: "streaming", birthInput: input });
      return resp.analysis_id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "未知错误";
      set({ status: "failed", error: msg });
      throw e;
    }
  },

  fetchResult: async (analysisId) => {
    let pollCount = 0;
    const poll = async (): Promise<void> => {
      try {
        const data = await getAnalysis(analysisId);
        if (data.status === "failed") {
          set({ result: data, status: "failed" });
          return;
        }
        if (data.status === "completed") {
          set({ result: data, status: "completed" });
          return;
        }
        pollCount++;
        if (pollCount >= MAX_POLLS) {
          set({ status: "failed", error: "分析超时，请稍后刷新重试" });
          return;
        }
        set({ result: data, status: "streaming" });
        await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        if (get().analysisId === analysisId || !get().analysisId) {
          await poll();
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : "获取结果失败";
        pollCount++;
        if (pollCount >= MAX_POLLS) {
          set({ status: "failed", error: msg });
          return;
        }
        await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        await poll();
      }
    };
    await poll();
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

  reset: () =>
    set({
      birthInput: null,
      analysisId: null,
      status: "idle",
      progress: [],
      result: null,
      error: null,
      paipanResult: null,
      paipanLoading: false,
    }),
}));
