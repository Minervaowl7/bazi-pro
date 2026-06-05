"use client";

import BirthForm from "@/components/BirthForm";

export default function Home() {
  return (
    <div style={{ minHeight: "calc(100vh - 3.5rem)", position: "relative", zIndex: 1 }}>

      {/* ===== Hero: 全幅视觉锚点 ===== */}
      <section style={{
        position: "relative",
        minHeight: "calc(100vh - 3.5rem)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px 32px 100px",
        overflow: "hidden",
      }}>
        {/* 背景装饰：五行方位圆环 */}
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "min(600px, 85vw)",
          height: "min(600px, 85vw)",
          borderRadius: "50%",
          border: "1px solid var(--color-border-subtle)",
          opacity: 0.4,
          pointerEvents: "none",
        }} />
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "min(420px, 60vw)",
          height: "min(420px, 60vw)",
          borderRadius: "50%",
          border: "1px solid var(--color-border-subtle)",
          opacity: 0.3,
          pointerEvents: "none",
        }} />

        {/* 五行方位文字 */}
        {[
          { wx: "木", angle: -90, color: "var(--el-wood)" },
          { wx: "火", angle: -18, color: "var(--el-fire)" },
          { wx: "土", angle: 54, color: "var(--el-earth)" },
          { wx: "金", angle: 126, color: "var(--el-metal)" },
          { wx: "水", angle: 198, color: "var(--el-water)" },
        ].map(({ wx, angle, color }) => {
          const rad = (angle * Math.PI) / 180;
          return (
            <span key={wx} className="hidden sm:block" style={{
              position: "absolute",
              top: `calc(50% + ${Math.sin(rad) * 260}px)`,
              left: `calc(50% + ${Math.cos(rad) * 260}px)`,
              transform: "translate(-50%, -50%)",
              fontSize: 28,
              fontFamily: "var(--font-serif)",
              fontWeight: 700,
              color,
              opacity: 0.12,
              pointerEvents: "none",
              userSelect: "none",
            }}>
              {wx}
            </span>
          );
        })}

        {/* 品牌印章 */}
        <div style={{
          marginBottom: 36,
          animation: "sealStamp 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: 12,
            background: "linear-gradient(135deg, var(--color-cinnabar), #8f3028)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 20px rgba(184,74,60,0.2)",
            position: "relative",
          }}>
            <span style={{
              fontSize: 30,
              color: "#fff",
              fontFamily: "var(--font-serif)",
              fontWeight: 700,
              letterSpacing: "0.05em",
            }}>命</span>
            {/* 印章边框纹理 */}
            <div style={{
              position: "absolute",
              inset: 3,
              borderRadius: 9,
              border: "1.5px solid rgba(255,255,255,0.15)",
              pointerEvents: "none",
            }} />
          </div>
        </div>

        {/* 主标题 */}
        <h1 style={{
          fontSize: 56,
          fontWeight: 700,
          lineHeight: 1.08,
          color: "var(--color-text-primary)",
          fontFamily: "var(--font-serif)",
          marginBottom: 20,
          letterSpacing: "-0.025em",
          textAlign: "center",
          position: "relative",
          zIndex: 1,
        }}>
          八字排盘
          <br />
          <span style={{
            background: "linear-gradient(135deg, var(--color-scholar-blue) 0%, var(--color-jade) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            fontSize: 44,
          }}>古法定盘 · 智能解读</span>
        </h1>

        <p style={{
          fontSize: 15,
          lineHeight: 1.9,
          color: "var(--color-text-muted)",
          maxWidth: 400,
          textAlign: "center",
          marginBottom: 48,
          position: "relative",
          zIndex: 1,
        }}>
          每一步可追溯至古籍原文，零幻觉。
        </p>

        {/* 表单卡片 */}
        <div style={{
          textAlign: "left",
          background: "var(--surface)",
          boxShadow: "var(--shadow-xl)",
          border: "1px solid var(--color-border)",
          borderRadius: 16,
          padding: "40px 44px",
          maxWidth: 420,
          width: "100%",
          position: "relative",
          zIndex: 1,
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 3,
            background: "linear-gradient(90deg, var(--color-cinnabar), var(--color-gold), var(--color-jade))",
            opacity: 0.5,
          }} />
          <BirthForm />
        </div>
      </section>

      {/* ===== 底部能力条 ===== */}
      <div style={{
        borderTop: "1px solid var(--color-border)",
        background: "var(--surface)",
        padding: "28px 32px",
      }}>
        <div style={{
          maxWidth: 900,
          margin: "0 auto",
          display: "flex",
          justifyContent: "center",
          gap: 48,
          flexWrap: "wrap",
        }}>
          {[
            { icon: "算", label: "确定性计算", sub: "零 LLM" },
            { icon: "典", label: "古籍引证", sub: "2964 条" },
            { icon: "派", label: "三大流派", sub: "一键对比" },
            { icon: "格", label: "破格检测", sub: "六层筛查" },
          ].map((f, i) => (
            <div key={i} style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}>
              <span style={{
                width: 36,
                height: 36,
                borderRadius: 8,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 15,
                fontFamily: "var(--font-serif)",
                fontWeight: 700,
                background: i === 0 ? "rgba(61,107,89,0.07)" :
                            i === 1 ? "rgba(161,127,64,0.07)" :
                            i === 2 ? "rgba(45,62,95,0.06)" :
                                      "rgba(184,74,60,0.06)",
                color: i === 0 ? "var(--color-jade)" :
                       i === 1 ? "var(--color-gold)" :
                       i === 2 ? "var(--color-scholar-blue)" :
                                 "var(--color-cinnabar)",
              }}>{f.icon}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>{f.label}</div>
                <div style={{ fontSize: 11, color: "var(--color-text-faint)", marginTop: 1 }}>{f.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 页脚 */}
      <footer style={{
        padding: "32px 32px 40px",
        textAlign: "center",
        position: "relative",
        zIndex: 1,
      }}>
        <p style={{
          fontSize: 11,
          letterSpacing: "0.06em",
          color: "var(--color-text-faint)",
        }}>
          bazi-pro · v5.3
        </p>
      </footer>
    </div>
  );
}
