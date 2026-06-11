import type { Metadata } from "next";
import CompareClient from "./CompareClient";

export const metadata: Metadata = {
  title: "八字合婚 | 八字排盘 · 确定性命理引擎",
  description:
    "基于五行生克、日主关系、用神互补的确定性兼容度分析。输入双方八字，即刻获得合婚分析结果。",
  openGraph: {
    title: "八字合婚 | 确定性命理引擎",
    description: "基于五行生克、日主关系、用神互补的确定性兼容度分析。",
  },
  twitter: {
    title: "八字合婚 | 确定性命理引擎",
    description: "基于五行生克、日主关系、用神互补的确定性兼容度分析。",
    card: "summary",
  },
};

export default function ComparePage() {
  return <CompareClient />;
}
