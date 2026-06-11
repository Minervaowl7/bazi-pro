export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

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

async function fetchApi<T>(path: string, init?: RequestInit, timeoutMs = 30000): Promise<T> {
  const apiKey = _getApiKey();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort("请求超时"), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal });
  } catch (networkErr) {
    const message = networkErr instanceof Error
      ? networkErr.name === "AbortError"
        ? "请求超时，请检查后端服务是否启动"
        : networkErr.message
      : "网络连接失败";
    throw new ApiError(message, 0, networkErr instanceof Error && networkErr.name === "AbortError" ? "TIMEOUT" : "NETWORK_ERROR");
  } finally {
    clearTimeout(timer);
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
  try {
    return await res.json();
  } catch {
    throw new ApiError("响应解析失败", res.status, "PARSE_ERROR");
  }
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
  name?: string;
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
  }, 120000);
}

/** SSE 流式 Chat 事件类型 */
export interface ChatStreamEvent {
  type: "token" | "reasoning" | "done" | "error" | "tool_call" | "tool_result";
  content: string;
  /** 工具调用名称（仅 tool_call 事件） */
  tool_name?: string;
  /** 工具调用参数（仅 tool_call 事件） */
  tool_args?: string;
}

/**
 * SSE 流式 Chat — 使用 fetch + ReadableStream 消费 SSE（支持自定义 Header）
 * 回调 onEvent 在每次收到事件时触发，返回 AbortController 供中断
 */
export function sendChatMessageStream(
  analysisId: string,
  message: string,
  school: string,
  onEvent: (event: ChatStreamEvent) => void,
  onError: (err: Error) => void,
  onDone: () => void,
): AbortController {
  const apiKey = _getApiKey();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const controller = new AbortController();

  (async () => {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}/api/v2/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ analysis_id: analysisId, message, school }),
        signal: controller.signal,
      });
    } catch (err) {
      if ((err as Error).name === "AbortError") return; // 用户主动中断
      onError(new Error(err instanceof Error ? (err.name === "AbortError" ? "请求已取消" : err.message) : "网络连接失败"));
      return;
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const msg = body?.error?.message || body?.detail || `请求失败 (${res.status})`;
      onError(new Error(msg));
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      onError(new Error("无法读取响应流"));
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 按 \n\n 分割 SSE 事件
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || ""; // 最后一个可能是不完整的

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          const dataStr = line.slice(6);
          try {
            const evt = JSON.parse(dataStr) as ChatStreamEvent;
            onEvent(evt);
            if (evt.type === "done") {
              onDone();
              return;
            }
            if (evt.type === "error") {
              onError(new Error(evt.content || "流式响应出错"));
              return;
            }
          } catch {
            // 忽略解析失败的行
          }
        }
      }
      // 流正常结束但没有收到 done 事件
      onDone();
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      onError(new Error(err instanceof Error ? err.message : "流读取中断"));
    }
  })();

  return controller;
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
  }, 300000);
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
  return fetchApi("/api/v2/settings/llm/test", { method: "POST" }, 120000);
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

export interface ZiweiDayunStep {
  age_range: string;
  age_start: number;
  age_end: number;
  palace: string;
  heavenly_stem: string;
  earthly_branch: string;
  major_stars: Array<{ name: string; brightness: string }>;
  sihua_flow: Record<string, string>;
}

export interface ZiweiDayunResponse {
  dayun: ZiweiDayunStep[];
  chart_summary?: {
    soul?: string;
    body?: string;
    fiveElementsClass?: string;
  };
}

export async function getZiweiDayun(params: ZiweiChartParams): Promise<ZiweiDayunResponse> {
  return fetchApi("/api/v2/ziwei/dayun", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export interface ZiweiLiunianResponse {
  year: number;
  yearly_stem: string;
  yearly_branch: string;
  palace_name: string;
  sihua: Record<string, string>;
  [key: string]: unknown;
}

export async function getZiweiLiunian(params: ZiweiHoroscopeParams): Promise<ZiweiLiunianResponse> {
  return fetchApi("/api/v2/ziwei/liunian", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export interface ZiweiSihuaParams extends ZiweiChartParams {
  query_year?: number;
}

export interface ZiweiSihuaBenming {
  sihua?: Record<string, string>;
  star_sihua_map?: Record<string, string>;
  palace_sihua?: Record<string, string[]>;
}

export interface ZiweiSihuaResponse {
  benming?: ZiweiSihuaBenming;
  daxian?: Array<Record<string, unknown>>;
  liunian?: Record<string, unknown>;
  [key: string]: unknown;
}

export async function getZiweiSihua(params: ZiweiSihuaParams): Promise<ZiweiSihuaResponse> {
  return fetchApi("/api/v2/ziwei/sihua", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
