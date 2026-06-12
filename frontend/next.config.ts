import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Required when the app lives in a monorepo subdirectory on Vercel.
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
