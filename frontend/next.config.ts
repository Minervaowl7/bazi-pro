import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: { unoptimized: true },
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8711";
    return [
      {
        source: "/api/v2/:path*",
        destination: `${apiBase}/api/v2/:path*`,
      },
    ];
  },
};

export default nextConfig;
