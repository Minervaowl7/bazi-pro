import type { Metadata } from "next";
import AnalyzeClient from "./AnalyzeClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const fallback: Metadata = {
    title: "八字分析 | 八字排盘 · 确定性命理引擎",
    description: "2964 条古籍条文驱动的八字排盘引擎，三大流派并行分析。",
  };

  try {
    const res = await fetch(`${API_BASE}/api/v2/analysis/${id}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return fallback;
    const data = await res.json();
    const r = data?.result as Record<string, unknown> | undefined;
    const dayMaster = (data?.day_master as string) || "";
    const patternName =
      (r?.pattern as Record<string, unknown>)?.pattern as string || "";
    const yongshen =
      (r?.yongshen as Record<string, unknown>)?.yongshen as string || "";

    const parts: string[] = [];
    if (dayMaster) parts.push(`${dayMaster}日主`);
    if (patternName) parts.push(patternName);
    if (yongshen) parts.push(`用神${yongshen}`);

    const title =
      parts.length > 0
        ? `${parts.join(" · ")} | 八字分析`
        : fallback.title as string;

    return {
      title,
      description: `八字排盘分析：${parts.join("、") || "详细命理解析"}。基于古籍条文的确定性计算引擎，三大流派并行分析。`,
      openGraph: { title, type: "article" },
      twitter: { title, card: "summary" },
    };
  } catch {
    return fallback;
  }
}

export default function AnalyzePage() {
  return <AnalyzeClient />;
}
