"use client";

import { useState } from "react";

interface ShenShaItem { name:string; position:string; type:string; desc?:string; }
interface Props { result: Record<string,unknown>; }

const TYPE_STYLES:{[k:string]:{bg:string;color:string;border:string}}={
  吉:{bg:"rgba(45,125,91,0.07)",color:"var(--success)",border:"rgba(45,125,91,0.16)"},
  凶:{bg:"rgba(196,60,44,0.07)",color:"var(--danger)",border:"rgba(196,60,44,0.16)"},
  中:{bg:"rgba(184,146,63,0.07)",color:"var(--warning)",border:"rgba(184,146,63,0.14)"},
};
const POSITION_ORDER=["年","月","日","时"];

export default function ShenShaPanel({ result }: Props) {
  const shensha=result.shensha as ShenShaItem[]|undefined;
  const [expanded,setExpanded]=useState(true);
  if (!shensha||shensha.length===0) return null;

  const grouped:{[pos:string]:ShenShaItem[]}={};
  for (const pos of POSITION_ORDER) {
    const items=shensha.filter(s=>s.position===pos);
    if (items.length>0) grouped[pos]=items;
  }
  const ungrouped=shensha.filter(s=>!POSITION_ORDER.includes(s.position));
  if (ungrouped.length>0) grouped["其他"]=ungrouped;

  return (
    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)",boxShadow:"var(--shadow-sm)"}}>
      <button
        aria-expanded={expanded}
        className="w-full flex items-center justify-between transition-colors duration-150 hover:bg-[var(--bg-hover)]"
        style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}}
        onClick={()=>setExpanded(!expanded)}
      >
        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>神煞</h3>
        <div className="flex items-center gap-3">
          <span style={{fontSize:13,color:"var(--color-text-faint)"}}>{shensha.length}个</span>
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="transition-transform duration-200" style={{color:"var(--color-text-faint)",transform:expanded?"rotate(180deg)":"rotate(0)"}}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="p-7 space-y-6">
          {Object.entries(grouped).map(([pos,items])=>(
            <div key={pos}>
              <div className="mb-3 font-semibold uppercase tracking-wider" style={{fontSize:13,color:"var(--color-text-faint)",letterSpacing:"0.08em"}}>
                {POSITION_ORDER.includes(pos)?`${pos}柱`:pos}
              </div>
              <div className="space-y-2">
                {items.map((item,i)=>{
                  const style=TYPE_STYLES[item.type]||TYPE_STYLES["中"];
                  return (
                    <div key={i} className="flex items-start gap-3 px-4 py-2.5 transition-colors duration-150 hover:bg-[var(--bg-hover)]" style={{background:"var(--bg-secondary)"}}>
                      <span className="font-bold shrink-0 px-2.5 py-1" style={{fontSize:13,background:style.bg,color:style.color,border:`1px solid ${style.border}`}}>{item.name}</span>
                      {item.desc&&<span style={{fontSize:14,color:"var(--color-text-muted)"}}>{item.desc}</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
