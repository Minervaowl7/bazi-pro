export default function Loading() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: "var(--border)", borderTopColor: "transparent" }} />
        <span className="text-sm" style={{ color: "var(--text-3)" }}>加载中...</span>
      </div>
    </div>
  );
}
