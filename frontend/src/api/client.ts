const BASE_URL = import.meta.env.VITE_API_URL || '';

interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

function getToken(): string | null {
  return localStorage.getItem('bazi_token');
}

function setToken(token: string): void {
  localStorage.setItem('bazi_token', token);
}

function removeToken(): void {
  localStorage.removeItem('bazi_token');
}

function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeToken();
    localStorage.removeItem('bazi_user');
    window.location.href = '/login';
    throw new Error('认证已过期，请重新登录');
  }

  const data = await response.json();

  if (!response.ok) {
    const apiError = data as ApiError;
    throw new Error(apiError.error?.message || `请求失败 (${response.status})`);
  }

  return data as T;
}

export interface RegisterParams {
  email: string;
  password: string;
  display_name?: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export interface WechatLoginParams {
  code: string;
}

export interface AuthResponse {
  token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    display_name: string | null;
    is_active: boolean;
  };
}

export interface UserInfo {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  oauth_provider: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string | null;
}

export interface AnalyzeParams {
  性别: string;
  八字: string;
  日主: string;
  detail_level: string;
  阳历?: string;
  农历?: string;
  生肖?: string;
}

export interface AnalyzeResponse {
  run_id: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  status: string;
  run_id?: string;
  error?: string;
  step?: number;
  summary?: string;
}

export interface ResultResponse {
  status: string;
  run_id: string;
  html?: string;
  message?: string;
}

export interface HistoryItem {
  run_id: string;
  bazi: string;
  day_master: string;
  gender: string;
  solar_date: string;
  detail_level: string;
  status: string;
  created_at: string;
}

export interface HistoryResponse {
  history: HistoryItem[];
  total: number;
  source: string;
}

export interface QuotaInfo {
  allowed: boolean;
  plan: string;
  remaining: number;
  total: number;
}

export interface SubscriptionInfo {
  id: string;
  plan: string;
  status: string;
  started_at: string;
  expires_at: string | null;
}

export interface OrderParams {
  user_id: string;
  amount: number;
  payment_method: string;
  description: string;
}

export interface OrderResponse {
  order_id: string;
  amount: number;
  status: string;
  payment_url: string | null;
  created_at: string;
}

export const api = {
  auth: {
    register: (params: RegisterParams) =>
      request<AuthResponse>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    login: (params: LoginParams) =>
      request<AuthResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    wechat: (params: WechatLoginParams) =>
      request<AuthResponse>('/api/auth/wechat', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    me: () => request<UserInfo>('/api/auth/me'),
  },

  analysis: {
    create: (params: AnalyzeParams) =>
      request<AnalyzeResponse>('/api/analyze', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    status: (runId: string) =>
      request<StatusResponse>(`/api/status/${runId}`),

    result: (runId: string) =>
      request<ResultResponse>(`/api/result/${runId}`),
  },

  history: {
    list: (limit = 50, offset = 0) =>
      request<HistoryResponse>(`/api/history?limit=${limit}&offset=${offset}`),
  },

  billing: {
    quota: (userId: string) =>
      request<QuotaInfo>(`/api/billing/quota?user_id=${userId}`),

    subscription: (userId: string) =>
      request<SubscriptionInfo>(`/api/billing/subscription?user_id=${userId}`),

    createOrder: (params: OrderParams) =>
      request<OrderResponse>('/api/billing/order', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
  },
};

export { getToken, setToken, removeToken };
