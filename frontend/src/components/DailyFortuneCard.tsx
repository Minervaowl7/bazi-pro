"use client";

import { useEffect, useState } from "react";
import { getDailyFortune, type DailyFortune } from "@/lib/api";

const LEVEL_COLORS:{[k:string]:string}={"大吉":"var(--wx-wood)","吉":"var(--wx-wood)","中吉":"var(--scholar-blue)","小吉":"var(--scholar-blue)","平":"var(--text-3)","中凶":"var(--wx-fire)","小凶":"var(--wx-fire)","凶":"var(--wx-fire)","大凶":"var(--wx-fire)"};
interface Props { analysisId:string; }

export default function DailyFortuneCard({ analysisId }:Props) {
  const [fortune,setFortune]=useState<DailyFortune|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState(false);

  useEffect(()=>{
    const ac=new AbortController();
    getDailyFortune(analysisId).then(data=>{if(!ac.signal.aborted&&data.date)setFortune(data);}).catch(()=>{if(!ac.signal.aborted)setError(true);}).finally(()=>{if(!ac.signal.aborted)setLoading(false);});
    return ()=>{ac.abort();};
  },[analysisId]);

  if (loading) return (
    <section className="card" style={{borderRadius:12}}>
      <div className="p-7 flex items-center justify-center" style={{minHeight:120}}>
        <div className="flex items-center gap-2" style={{color:"var(--text-3)"}}>
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25"/><path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/></svg>
          <span style={{fontSize:13}}>加载运势中...</span>
        </div>
      </div>
    </section>
  );

  if (error||!fortune) return null;
  const levelColor=LEVEL_COLORS[fortune.overall_level]||"var(--text-3)";

  return (
    <section style={{background:"var(--surface)",border:"1px solid var(--border)",boxShadow:"var(--shadow-sm)",borderRadius:12}}>
      <div style={{borderBottom:"1px solid var(--border)",padding:"16px 24px"}} className="flex items-center justify-between">
        <h3 className="font-bold" style={{fontSize:16,color:"var(--ink)",fontFamily:"var(--font-display)"}}>今日运势</h3>
        <span style={{fontSize:13,color:"var(--text-4)"}}>{fortune.gan_zhi}日</span>
      </div>
      <div className="p-7">
        <div className="text-center mb-5">
          <span className="font-bold" style={{fontSize:28,color:levelColor}}>{fortune.overall_level}</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {Object.entries(fortune.dimensions).filter(([k])=>k!=="整体").slice(0,6).map(([dim,data])=>(
            <div key={dim} className="text-center py-3">
              <div style={{fontSize:12,color:"var(--text-4)"}}>{dim}</div>
              <div className="font-semibold mt-1" style={{fontSize:15,color:LEVEL_COLORS[data.level]||"var(--text-3)"}}>{data.level}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
