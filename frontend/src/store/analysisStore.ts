import { create } from 'zustand';

interface WsMessage {
  step: number;
  summary: string;
  status: string;
  progress?: number;
}

interface AnalysisState {
  runId: string | null;
  status: string;
  progress: number;
  currentStep: string;
  wsConnected: boolean;
  resultHtml: string | null;
  error: string | null;

  startAnalysis: (runId: string) => void;
  connectWs: (runId: string) => void;
  disconnectWs: () => void;
  setProgress: (step: number, summary: string, status: string) => void;
  setResult: (html: string) => void;
  setError: (error: string) => void;
  reset: () => void;
}

let wsInstance: WebSocket | null = null;

const BASE_URL = import.meta.env.VITE_API_URL || '';

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  runId: null,
  status: 'idle',
  progress: 0,
  currentStep: '',
  wsConnected: false,
  resultHtml: null,
  error: null,

  startAnalysis: (runId) => {
    set({
      runId,
      status: 'queued',
      progress: 0,
      currentStep: '已提交',
      wsConnected: false,
      resultHtml: null,
      error: null,
    });
    get().connectWs(runId);
  },

  connectWs: (runId) => {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = BASE_URL
      ? BASE_URL.replace(/^https?:\/\//, '').replace(/\/$/, '')
      : window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${runId}`;

    try {
      wsInstance = new WebSocket(wsUrl);

      wsInstance.onopen = () => {
        set({ wsConnected: true });
      };

      wsInstance.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data);
          const progressPercent = msg.step ? Math.min((msg.step / 9) * 100, 100) : get().progress;
          set({
            progress: progressPercent,
            currentStep: msg.summary || '',
            status: msg.status === 'done' ? 'completed' : 'running',
          });
          if (msg.status === 'done' && msg.step === 9) {
            set({ status: 'completed', progress: 100 });
            wsInstance?.close();
          }
        } catch {
          // ignore parse errors
        }
      };

      wsInstance.onerror = () => {
        set({ wsConnected: false });
      };

      wsInstance.onclose = () => {
        set({ wsConnected: false });
        wsInstance = null;
      };
    } catch {
      set({ wsConnected: false });
    }
  },

  disconnectWs: () => {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
    set({ wsConnected: false });
  },

  setProgress: (step, summary, status) => {
    const progressPercent = Math.min((step / 9) * 100, 100);
    set({ progress: progressPercent, currentStep: summary, status });
  },

  setResult: (html) => {
    set({ resultHtml: html, status: 'completed', progress: 100 });
  },

  setError: (error) => {
    set({ error, status: 'failed' });
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
  },

  reset: () => {
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
    set({
      runId: null,
      status: 'idle',
      progress: 0,
      currentStep: '',
      wsConnected: false,
      resultHtml: null,
      error: null,
    });
  },
}));
