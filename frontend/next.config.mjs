/** @type {import('next').NextConfig} */
const backend = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default {
  // Allow Arena preview host and any dev origin
  experimental: { serverActions: { allowedOrigins: ["*"] } },
  async rewrites() {
    return [
      { source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` },
      { source: "/health", destination: `${backend}/health` },
    ];
  },
};
