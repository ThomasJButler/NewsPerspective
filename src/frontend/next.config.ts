import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

const repoRoot = fileURLToPath(new URL("../..", import.meta.url));
const backendOrigin = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  turbopack: {
    root: repoRoot,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
