import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-6">
      <div className="text-center">
        <div className="text-6xl font-bold mb-4" style={{ color: "var(--color-border)" }}>404</div>
        <h1 className="text-xl font-bold mb-2" style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-serif)" }}>
          页面未找到
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--color-text-muted)" }}>
          你访问的页面不存在或已被移除
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-all active:scale-[0.97]"
          style={{ background: "var(--color-scholar-blue)" }}
        >
          返回首页
        </Link>
      </div>
    </div>
  );
}
