"use client";

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
        {/* 日主大字 */}
        <div className="flex justify-center mb-6">
          <div
            style={{
              width: 88,
              height: 88,
              borderRadius: "50%",
              background:
                "linear-gradient(135deg, var(--cinnabar), #a04030)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 8px 32px rgba(201,100,66,0.25)",
            }}
          >
            <span
              style={{
                fontSize: 40,
                color: "#fff",
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                lineHeight: 1,
              }}
            >
              {dayMaster || "—"}
            </span>
          </div>
        </div>

        {/* 姓名 */}
        <h1
          style={{
            fontSize: 28,
            fontWeight: 700,
            color: "var(--ink)",
            fontFamily: "var(--font-display)",
            letterSpacing: "0.08em",
            marginBottom: 4,
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
            marginBottom: 24,
          }}
        >
          详批报告 · {dateStr}
        </p>

        {/* 八字展示 */}
        <div
          className="inline-flex items-center gap-1 px-6 py-3 rounded-lg mb-8"
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
          }}
        >
          <span
            style={{
              fontSize: 18,
              fontFamily: "var(--font-display)",
              fontWeight: 600,
              color: "var(--ink)",
              letterSpacing: "0.15em",
            }}
          >
            {bazi || "— — — —"}
          </span>
        </div>

        {/* 信息卡片 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "格局", value: pattern },
            { label: "用神", value: yongshen },
            { label: "旺衰", value: wangshuai },
            { label: "生肖", value: zodiac },
          ].map((item) => (
            <div
              key={item.label}
              className="px-4 py-3 rounded-lg text-center"
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
              }}
            >
              <div
                className="text-[11px] mb-1 tracking-wide"
                style={{ color: "var(--text-3)" }}
              >
                {item.label}
              </div>
              <div
                className="text-sm font-semibold"
                style={{
                  color:
                    item.label === "格局" || item.label === "用神"
                      ? "var(--cinnabar)"
                      : "var(--ink)",
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
