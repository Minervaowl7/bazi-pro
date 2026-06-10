"use client";

import { WUXING_COLORS, GAN_WUXING, ZHI_WUXING } from "@/lib/constants";

interface ReportCoverProps {
  name?: string;
  dayMaster?: string;
  bazi?: string;
  pattern?: string;
  yongshen?: string;
  wangshuai?: string;
  gender?: string;
  zodiac?: string;
  createdAt?: string;
}

export default function ReportCover({
  name,
  dayMaster,
  bazi,
  pattern,
  yongshen,
  wangshuai,
  gender,
  zodiac,
  createdAt,
}: ReportCoverProps) {
  const displayName = name || "命主";
  const dateStr = createdAt
    ? new Date(createdAt).toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : new Date().toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });

  // 日主五行色
  const dmWx = dayMaster ? GAN_WUXING[dayMaster] : "";
  const dmColor = dmWx ? WUXING_COLORS[dmWx] : "var(--cinnabar)";

  // 八字拆分为四柱，逐字着色（过滤非汉字分隔符）
  const baziChars = bazi ? bazi.replace(/\s+/g, "").split("").filter(ch => /\p{Unified_Ideograph}/u.test(ch)) : [];

  const INFO_ITEMS = [
    { label: "格局", value: pattern, accent: true },
    { label: "用神", value: yongshen, accent: true },
    { label: "旺衰", value: wangshuai, accent: false },
    { label: "生肖", value: zodiac, accent: false },
  ];

  return (
    <div
      style={{
        background: "var(--surface)",
        borderRadius: "var(--r)",
        border: "1px solid var(--border)",
        overflow: "hidden",
      }}
    >
      {/* 顶部装饰带 */}
      <div
        style={{
          height: 3,
          background:
            "linear-gradient(90deg, var(--cinnabar), var(--gold), var(--jade))",
          opacity: 0.6,
        }}
      />

      {/* 封面内容 */}
      <div className="px-8 py-10 text-center">
        {/* 日主印章 — 增加内阴影和光泽感 */}
        <div className="flex justify-center mb-6">
          <div
            style={{
              width: 92,
              height: 92,
              borderRadius: "50%",
              background: `linear-gradient(145deg, ${dmColor}, color-mix(in srgb, ${dmColor} 70%, #000))`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: `0 8px 32px color-mix(in srgb, ${dmColor} 30%, transparent), inset 0 2px 4px rgba(255,255,255,0.15)`,
              position: "relative",
            }}
          >
            {/* 内圈装饰 */}
            <div
              style={{
                position: "absolute",
                inset: 4,
                borderRadius: "50%",
                border: "1px solid rgba(255,255,255,0.15)",
              }}
            />
            <span
              style={{
                fontSize: 42,
                color: "#fff",
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                lineHeight: 1,
                textShadow: "0 1px 2px rgba(0,0,0,0.2)",
              }}
            >
              {dayMaster || "—"}
            </span>
          </div>
        </div>

        {/* 姓名 */}
        <h1
          style={{
            fontSize: 30,
            fontWeight: 700,
            color: "var(--ink)",
            fontFamily: "var(--font-display)",
            letterSpacing: "0.1em",
            marginBottom: 6,
          }}
        >
          {displayName}
        </h1>

        {/* 副标题 */}
        <p
          style={{
            fontSize: 13,
            color: "var(--text-3)",
            fontFamily: "var(--font-display)",
            marginBottom: 28,
          }}
        >
          详批报告 · {dateStr}
        </p>

        {/* 八字展示 — 逐字五行着色 */}
        <div
          className="inline-flex items-center gap-0.5 px-8 py-3.5 rounded-lg mb-8"
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
          }}
        >
          {baziChars.length > 0 ? (
            baziChars.map((ch, i) => {
              const wx = GAN_WUXING[ch] || ZHI_WUXING[ch] || "";
              const color = wx ? WUXING_COLORS[wx] : "var(--ink)";
              return (
                <span
                  key={i}
                  style={{
                    fontSize: 20,
                    fontFamily: "var(--font-display)",
                    fontWeight: 600,
                    color,
                    letterSpacing: "0.02em",
                    margin: "0 3px",
                  }}
                >
                  {ch}
                </span>
              );
            })
          ) : (
            <span
              style={{
                fontSize: 18,
                fontFamily: "var(--font-display)",
                fontWeight: 600,
                color: "var(--text-4)",
                letterSpacing: "0.15em",
              }}
            >
              — — — —
            </span>
          )}
        </div>

        {/* 信息卡片 — 增加顶部 accent 线 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {INFO_ITEMS.map((item) => (
            <div
              key={item.label}
              className="px-4 py-3.5 rounded-lg text-center relative overflow-hidden"
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
              }}
            >
              {/* 顶部 accent 线 */}
              {item.accent && (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: "25%",
                    right: "25%",
                    height: 2,
                    background: `linear-gradient(90deg, transparent, var(--gold), transparent)`,
                    opacity: 0.5,
                  }}
                />
              )}
              <div
                className="text-[11px] mb-1.5 tracking-wide"
                style={{ color: "var(--text-3)" }}
              >
                {item.label}
              </div>
              <div
                className="text-sm font-semibold"
                style={{
                  color: item.accent ? "var(--cinnabar)" : "var(--ink)",
                  fontFamily: "var(--font-display)",
                }}
              >
                {item.value || "—"}
              </div>
            </div>
          ))}
        </div>

        {/* 专属标注 */}
        <div
          className="mt-8 pt-6"
          style={{ borderTop: "1px solid var(--border-subtle)" }}
        >
          <p
            className="text-[11px] tracking-wide"
            style={{ color: "var(--text-4)" }}
          >
            本报告专为 {displayName} 生成 · 基于确定性命理计算
          </p>
        </div>
      </div>
    </div>
  );
}
