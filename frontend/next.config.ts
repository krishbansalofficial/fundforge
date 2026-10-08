import type { NextConfig } from "next";

const api = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Same-origin proxy: the browser never needs CORS or the API host.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
