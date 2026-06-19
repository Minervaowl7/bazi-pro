import type { Metadata } from "next";
import ReportClient from "./ReportClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const fallback: Metadata = {
    title: "详批报告 | 八字排盘 · 确定性命理引擎",
    description: "八字详批报告，包含格局分析、用神推导、大运流年等完整命理解读。",
  };

  try {
    const res = await fetch(`${API_BASE}/api/v2/analysis/${id}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return fallback;
    const data = await res.json();
    const r = data?.result as Record<string, unknown> | undefined;
    const dayMaster = (data?.day_master as string) || "";
    const birthJson = r?.birth_json as Record<string, unknown> | undefined;
    const name = (birthJson?.name as string) || "";

    const title = name
      ? `${name}的详批报告 | 八字排盘`
      : dayMaster
        ? `${dayMaster}日主详批报告 | 八字排盘`
        : fallback.title as string;

    return {
      title,
      description: `八字详批报告${name ? ` — ${name}` : ""}，包含格局分析、用神推导、大运流年等完整命理解读。`,
      openGraph: { title, type: "article" },
      twitter: { title, card: "summary" },
    };
  } catch {
    return fallback;
  }
}

export default function ReportPage() {
  return <ReportClient />;
}
