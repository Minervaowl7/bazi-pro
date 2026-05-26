import { create } from 'zustand';
import { api, getToken, setToken, removeToken } from '../api/client';
import type { UserInfo } from '../api/client';

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  loading: boolean;
  error: string | null;
  initialized: boolean;

  init: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  wechatLogin: (code: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getToken(),
  user: null,
  loading: false,
  error: null,
  initialized: false,

  init: async () => {
    const token = getToken();
    if (!token) {
      set({ initialized: true });
      return;
    }
    try {
      const user = await api.auth.me();
      set({ user, initialized: true });
    } catch {
      removeToken();
      set({ token: null, user: null, initialized: true });
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await api.auth.login({ email, password });
      setToken(res.token);
      localStorage.setItem('bazi_user', JSON.stringify(res.user));
      set({ token: res.token, loading: false });
      await get().fetchUser();
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  register: async (email, password, displayName) => {
    set({ loading: true, error: null });
    try {
      const res = await api.auth.register({
        email,
        password,
        display_name: displayName,
      });
      setToken(res.token);
      localStorage.setItem('bazi_user', JSON.stringify(res.user));
      set({ token: res.token, loading: false });
      await get().fetchUser();
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  wechatLogin: async (code) => {
    set({ loading: true, error: null });
    try {
      const res = await api.auth.wechat({ code });
      setToken(res.token);
      localStorage.setItem('bazi_user', JSON.stringify(res.user));
      set({ token: res.token, loading: false });
      await get().fetchUser();
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  logout: () => {
    removeToken();
    localStorage.removeItem('bazi_user');
    set({ token: null, user: null });
  },

  clearError: () => set({ error: null }),

  fetchUser: async () => {
    try {
      const user = await api.auth.me();
      set({ user });
    } catch {
      removeToken();
      set({ token: null, user: null });
    }
  },
}));
