import path from "node:path";
import type { NextConfig } from "next";

const apiUrl = (
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Required when the app lives in a monorepo subdirectory on Vercel.
  outputFileTracingRoot: path.join(__dirname, ".."),
  async rewrites() {
    return [
      { source: "/health", destination: `${apiUrl}/health` },
      { source: "/api/:path*", destination: `${apiUrl}/api/:path*` },
    ];
  },
};

export default nextConfig;
