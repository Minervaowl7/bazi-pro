"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import RemarkGfm from "remark-gfm";
import { sendChatMessage, getChatHistory, type ChatMessage } from "@/lib/api";

function CitationsBlock({ citations }: { citations?: string }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.trim().length === 0) return null;
  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs font-medium transition-colors duration-150"
        style={{ color: "var(--color-text-faint)" }}
        onMouseEnter={(e) => { e.currentTarget.style.color = "var(--color-scholar-blue)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.color = "var(--color-text-faint)"; }}
      >
        {open ? "▾ 收起古籍依据" : "▸ 查看古籍依据"}
      </button>
      {open && (
        <div
          className="mt-2 px-3 py-2.5 rounded-md text-xs leading-relaxed"
          style={{
            background: "var(--bg-card)",
            color: "var(--text-muted)",
            border: "1px solid var(--border)",
          }}
        >
          {citations}
        </div>
      )}
    </div>
  );
}

const QUICK_QUESTIONS = [
  "我的事业发展方向是什么？",
  "我的感情运势如何？",
  "今年运势怎么样？",
  "我的性格特点是什么？",
  "适合什么样的职业？",
  "健康方面需要注意什么？",
];

interface Props { analysisId: string; school?: string; }

export default function ChatPanel({ analysisId, school = "ziping" }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showQuick, setShowQuick] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    let cancelled = false;
    mountedRef.current = true;
    getChatHistory(analysisId, school).then((data) => {
      if (cancelled) return;
      if (data.messages && data.messages.length > 0) { setMessages(data.messages); setShowQuick(false); }
    }).catch(() => {});
    return () => { cancelled = true; mountedRef.current = false; };
  }, [analysisId, school]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?:string){
    const message=text||input.trim();
    if(!message||loading)return;
    setInput("");setError("");setShowQuick(false);
    setMessages(prev=>[...prev,{role:"user",content:message}]);
    setLoading(true);
    try{
      const data=await sendChatMessage(analysisId,message,school);
      if(!mountedRef.current)return;
      setMessages(prev=>[...prev,{role:"assistant",content:data.reply,citations:data.citations}]);
    }catch(err){
      if(!mountedRef.current)return;
      const errMsg=err instanceof Error?err.message:"发送失败";
      if(errMsg.includes("LLM")&&(errMsg.includes("未配置")||errMsg.includes("503")||errMsg.includes("not configured"))){
        setError("LLM 服务未配置。请在服务端设置 LLM_API_KEY 环境变量后重启。");
      }else{setError(errMsg);}
    }finally{
      if(mountedRef.current)setLoading(false);
    }
  }

  function handleKeyDown(e:React.KeyboardEvent){if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();handleSend();}}

  return (
    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)",boxShadow:"var(--shadow-sm)"}}>
      <div style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-bold" style={{fontSize:18,color:"var(--color-cinnabar)",fontFamily:"var(--font-serif)"}}>☯</span>
          <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>命理问答</h3>
        </div>
        <span style={{fontSize:13,color:"var(--color-text-faint)"}}>基于命盘数据 · AI 解读</span>
      </div>

      <div className="max-h-[600px] overflow-y-auto px-7 py-6" style={{minHeight:120}}>
        {messages.length===0&&!loading&&(
          <div className="text-center py-10">
            <p style={{fontSize:16,color:"var(--color-text-secondary)"}}>向命理师提问，深入了解你的命盘</p>
            <p style={{fontSize:14,color:"var(--color-text-faint)"}}>基于你的八字数据，AI 将给出针对性解读</p>
          </div>
        )}

        {messages.map((msg,i)=>(
          <div key={i} className={`mb-5 ${msg.role==="user"?"flex justify-end":""}`}>
            {msg.role==="assistant"?(
              <div className="pr-12">
                <div className="flex items-center gap-2 mb-2">
                  <span style={{fontSize:17,color:"var(--color-cinnabar)"}}>☯</span>
                  <span className="font-semibold uppercase tracking-wider" style={{fontSize:12,color:"var(--color-scholar-blue)",fontFamily:"var(--font-serif)",letterSpacing:"0.06em"}}>命理师</span>
                </div>
                <div className="markdown-body" style={{color:"var(--color-text-secondary)",lineHeight:1.8,fontSize:15}}>
                  <ReactMarkdown remarkPlugins={[RemarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
                <CitationsBlock citations={msg.citations} />
              </div>
            ):(
              <div className="max-w-[80%]">
                <div className="px-4 py-3 whitespace-pre-wrap" style={{
                  fontSize:15,lineHeight:1.7,color:"var(--color-text-primary)",
                  background:"var(--bg-secondary)",border:"1px solid var(--color-border-subtle)",
                }}>
                  {msg.content}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="mb-5 pr-12">
            <div className="flex items-center gap-2 mb-2">
              <span style={{fontSize:17,color:"var(--color-cinnabar)"}}>☯</span>
              <span className="font-semibold uppercase tracking-wider" style={{fontSize:12,color:"var(--color-scholar-blue)",fontFamily:"var(--font-serif)",letterSpacing:"0.06em"}}>命理师</span>
            </div>
            <div className="p-5 space-y-3" style={{background:"var(--bg-secondary)",border:"1px solid var(--color-border-subtle)"}}>
              {["正在分析命盘数据…","检索古籍条文…","生成解读…"].map((label,idx)=>(
                <div key={idx} className="flex items-center gap-3">
                  <span className="w-1.5 h-1.5 animate-pulse" style={{background:"var(--color-scholar-blue)"}} />
                  <span style={{fontSize:14,color:"var(--color-text-muted)"}}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="px-7 py-3 border-t" style={{borderColor:"var(--color-border-subtle)"}}>
          <p className="font-medium" style={{fontSize:13,color:"var(--danger)"}}>{error}</p>
        </div>
      )}

      {showQuick&&messages.length===0&&(
        <div className="px-7 py-5 border-t" style={{borderColor:"var(--color-border-subtle)"}}>
          <p className="mb-3 font-semibold uppercase tracking-wider" style={{fontSize:13,color:"var(--color-text-faint)",letterSpacing:"0.08em"}}>快捷提问</p>
          <div className="flex flex-wrap gap-2.5">
            {QUICK_QUESTIONS.map((q,i)=>(
              <button key={i} onClick={()=>handleSend(q)} disabled={loading}
                className="px-4 py-2.5 font-medium transition-colors duration-150 disabled:opacity-50"
                style={{
                  fontSize:13,
                  color:"var(--color-text-secondary)",
                  background:"var(--bg-secondary)",
                  border:"1px solid var(--color-border-subtle)",
                }}
                onMouseEnter={(e)=>{e.currentTarget.style.borderColor="rgba(45,62,95,0.25)";e.currentTarget.style.color="var(--color-scholar-blue)";}}
                onMouseLeave={(e)=>{e.currentTarget.style.borderColor="var(--color-border-subtle)";e.currentTarget.style.color="var(--color-text-secondary)";}}
              >{q}</button>
            ))}
          </div>
        </div>
      )}

      <div className="px-7 py-5 border-t sticky bottom-0" style={{borderColor:"var(--color-border-subtle)",background:"var(--surface)"}}>
        <div className="flex gap-3">
          <textarea
            ref={inputRef} value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={handleKeyDown}
            aria-label="输入你的问题"
            placeholder="输入你的问题… (Enter 发送，Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none px-4 py-3 transition-colors"
            style={{
              fontSize:15,fontFamily:"var(--font-sans)",
              background:"var(--bg-secondary)",
              border:"1px solid var(--color-border-subtle)",
              color:"var(--color-text-primary)",
              maxHeight:100,
              outline:"none",
            }}
            onFocus={(e)=>{e.currentTarget.style.borderColor="var(--color-scholar-blue)";e.currentTarget.style.boxShadow="0 0 0 2px rgba(45,62,95,0.15)";}}
            onBlur={(e)=>{e.currentTarget.style.borderColor="var(--color-border-subtle)";e.currentTarget.style.boxShadow="none";}}
            disabled={loading}
          />
          <button onClick={()=>handleSend()} disabled={loading||!input.trim()}
            className="px-6 py-3 font-semibold transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{fontSize:14,background:"var(--color-ink)",color:"var(--surface)"}}
          >
            发送
          </button>
        </div>
      </div>

      <style jsx>{`
        .markdown-body :global(h1),.markdown-body :global(h2),.markdown-body :global(h3)
          { color:var(--color-scholar-blue);margin-top:1.2rem;margin-bottom:0.55rem;font-weight:700;font-family:var(--font-serif); }
        .markdown-body :global(h1){font-size:1.35rem;} .markdown-body :global(h2){font-size:1.2rem;} .markdown-body :global(h3){font-size:1.1rem;}
        .markdown-body :global(p){line-height:1.8;font-size:15;margin-bottom:0.55rem;}
        .markdown-body :global(strong){font-weight:700;color:var(--color-text-primary);}
        .markdown-body :global(ul),.markdown-body :global(ol){padding-left:1.2rem;margin-top:0.35rem;margin-bottom:0.55rem;}
        .markdown-body :global(li){margin-top:0.35rem;font-size:15;}
        .markdown-body :global(code){font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--bg-secondary);padding:0.14rem 0.45rem;border-radius:4px;font-size:13px;}
        .markdown-body :global(pre){background:var(--bg-secondary);border-radius:4px;padding:1rem;overflow-x:auto;margin-top:0.55rem;margin-bottom:0.55rem;border:1px solid var(--color-border-subtle);}
        .markdown-body :global(pre code){background:transparent;padding:0;font-size:13px;}
        .markdown-body :global(blockquote){border-left:2.5px solid var(--color-scholar-blue);padding-left:1rem;font-style:italic;font-size:15;opacity:0.9;margin-top:0.55rem;margin-bottom:0.55rem;color:var(--color-text-secondary);}
        .markdown-body :global(hr){border-top:1px solid var(--color-border-subtle);margin-top:1.1rem;margin-bottom:1.1rem;}
        .markdown-body :global(a){color:var(--color-scholar-blue);text-decoration:underline;}
        .markdown-body :global(table){width:100%;font-size:15;border-collapse:collapse;margin-top:0.55rem;margin-bottom:0.55rem;}
        .markdown-body :global(th){background:var(--bg-secondary);padding:0.55rem 0.85rem;text-align:left;font-weight:600;border-bottom:1px solid var(--color-border-subtle);}
        .markdown-body :global(td){padding:0.55rem 0.85rem;border-bottom:1px solid var(--color-border-subtle);}
      `}</style>
    </section>
  );
}
