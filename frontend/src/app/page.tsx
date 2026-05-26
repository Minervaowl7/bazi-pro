"use client";

import BirthForm from "@/components/BirthForm";

export default function Home() {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-[var(--accent)] tracking-wider mb-2">
            bazi-pro
          </h1>
          <p className="text-[var(--text-muted)] text-sm">
            专业八字命理分析引擎 · 确定性计算 · 古籍引证
          </p>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-6">
          <h2 className="text-base font-medium mb-4 text-[var(--text-secondary)]">
            输入命盘信息
          </h2>
          <BirthForm />
        </div>

        <p className="text-center text-xs text-[var(--text-muted)] mt-6 max-w-sm mx-auto">
          本服务仅供传统文化学习与参考，分析结果不构成任何决策依据。
        </p>
      </div>
    </div>
  );
}
