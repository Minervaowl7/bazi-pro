const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function _getApiKey(): string {
  if (typeof window === "undefined") return "";
  try {
    return localStorage.getItem("bazi_api_key") || "";
  } catch {
    return "";
  }
}

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const apiKey = _getApiKey();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch (networkErr) {
    const message = networkErr instanceof Error ? networkErr.message : "网络连接失败";
    throw new ApiError(message, 0, "NETWORK_ERROR");
  }
  if (!res.ok) {
    if (res.status === 404) {
      throw new ApiError("资源不存在", 404, "NOT_FOUND");
    }
    const err = await res.json().catch(() => ({}));
    const message =
      err?.error?.message || err?.detail || `请求失败 (${res.status})`;
    throw new ApiError(message, res.status, err?.error?.code);
  }
  return res.json();
}

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
  error?: string;
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
  return fetchApi("/api/v2/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  return fetchApi(`/api/v2/analysis/${analysisId}`);
}

export async function getHistory(page = 1, pageSize = 20): Promise<HistoryResponse> {
  return fetchApi(`/api/v2/history?page=${page}&page_size=${pageSize}`);
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
  return fetchApi("/api/v2/paipan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export interface ChatMessage {
  role: string;
  content: string;
  citations?: string;
  created_at?: string;
}

export interface ChatResponse {
  reply: string;
  citations?: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

export async function sendChatMessage(analysisId: string, message: string, school: string = "ziping"): Promise<ChatResponse> {
  return fetchApi("/api/v2/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId, message, school }),
  });
}

export async function getChatHistory(analysisId: string, school?: string): Promise<ChatHistoryResponse> {
  const params = school ? `?school=${encodeURIComponent(school)}` : "";
  return fetchApi(`/api/v2/chat/${analysisId}${params}`);
}

export interface ReportSection {
  title: string;
  content: string;
}

export interface ReportResponse {
  analysis_id: string;
  status: "generating" | "completed" | "failed";
  sections?: Record<string, string>;
  citations?: Record<string, string>;
  created_at?: string;
  completed_at?: string;
  error?: string;
}

export async function generateReport(analysisId: string, school: string = "ziping"): Promise<ReportResponse> {
  return fetchApi("/api/v2/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId, school }),
  });
}

export async function getReport(analysisId: string): Promise<ReportResponse | null> {
  try {
    return await fetchApi<ReportResponse>(`/api/v2/report/${analysisId}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export interface LLMSettings {
  api_key: string;
  api_base: string;
  model: string;
}

export interface LLMSettingsResponse {
  api_base: string;
  api_key_set: boolean;
  model: string;
}

export async function getLLMSettings(): Promise<LLMSettingsResponse> {
  return fetchApi("/api/v2/settings/llm");
}

export async function updateLLMSettings(settings: LLMSettings): Promise<LLMSettingsResponse> {
  return fetchApi("/api/v2/settings/llm", {
    method: "POST",
    body: JSON.stringify(settings),
  });
}

export interface LLMTestResponse {
  ok: boolean;
  reply?: string;
}

export async function testLLMConnection(): Promise<LLMTestResponse> {
  return fetchApi("/api/v2/settings/llm/test", { method: "POST" });
}

export interface DailyFortune {
  date: string;
  gan_zhi: string;
  overall_level: string;
  dimensions: Record<string, { score: number; level: string }>;
}

export async function getDailyFortune(analysisId: string): Promise<DailyFortune> {
  return fetchApi(`/api/v2/fortune/daily/${analysisId}`);
}

export interface DayunLiunianResponse {
  analysis_id: string;
  dayun_scores: Array<Record<string, unknown>>;
  liunian_scores: Array<{ year: number; age: number; gan_zhi: string; score: number; level?: string; reason?: string }>;
  warning?: string;
}

export async function getDayunLiunian(analysisId: string): Promise<DayunLiunianResponse> {
  return fetchApi(`/api/v2/dayun-liunian/${analysisId}`);
}

const SSE_TIMEOUT_MS = 120000;

export function subscribeSSE(
  analysisId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (err: Event) => void,
): EventSource {
  const apiKey = _getApiKey();
  let url = `${API_BASE}/api/v2/analysis/${analysisId}/stream`;
  if (apiKey) {
    url += `?token=${encodeURIComponent(apiKey)}`;
  }
  const es = new EventSource(url);

  let done = false;
  let timedOut = false;

  const handleEvent = (type: string) => (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onEvent({ event: type, data });
    } catch {
      onEvent({ event: type, data: { raw: e.data } });
    }
  };

  es.addEventListener("progress", handleEvent("progress"));
  es.addEventListener("done", (e) => {
    done = true;
    clearTimeout(timeoutId);
    handleEvent("done")(e);
  });

  es.addEventListener("analysis-error", (e: MessageEvent) => {
    done = true;
    clearTimeout(timeoutId);
    try {
      const data = JSON.parse(e.data);
      onEvent({ event: "error", data });
    } catch {
      onEvent({ event: "error", data: { raw: e.data, message: "分析过程出错" } });
    }
  });

  const timeoutId = setTimeout(() => {
    if (!done) {
      timedOut = true;
      es.close();
      onError?.(new Event("timeout") as unknown as Event);
    }
  }, SSE_TIMEOUT_MS);

  const origOnError = es.onerror;
  es.onerror = (e: Event) => {
    if (done || timedOut) return;
    clearTimeout(timeoutId);
    if (!done && !timedOut) {
      onError?.(e);
    }
    origOnError?.call(es, e);
  };

  return es;
}

// ── 紫微斗数 API ──────────────────────────────────────────────

export interface ZiweiChartParams {
  solar_date: string;
  hour: number;
  gender: number;
}

export interface ZiweiHoroscopeParams extends ZiweiChartParams {
  query_date?: string;
}

export interface ZiweiPalaceParams extends ZiweiChartParams {
  palace_name?: string;
}

export async function getZiweiChart(params: ZiweiChartParams): Promise<Record<string, unknown>> {
  return fetchApi("/api/v2/ziwei/chart", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getZiweiHoroscope(params: ZiweiHoroscopeParams): Promise<Record<string, unknown>> {
  return fetchApi("/api/v2/ziwei/horoscope", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getZiweiPalace(params: ZiweiPalaceParams): Promise<Record<string, unknown>> {
  return fetchApi("/api/v2/ziwei/palace", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
