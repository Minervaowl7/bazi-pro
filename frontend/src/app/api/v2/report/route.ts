import { NextRequest } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const backendUrl = `${BACKEND_URL}/api/v2/report`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 280_000);

  try {
    const upstream = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    const text = await upstream.text();
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }

    return new Response(JSON.stringify(data), {
      status: upstream.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
      },
    });
  } catch (e) {
    clearTimeout(timeout);
    const msg = e instanceof Error ? e.message : "代理请求失败";
    const isTimeout = msg.includes("abort") || msg.includes("timeout") || msg.includes("Timeout");
    return new Response(
      JSON.stringify({
        error: {
          code: isTimeout ? "TIMEOUT" : "PROXY_ERROR",
          message: isTimeout ? "报告生成超时，请稍后重试" : msg,
        },
      }),
      {
        status: isTimeout ? 504 : 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
