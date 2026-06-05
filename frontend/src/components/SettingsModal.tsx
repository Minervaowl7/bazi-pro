"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getLLMSettings, updateLLMSettings, testLLMConnection } from "@/lib/api";

const STORAGE_KEY = "bazi_llm_settings";

interface Provider {
  id: string;
  name: string;
  desc: string;
  base: string;
  models: string[];
  keyPrefix: string;
}

const PROVIDERS: Provider[] = [
  {
    id: "xiaomi",
    name: "小米 MiMo",
    desc: "小米自研推理模型",
    base: "https://token-plan-cn.xiaomimimo.com/v1",
    models: ["mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-pro"],
    keyPrefix: "tp-",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    desc: "深度求索大模型",
    base: "https://api.deepseek.com/v1",
    models: ["deepseek-chat", "deepseek-reasoner"],
    keyPrefix: "sk-",
  },
  {
    id: "openai",
    name: "OpenAI",
    desc: "GPT 系列模型",
    base: "https://api.openai.com/v1",
    models: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    keyPrefix: "sk-",
  },
  {
    id: "qwen",
    name: "通义千问",
    desc: "阿里云大模型",
    base: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    models: ["qwen-plus", "qwen-turbo", "qwen-max"],
    keyPrefix: "sk-",
  },
  {
    id: "siliconflow",
    name: "硅基流动",
    desc: "开源模型聚合平台",
    base: "https://api.siliconflow.cn/v1",
    models: ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"],
    keyPrefix: "sk-",
  },
  {
    id: "ollama",
    name: "Ollama",
    desc: "本地模型部署",
    base: "http://localhost:11434/v1",
    models: ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b"],
    keyPrefix: "",
  },
];

function detectProvider(apiBase: string): Provider | null {
  for (const p of PROVIDERS) {
    if (apiBase.includes(new URL(p.base).hostname)) return p;
  }
  return null;
}

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [apiBase, setApiBase] = useState("https://token-plan-cn.xiaomimimo.com/v1");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("mimo-v2.5-pro");
  const [keySet, setKeySet] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [customBase, setCustomBase] = useState(false);
  const [customModel, setCustomModel] = useState(false);

  const provider = useMemo(() => detectProvider(apiBase), [apiBase]);

  const loadFromServer = useCallback(() => {
    getLLMSettings()
      .then((data) => {
        setApiBase(data.api_base || "https://api.openai.com/v1");
        setModel(data.model || "gpt-4o-mini");
        setKeySet(data.api_key_set || false);
        setCustomBase(!detectProvider(data.api_base || ""));
        const detected = detectProvider(data.api_base || "");
        if (detected && !detected.models.includes(data.model || "")) {
          setCustomModel(true);
        } else {
          setCustomModel(false);
        }
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  useEffect(() => {
    if (open && !loaded) loadFromServer();
  }, [open, loaded, loadFromServer]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  const handleProviderSelect = (p: Provider) => {
    setApiBase(p.base);
    setCustomBase(false);
    if (!p.models.includes(model)) {
      setModel(p.models[0]);
      setCustomModel(false);
    }
    setMsg(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const data = await updateLLMSettings({
        api_key: apiKey || "",
        api_base: apiBase || "",
        model: model || "",
      });
      if (data.api_key_set !== undefined) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ api_base: apiBase, model }));
        setKeySet(data.api_key_set || false);
        setMsg({ text: "保存成功", ok: true });
        if (apiKey) setApiKey("");
      } else {
        setMsg({ text: "保存失败", ok: false });
      }
    } catch {
      setMsg({ text: "连接失败，请检查后端是否启动", ok: false });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMsg(null);
    try {
      const data = await testLLMConnection();
      if (data.ok) {
        setMsg({ text: `连接成功: ${data.reply || "OK"}`, ok: true });
      } else {
        setMsg({ text: "连接失败", ok: false });
      }
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : "连接测试失败";
      setMsg({ text: errMsg, ok: false });
    } finally {
      setTesting(false);
    }
  };

  if (!open) return null;

  const inputStyle: React.CSSProperties = {
    fontSize: 14, padding: "10px 12px",
    background: "var(--bg-secondary)", color: "var(--color-text-primary)",
    border: "1px solid var(--color-border-subtle)",
    fontFamily: "var(--font-mono)", outline: "none", width: "100%", boxSizing: "border-box",
    transition: "border-color 0.15s, box-shadow 0.15s",
  };
  const labelStyle: React.CSSProperties = {
    fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)",
    textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6,
  };
  const focusProps = {
    onFocus: (e: React.FocusEvent<HTMLInputElement>) => {
      e.currentTarget.style.borderColor = "var(--color-scholar-blue)";
      e.currentTarget.style.boxShadow = "0 0 0 2px rgba(45,62,95,0.12)";
    },
    onBlur: (e: React.FocusEvent<HTMLInputElement>) => {
      e.currentTarget.style.borderColor = "var(--color-border-subtle)";
      e.currentTarget.style.boxShadow = "none";
    },
  };

  return (
    <div
      role="dialog" aria-modal="true" aria-label="AI 模型设置"
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(28,25,23,0.45)", backdropFilter: "blur(4px)",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: "100%", maxWidth: 520, maxHeight: "90vh", overflow: "auto",
        background: "var(--surface)", border: "1px solid var(--color-border)",
        boxShadow: "0 25px 50px -12px rgba(28,25,23,0.25)",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "20px 24px 16px", borderBottom: "1px solid var(--color-border)",
        }}>
          <div>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--color-ink)", fontFamily: "var(--font-serif)", margin: 0 }}>
              AI 模型设置
            </h2>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", margin: "4px 0 0" }}>
              配置 AI 解读所使用的大语言模型
            </p>
          </div>
          <button aria-label="关闭" onClick={onClose}
            style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", background: "transparent", border: "none", cursor: "pointer", color: "var(--color-text-muted)" }}>
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 24 }}>

          {/* Status */}
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "10px 14px",
            background: keySet ? "rgba(45,125,91,0.06)" : "rgba(184,74,60,0.06)",
            border: `1px solid ${keySet ? "rgba(45,125,91,0.15)" : "rgba(184,74,60,0.15)"}`,
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
              background: keySet ? "var(--el-wood)" : "var(--el-fire)",
            }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: keySet ? "var(--el-wood)" : "var(--el-fire)" }}>
              {keySet ? "API Key 已配置" : "API Key 未配置 — AI 解读功能不可用"}
            </span>
          </div>

          {/* Provider Selection */}
          <div>
            <div style={labelStyle}>选择服务商</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {PROVIDERS.map((p) => {
                const active = !customBase && provider?.id === p.id;
                return (
                  <button key={p.id} onClick={() => handleProviderSelect(p)}
                    style={{
                      padding: "10px 8px", textAlign: "left", cursor: "pointer",
                      background: active ? "rgba(45,62,95,0.06)" : "var(--bg-secondary)",
                      border: `1.5px solid ${active ? "var(--color-scholar-blue)" : "var(--color-border-subtle)"}`,
                      transition: "all 0.15s",
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 600, color: active ? "var(--color-scholar-blue)" : "var(--color-text-primary)" }}>
                      {p.name}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 2 }}>
                      {p.desc}
                    </div>
                  </button>
                );
              })}
              <button onClick={() => { setCustomBase(true); setMsg(null); }}
                style={{
                  padding: "10px 8px", textAlign: "left", cursor: "pointer",
                  background: customBase ? "rgba(45,62,95,0.06)" : "var(--bg-secondary)",
                  border: `1.5px solid ${customBase ? "var(--color-scholar-blue)" : "var(--color-border-subtle)"}`,
                  transition: "all 0.15s",
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: customBase ? "var(--color-scholar-blue)" : "var(--color-text-primary)" }}>
                  自定义
                </div>
                <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 2 }}>
                  其他 OpenAI 兼容 API
                </div>
              </button>
            </div>
          </div>

          {/* API Base URL */}
          <div>
            <div style={labelStyle}>API 地址</div>
            {customBase ? (
              <input type="url" autoComplete="off" spellCheck={false}
                placeholder="https://api.example.com/v1"
                value={apiBase}
                onChange={(e) => setApiBase(e.target.value)}
                style={inputStyle} {...focusProps}
              />
            ) : (
              <div style={{
                fontSize: 13, padding: "10px 12px", fontFamily: "var(--font-mono)",
                background: "var(--bg-secondary)", color: "var(--color-text-secondary)",
                border: "1px solid var(--color-border-subtle)", wordBreak: "break-all",
              }}>
                {apiBase}
              </div>
            )}
          </div>

          {/* API Key */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={labelStyle}>API Key</span>
              {keySet && (
                <span style={{ fontSize: 11, color: "var(--el-wood)", fontWeight: 500 }}>
                  已保存
                </span>
              )}
            </div>
            <div style={{ position: "relative" }}>
              <input
                type={showKey ? "text" : "password"}
                autoComplete="off" spellCheck={false}
                placeholder={keySet ? "留空则保持现有 Key 不变" : `${provider?.keyPrefix || "sk-"}...`}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ ...inputStyle, paddingRight: 44 }}
                {...focusProps}
              />
              <button aria-label={showKey ? "隐藏" : "显示"}
                onClick={() => setShowKey(!showKey)}
                style={{
                  position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)",
                  background: "transparent", border: "none", cursor: "pointer",
                  color: "var(--color-text-muted)", padding: 4,
                }}>
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                  {showKey
                    ? <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
                    : <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                  }
                </svg>
              </button>
            </div>
          </div>

          {/* Model Selection */}
          <div>
            <div style={labelStyle}>模型</div>
            {provider && !customModel ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {provider.models.map((m) => (
                    <button key={m} onClick={() => { setModel(m); setMsg(null); }}
                      style={{
                        padding: "8px 14px", fontSize: 13, fontFamily: "var(--font-mono)",
                        cursor: "pointer", fontWeight: model === m ? 600 : 400,
                        background: model === m ? "rgba(45,62,95,0.08)" : "var(--bg-secondary)",
                        border: `1.5px solid ${model === m ? "var(--color-scholar-blue)" : "var(--color-border-subtle)"}`,
                        color: model === m ? "var(--color-scholar-blue)" : "var(--color-text-primary)",
                        transition: "all 0.15s",
                      }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                <button onClick={() => setCustomModel(true)}
                  style={{
                    fontSize: 12, color: "var(--color-scholar-blue)", background: "none",
                    border: "none", cursor: "pointer", padding: "4px 0", textAlign: "left",
                    textDecoration: "underline", textUnderlineOffset: "2px",
                  }}>
                  输入其他模型名称
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <input type="text" autoComplete="off" spellCheck={false}
                  placeholder="输入模型名称，如 mimo-v2.5-pro"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  style={inputStyle} {...focusProps}
                />
                {provider && (
                  <button onClick={() => { setCustomModel(false); setModel(provider.models[0]); }}
                    style={{
                      fontSize: 12, color: "var(--color-scholar-blue)", background: "none",
                      border: "none", cursor: "pointer", padding: "4px 0", textAlign: "left",
                      textDecoration: "underline", textUnderlineOffset: "2px",
                    }}>
                    返回选择 {provider.name} 模型
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Message */}
          {msg && (
            <div aria-live="polite" style={{
              fontSize: 13, fontWeight: 500,
              color: msg.ok ? "var(--el-wood)" : "var(--el-fire)",
              padding: "10px 14px",
              background: msg.ok ? "rgba(45,125,91,0.06)" : "rgba(184,74,60,0.06)",
              border: `1px solid ${msg.ok ? "rgba(45,125,91,0.15)" : "rgba(184,74,60,0.15)"}`,
              wordBreak: "break-all",
            }}>
              {msg.text}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "16px 24px 20px", borderTop: "1px solid var(--color-border)",
        }}>
          <button onClick={handleTest} disabled={testing || !keySet}
            style={{
              fontSize: 13, fontWeight: 500, padding: "8px 16px",
              background: "transparent", border: "1px solid var(--color-border)",
              color: "var(--color-text-primary)", cursor: testing || !keySet ? "not-allowed" : "pointer",
              fontFamily: "var(--font-sans)", opacity: testing || !keySet ? 0.5 : 1,
              display: "flex", alignItems: "center", gap: 6,
            }}>
            {testing ? (
              <><span style={{ display: "inline-block", width: 12, height: 12, border: "2px solid var(--color-border)", borderTopColor: "var(--color-scholar-blue)", borderRadius: "50%", animation: "spin 0.6s linear infinite" }} /> 测试中…</>
            ) : "测试连接"}
          </button>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={onClose}
              style={{
                fontSize: 14, fontWeight: 500, padding: "9px 20px",
                background: "transparent", border: "1px solid var(--color-border)",
                color: "var(--color-text-primary)", cursor: "pointer", fontFamily: "var(--font-sans)",
              }}>
              取消
            </button>
            <button onClick={handleSave} disabled={saving}
              style={{
                fontSize: 14, fontWeight: 600, padding: "9px 24px",
                background: "var(--color-scholar-blue)", border: "none",
                color: "#fff", cursor: saving ? "wait" : "pointer", fontFamily: "var(--font-sans)",
                opacity: saving ? 0.7 : 1,
              }}>
              {saving ? "保存中…" : "保存"}
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
