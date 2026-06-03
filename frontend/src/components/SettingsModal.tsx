"use client";

import { useCallback, useEffect, useState } from "react";
import { getLLMSettings, updateLLMSettings, type LLMSettings } from "@/lib/api";

const STORAGE_KEY = "bazi_llm_settings";

const POPULAR_MODELS = [
  { label: "GPT-4o Mini", value: "gpt-4o-mini" },
  { label: "GPT-4o", value: "gpt-4o" },
  { label: "DeepSeek Chat", value: "deepseek-chat" },
  { label: "DeepSeek Reasoner", value: "deepseek-reasoner" },
  { label: "Qwen Plus", value: "qwen-plus" },
  { label: "Qwen Turbo", value: "qwen-turbo" },
  { label: "Claude 3.5 Sonnet", value: "claude-3-5-sonnet-20241022" },
  { label: "自定义", value: "" },
];

const POPULAR_BASES = [
  { label: "OpenAI", value: "https://api.openai.com/v1" },
  { label: "DeepSeek", value: "https://api.deepseek.com/v1" },
  { label: "通义千问", value: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { label: "硅基流动", value: "https://api.siliconflow.cn/v1" },
  { label: "自定义", value: "" },
];

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [form, setForm] = useState<LLMSettings>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as LLMSettings;
        return { api_base: parsed.api_base || "https://api.openai.com/v1", model: parsed.model || "gpt-4o-mini", api_key: "" };
      }
    } catch {}
    return { api_key: "", api_base: "https://api.openai.com/v1", model: "gpt-4o-mini" };
  });
  const [keySet, setKeySet] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadFromServer = useCallback(() => {
    getLLMSettings()
      .then(data => {
        setForm({
          api_base: data.api_base || "https://api.openai.com/v1",
          model: data.model || "gpt-4o-mini",
          api_key: "",
        });
        setKeySet(data.api_key_set || false);
        setLoaded(true);
      })
      .catch(() => { setLoaded(true); });
  }, []);

  useEffect(() => {
    if (open && !loaded) {
      loadFromServer();
    }
  }, [open, loaded, loadFromServer]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  const handleSave = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const payload: Record<string, string> = { ...form };
      if (!payload.api_key && keySet) delete payload.api_key;

      const data = await updateLLMSettings({ api_key: payload.api_key || "", api_base: payload.api_base || "", model: payload.model || "" });
      if (data.api_key_set !== undefined) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ api_base: form.api_base, model: form.model }));
        setKeySet(data.api_key_set || false);
        setMsg({ text: "保存成功", ok: true });
        if (form.api_key) setForm(f => ({ ...f, api_key: "" }));
      } else {
        setMsg({ text: "保存失败", ok: false });
      }
    } catch {
      setMsg({ text: "连接失败，请检查后端是否启动", ok: false });
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  const currentBasePreset = POPULAR_BASES.find(b => b.value === form.api_base);
  const currentModelPreset = POPULAR_MODELS.find(m => m.value === form.model);
  const isCustomBase = !currentBasePreset;
  const isCustomModel = !currentModelPreset;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="LLM 设置"
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(28,25,23,0.45)",
        backdropFilter: "blur(4px)",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: "100%", maxWidth: 480,
        background: "var(--surface)",
        border: "1px solid var(--color-border)",
        boxShadow: "0 25px 50px -12px rgba(28,25,23,0.25)",
        padding: 0,
        overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "20px 24px 16px",
          borderBottom: "1px solid var(--color-border)",
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--color-ink)", fontFamily: "var(--font-serif)", margin: 0 }}>
            LLM 配置
          </h2>
          <button
            aria-label="关闭"
            onClick={onClose}
            style={{
              width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center",
              background: "transparent", border: "none", cursor: "pointer", color: "var(--color-text-muted)",
            }}
          >
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Status indicator */}
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "10px 14px",
            background: keySet ? "rgba(34,197,94,0.08)" : "rgba(234,88,12,0.08)",
            border: `1px solid ${keySet ? "rgba(34,197,94,0.2)" : "rgba(234,88,12,0.2)"}`,
          }}>
            <div aria-hidden="true" style={{
              width: 8, height: 8, borderRadius: "50%",
              background: keySet ? "#22c55e" : "#ea580c",
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 13, color: keySet ? "#16a34a" : "#c2410c", fontWeight: 500 }}>
              {keySet ? "API Key 已配置" : "API Key 未配置，AI 解读功能不可用"}
            </span>
          </div>

          {/* API Base */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label htmlFor="llm-api-base" style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>
              API 服务商
            </label>
            <select
              id="llm-api-base-preset"
              value={isCustomBase ? "" : form.api_base}
              onChange={(e) => {
                if (e.target.value === "") {
                  setForm(f => ({ ...f, api_base: "" }));
                } else {
                  setForm(f => ({ ...f, api_base: e.target.value }));
                }
              }}
              style={{
                fontSize: 14, padding: "10px 12px",
                background: "var(--bg-secondary)", color: "var(--color-text-primary)",
                border: "1px solid var(--color-border-subtle)",
                fontFamily: "var(--font-sans)", outline: "none",
              }}
            >
              {POPULAR_BASES.map(b => (
                <option key={b.label} value={b.value}>{b.label}{b.value ? ` - ${b.value}` : ""}</option>
              ))}
            </select>
            {isCustomBase && (
              <input
                id="llm-api-base"
                type="url"
                autoComplete="off"
                spellCheck={false}
                placeholder="https://api.example.com/v1"
                value={form.api_base}
                onChange={(e) => setForm(f => ({ ...f, api_base: e.target.value }))}
                style={{
                  fontSize: 14, padding: "10px 12px",
                  background: "var(--bg-secondary)", color: "var(--color-text-primary)",
                  border: "1px solid var(--color-border-subtle)",
                  fontFamily: "var(--font-sans)", outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-scholar-blue)"; e.currentTarget.style.boxShadow = "0 0 0 2px rgba(45,62,95,0.15)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--color-border-subtle)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            )}
          </div>

          {/* API Key */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label htmlFor="llm-api-key" style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>
              API Key
            </label>
            <div style={{ position: "relative" }}>
              <input
                id="llm-api-key"
                type={showKey ? "text" : "password"}
                autoComplete="off"
                spellCheck={false}
                placeholder={keySet ? "已保存，留空则保持不变" : "sk-..."}
                value={form.api_key}
                onChange={(e) => setForm(f => ({ ...f, api_key: e.target.value }))}
                style={{
                  fontSize: 14, padding: "10px 12px", paddingRight: 44,
                  background: "var(--bg-secondary)", color: "var(--color-text-primary)",
                  border: "1px solid var(--color-border-subtle)",
                  fontFamily: "var(--font-sans)", outline: "none",
                  width: "100%", boxSizing: "border-box",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-scholar-blue)"; e.currentTarget.style.boxShadow = "0 0 0 2px rgba(45,62,95,0.15)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--color-border-subtle)"; e.currentTarget.style.boxShadow = "none"; }}
              />
              <button
                aria-label={showKey ? "隐藏 Key" : "显示 Key"}
                onClick={() => setShowKey(!showKey)}
                style={{
                  position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)",
                  background: "transparent", border: "none", cursor: "pointer",
                  color: "var(--color-text-muted)", padding: 4,
                }}
              >
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  {showKey
                    ? <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
                    : <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                  }
                </svg>
              </button>
            </div>
          </div>

          {/* Model */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label htmlFor="llm-model" style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>
              模型
            </label>
            <select
              id="llm-model-preset"
              value={isCustomModel ? "" : form.model}
              onChange={(e) => {
                if (e.target.value === "") {
                  setForm(f => ({ ...f, model: "" }));
                } else {
                  setForm(f => ({ ...f, model: e.target.value }));
                }
              }}
              style={{
                fontSize: 14, padding: "10px 12px",
                background: "var(--bg-secondary)", color: "var(--color-text-primary)",
                border: "1px solid var(--color-border-subtle)",
                fontFamily: "var(--font-sans)", outline: "none",
              }}
            >
              {POPULAR_MODELS.map(m => (
                <option key={m.label} value={m.value}>{m.label}{m.value ? ` (${m.value})` : ""}</option>
              ))}
            </select>
            {isCustomModel && (
              <input
                id="llm-model"
                type="text"
                autoComplete="off"
                spellCheck={false}
                placeholder="模型名称"
                value={form.model}
                onChange={(e) => setForm(f => ({ ...f, model: e.target.value }))}
                style={{
                  fontSize: 14, padding: "10px 12px",
                  background: "var(--bg-secondary)", color: "var(--color-text-primary)",
                  border: "1px solid var(--color-border-subtle)",
                  fontFamily: "var(--font-sans)", outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-scholar-blue)"; e.currentTarget.style.boxShadow = "0 0 0 2px rgba(45,62,95,0.15)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--color-border-subtle)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            )}
          </div>

          {/* Message */}
          {msg && (
            <div aria-live="polite" style={{
              fontSize: 13, fontWeight: 500,
              color: msg.ok ? "#16a34a" : "#dc2626",
              padding: "8px 12px",
              background: msg.ok ? "rgba(34,197,94,0.08)" : "rgba(220,38,38,0.08)",
              border: `1px solid ${msg.ok ? "rgba(34,197,94,0.2)" : "rgba(220,38,38,0.2)"}`,
            }}>
              {msg.text}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          display: "flex", justifyContent: "flex-end", gap: 10,
          padding: "16px 24px 20px",
          borderTop: "1px solid var(--color-border)",
        }}>
          <button
            onClick={onClose}
            style={{
              fontSize: 14, fontWeight: 500, padding: "9px 20px",
              background: "transparent", border: "1px solid var(--color-border)",
              color: "var(--color-text-primary)", cursor: "pointer", fontFamily: "var(--font-sans)",
            }}
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              fontSize: 14, fontWeight: 600, padding: "9px 24px",
              background: "var(--color-scholar-blue)", border: "none",
              color: "#fff", cursor: saving ? "wait" : "pointer", fontFamily: "var(--font-sans)",
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
