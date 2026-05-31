import { NextRequest } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";

export const maxDuration = 300;

export async function POST(request: NextRequest) {
  const body = await request.json();
  const backendUrl = `${BACKEND_URL}/api/v2/report`;

  try {
    const upstream = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(290_000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      return new Response(JSON.stringify(data), {
        status: upstream.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "代理请求失败";
    return new Response(
      JSON.stringify({ error: { code: "PROXY_ERROR", message: msg } }),
      {
        status: 504,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
