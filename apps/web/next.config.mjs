/** @type {import('next').NextConfig} */
const apiBaseUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/api/:path*`
      }
    ];
  }
};

export default nextConfig;
