import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: the profile's Dockerfile serves the build with nginx.
  output: "export",
};

export default nextConfig;
