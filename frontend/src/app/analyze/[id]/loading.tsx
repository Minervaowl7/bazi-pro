export default function Loading() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center" role="status" aria-label="正在排盘加载中">
      <div className="flex flex-col items-center gap-6">
        {/* 五行环绕 */}
        <div className="relative w-16 h-16">
          {["木", "火", "土", "金", "水"].map((wx, i) => {
            const angle = i * 72 - 90;
            const rad = (angle * Math.PI) / 180;
            const x = 24 + 24 * Math.cos(rad);
            const y = 24 + 24 * Math.sin(rad);
            return (
              <span
                key={wx}
                className="absolute text-xs font-bold"
                style={{
                  left: x,
                  top: y,
                  color: "var(--text-4)",
                  opacity: 0.4,
                  animation: `pulse-soft 2s ease-in-out ${i * 0.3}s infinite`,
                }}
              >
                {wx}
              </span>
            );
          })}
          {/* 中心点 */}
          <span
            className="absolute inset-0 m-auto w-2.5 h-2.5 rounded-full"
            style={{
              background: "var(--wx-water)",
              animation: "pulse-soft 2s ease-in-out infinite",
            }}
          />
        </div>

        <div className="text-center">
          <p className="text-sm font-medium" style={{ color: "var(--text-2)" }}>
            正在排盘
          </p>
          <p className="text-[11px] mt-1" style={{ color: "var(--text-4)" }}>
            初始化命理引擎...
          </p>
        </div>
      </div>
    </div>
  );
}
