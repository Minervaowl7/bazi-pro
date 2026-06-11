"use client";

import { useEffect, useState } from "react";

/**
 * SSR 安全的网络连接状态检测。
 * 服务端始终返回 true（假设在线），客户端挂载后更新真实值。
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return isOnline;
}
