"use client";

import BirthForm from "@/components/BirthForm";

const FEATURES = [
  { title: "确定性计算", desc: "十神、藏干、五行力量、旺衰、格局、喜用神，全部确定性推导，零 LLM 参与", icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" },
  { title: "古籍引证", desc: "2964 条古籍语料，6 部经典（子平真诠/滴天髓/渊海子平/穷通宝鉴/神峰通考/三命通会）", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { title: "三大流派", desc: "子平法（格局用神）、盲派（宾主做功）、新派（百神空亡），一键对比三种视角", icon: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6z" },
  { title: "破格检测", desc: "六层格局筛查 + 破格条件检测，每个破格类型均有古籍原文依据", icon: "M13 10V3L4 14h7v7l9-11h-7z" },
];

export default function Home() {
  return (
    <div style={{minHeight:"calc(100vh - 3.5rem)",background:"var(--background)"}}>
      <div style={{width:"100%",display:"flex",justifyContent:"center"}}>
        <div style={{width:"100%",maxWidth:900,paddingLeft:32,paddingRight:32}}>

          {/* ===== Hero ===== */}
          <section style={{paddingTop:56,paddingBottom:48,textAlign:"center"}}>

            <span
              style={{
                display:"inline-flex",
                alignItems:"center",
                gap:8,
                paddingLeft:16,
                paddingRight:16,
                paddingTop:6,
                paddingBottom:6,
                marginBottom:32,
                fontSize:12,
                fontWeight:600,
                background:"rgba(61,107,89,0.06)",
                color:"var(--color-jade)",
                border:"1px solid rgba(61,107,89,0.15)",
                letterSpacing:"0.04em",
              }}
            >
              <span style={{width:6,height:6,borderRadius:"50%",background:"var(--success)",animation:"pulse 2s infinite"}} />
              v5.2 · 典籍对齐版
            </span>

            <h1 style={{fontSize:44,fontWeight:700,lineHeight:1.15,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)",marginBottom:20}}>
              确定性八字
              <br />
              <span style={{color:"var(--color-scholar-blue)"}}>命理引擎</span>
            </h1>

            <p style={{
              fontSize:17,lineHeight:1.85,color:"var(--color-text-secondary)",
              maxWidth:520,margin:"0 auto 36px auto",
            }}>
              算析分离架构，核心计算零 LLM 依赖。
              十神推导、格局筛查、喜用神判定，
              每一步均可追溯到确定性规则与古籍原文。
            </p>

            {/* 统计数字 */}
            <div style={{display:"flex",justifyContent:"center",gap:40,marginBottom:40}}>
              {[
                {value:"507",label:"Golden Cases"},
                {value:"13",label:"核心模块"},
                {value:"6",label:"经典古籍"},
                {value:"3",label:"分析流派"},
              ].map(s=>(
                <div key={s.label} style={{textAlign:"center"}}>
                  <div style={{
                    fontSize:28,fontWeight:700,color:"var(--color-scholar-blue)",
                    fontFamily:"var(--font-serif)",letterSpacing:"-0.02em",
                  }}>{s.value}</div>
                  <div style={{
                    marginTop:4,fontSize:10,textTransform:"uppercase",
                    letterSpacing:"0.12em",color:"var(--color-text-faint)",fontWeight:500,
                  }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* ===== 表单卡片 ===== */}
            <div style={{
              display:"inline-block",
              textAlign:"left",
              background:"var(--surface)",
              boxShadow:"var(--shadow-lg)",
              border:"1px solid var(--color-border)",
              padding:"36px 40px",
              maxWidth:420,width:"100%",
            }}>
              <BirthForm />
            </div>
          </section>

          {/* 分隔线 */}
          <div style={{
            width:"100%",maxWidth:240,margin:"0 auto 48px auto",
            height:1,background:"linear-gradient(90deg,transparent,var(--color-border-strong),transparent)",
          }} />

          {/* ===== Features ===== */}
          <section style={{paddingBottom:56}}>
            <div style={{textAlign:"center",marginBottom:40}}>
              <h2 style={{fontSize:26,fontWeight:700,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)",marginBottom:10}}>核心能力</h2>
              <p style={{fontSize:15,color:"var(--color-text-muted)"}}>每一项计算结果都可追溯，每一条引证都有出处</p>
            </div>

            <div style={{
              display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:20,maxWidth:800,margin:"0 auto",
            }}>
              {FEATURES.map(f=>(
                <div key={f.title} style={{
                  padding:28,background:"var(--surface)",border:"1px solid var(--color-border)",
                  transition:"background-color 0.2s",
                }}
                onMouseEnter={(e)=>{e.currentTarget.style.background="var(--bg-hover)";}}
                onMouseLeave={(e)=>{e.currentTarget.style.background="var(--surface)";}}
                >
                  <div style={{
                    width:48,height:48,display:"flex",alignItems:"center",justifyContent:"center",
                    marginBottom:16,background:"var(--accent-dim)",
                  }}>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"
                      style={{color:"var(--color-scholar-blue)"}}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d={f.icon}/>
                    </svg>
                  </div>
                  <h3 style={{fontSize:17,fontWeight:700,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)",marginBottom:8}}>{f.title}</h3>
                  <p style={{fontSize:14,lineHeight:1.75,color:"var(--color-text-muted)"}}>{f.desc}</p>
                </div>
              ))}
            </div>
          </section>

        </div>
      </div>

      <footer style={{
        borderTop:"1px solid var(--color-border)",
        paddingTop:32,paddingBottom:32,textAlign:"center",
      }}>
        <p style={{
          fontSize:11,letterSpacing:"0.05em",color:"var(--color-text-faint)",
        }}>bazi-pro · 确定性命理引擎 · 算析分离 · 古籍引证 · 零幻觉</p>
      </footer>
    </div>
  );
}
