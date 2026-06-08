"use client";

import { useEffect, useState } from "react";

/**
 * SSR 安全的 prefers-reduced-motion 检测。
 * 服务端始终返回 false（允许动画），客户端挂载后更新真实值。
 */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    // 首次同步（useEffect 在 paint 后运行，不会阻塞）
    const handler = () => setReduced(mql.matches);
    handler();
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return reduced;
}
