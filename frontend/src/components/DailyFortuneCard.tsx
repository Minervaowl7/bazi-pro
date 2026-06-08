"use client";

import { useEffect, useState } from "react";
import { getDailyFortune, type DailyFortune } from "@/lib/api";

const LEVEL_COLORS:{[k:string]:string}={"大吉":"var(--wx-wood)","吉":"var(--wx-wood)","中吉":"var(--scholar-blue)","小吉":"var(--scholar-blue)","平":"var(--text-3)","中凶":"var(--wx-fire)","小凶":"var(--wx-fire)","凶":"var(--wx-fire)","大凶":"var(--wx-fire)"};
interface Props { analysisId:string; }

export default function DailyFortuneCard({ analysisId }:Props) {
  const [fortune,setFortune]=useState<DailyFortune|null>(null);

  useEffect(()=>{
    const ac=new AbortController();
    getDailyFortune(analysisId).then(data=>{if(!ac.signal.aborted&&data.date)setFortune(data);}).catch(()=>{});
    return ()=>{ac.abort();};
  },[analysisId]);

  if (!fortune) return null;
  const levelColor=LEVEL_COLORS[fortune.overall_level]||"var(--text-3)";

  return (
    <section style={{background:"var(--surface)",border:"1px solid var(--border)",boxShadow:"var(--shadow-sm)"}}>
      <div style={{borderBottom:"2px solid var(--border-strong)",padding:"16px 24px"}} className="flex items-center justify-between">
        <h3 className="font-bold" style={{fontSize:16,color:"var(--ink)",fontFamily:"var(--font-display)"}}>今日运势</h3>
        <span style={{fontSize:13,color:"var(--text-4)"}}>{fortune.gan_zhi}日</span>
      </div>
      <div className="p-7">
        <div className="text-center mb-5">
          <span className="font-bold" style={{fontSize:28,color:levelColor}}>{fortune.overall_level}</span>
        </div>
        <div className="grid grid-cols-3 gap-4">
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
