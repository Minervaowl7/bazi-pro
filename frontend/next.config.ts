import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: { unoptimized: true },
  allowedDevOrigins: [
    "127.0.0.1",
    "run-agent-6a1ab6ea393a9f7634f36332-mpt9no3g-preview.agent-sandbox-bj-d3-gw.trae.cn",
  ],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
