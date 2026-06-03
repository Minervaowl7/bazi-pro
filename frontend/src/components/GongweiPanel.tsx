"use client";

interface Props { result: Record<string,unknown>; }

export default function GongweiPanel({ result }: Props) {
  const gongwei=result.gongwei as Record<string,string>|undefined;
  if (!gongwei||Object.keys(gongwei).length===0) return null;

  const items=Object.entries(gongwei);

  return (
    <section style={{background:"var(--surface)",border:"1px solid var(--color-border)",boxShadow:"var(--shadow-sm)"}}>
      <div style={{borderBottom:"2px solid var(--color-border-strong)",padding:"16px 24px"}}>
        <h3 className="font-bold" style={{fontSize:16,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>宫位信息</h3>
      </div>
      <div className="p-7 grid grid-cols-2 sm:grid-cols-3 gap-5">
        {items.map(([label,value])=>(
          <div key={label} className="text-center p-5" style={{background:"var(--bg-secondary)"}}>
            <div className="mb-2 font-semibold uppercase tracking-wider" style={{fontSize:12,color:"var(--color-text-faint)",letterSpacing:"0.08em"}}>{label}</div>
            <div className="font-bold" style={{fontSize:22,color:"var(--color-text-primary)",fontFamily:"var(--font-serif)"}}>{value}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
