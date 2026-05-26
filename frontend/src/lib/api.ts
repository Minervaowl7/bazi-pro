const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8710";

export interface BirthInput {
  性别: string;
  八字: string;
  日主: string;
  阳历?: string;
  农历?: string;
  生肖?: string;
  大运?: Array<{ age_range: string; gan: string; zhi: string }>;
  detail_level?: string;
  longitude?: number;
  latitude?: number;
}

export interface AnalysisSubmitResponse {
  analysis_id: string;
  status: string;
  stream_url: string;
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface AnalysisResult {
  analysis_id: string;
  status: string;
  created_at?: string;
  completed_at?: string;
  day_master?: string;
  pattern?: string;
  yongshen?: string;
  result?: Record<string, unknown>;
}

export interface HistoryItem {
  id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  day_master: string;
  pattern: string;
  yongshen: string;
  bazi?: string;
}

export interface HistoryResponse {
  analyses: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function submitAnalysis(input: BirthInput): Promise<AnalysisSubmitResponse> {
  const res = await fetch(`${API_BASE}/api/v2/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `请求失败 (${res.status})`);
  }
  return res.json();
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v2/analysis/${analysisId}`);
  if (!res.ok) {
    throw new Error(`获取分析结果失败 (${res.status})`);
  }
  return res.json();
}

export async function getHistory(page = 1, pageSize = 20): Promise<HistoryResponse> {
  const res = await fetch(`${API_BASE}/api/v2/history?page=${page}&page_size=${pageSize}`);
  if (!res.ok) {
    throw new Error(`获取历史记录失败 (${res.status})`);
  }
  return res.json();
}

export function subscribeSSE(
  analysisId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (err: Event) => void,
): EventSource {
  const url = `${API_BASE}/api/v2/analysis/${analysisId}/stream`;
  const es = new EventSource(url);

  const handleEvent = (type: string) => (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({ event: type, data });
    } catch {
      onEvent({ event: type, data: { raw: e.data } });
    }
  };

  es.addEventListener("progress", handleEvent("progress"));
  es.addEventListener("done", handleEvent("done"));
  es.addEventListener("error", (e) => {
    if (es.readyState === EventSource.CLOSED) return;
    onError?.(e);
  });

  return es;
}
