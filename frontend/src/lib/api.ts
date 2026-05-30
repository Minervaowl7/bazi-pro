const SERVER_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";
const API_BASE = typeof window !== "undefined" ? "" : SERVER_API_BASE;

export interface BirthInput {
  性别: string;
  八字: string;
  日主: string;
  阳历?: string;
  农历?: string;
  生肖?: string;
  大运?: Array<{ age_range: string; gan: string; zhi: string }>;
  detail_level?: string;
  school?: string;
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
  narration?: Record<string, unknown>;
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

export interface PaipanInput {
  性别: string;
  阳历: string;
  农历?: string;
}

export interface PaipanPillar {
  position: string;
  gan: string;
  zhi: string;
  wuxing_gan: string;
  wuxing_zhi: string;
}

export interface PaipanResult {
  status: string;
  八字: string;
  日主: string;
  性别: string;
  阳历: string;
  生肖: string;
  pillars: PaipanPillar[];
  dayun: Array<{ age_range: string; gan: string; zhi: string }>;
  message?: string;
}

export async function submitPaipan(input: PaipanInput): Promise<PaipanResult> {
  const res = await fetch(`${API_BASE}/api/v2/paipan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `排盘请求失败 (${res.status})`);
  }
  return res.json();
}

export interface ChatMessage {
  role: string;
  content: string;
  citations?: string;
  created_at?: string;
}

export interface ChatResponse {
  reply: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

export async function sendChatMessage(analysisId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v2/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId, message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `对话请求失败 (${res.status})`);
  }
  return res.json();
}

export async function getChatHistory(analysisId: string): Promise<ChatHistoryResponse> {
  const res = await fetch(`${API_BASE}/api/v2/chat/${analysisId}`);
  if (!res.ok) {
    throw new Error(`获取对话历史失败 (${res.status})`);
  }
  return res.json();
}

export interface ReportSection {
  title: string;
  content: string;
}

export interface ReportResponse {
  analysis_id: string;
  status: "generating" | "completed" | "failed";
  sections?: Record<string, string>;
  created_at?: string;
  completed_at?: string;
  error?: string;
}

export async function generateReport(analysisId: string): Promise<ReportResponse> {
  const res = await fetch(`${API_BASE}/api/v2/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `生成报告失败 (${res.status})`);
  }
  return res.json();
}

export async function getReport(analysisId: string): Promise<ReportResponse | null> {
  const res = await fetch(`${API_BASE}/api/v2/report/${analysisId}`);
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`获取报告失败 (${res.status})`);
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
