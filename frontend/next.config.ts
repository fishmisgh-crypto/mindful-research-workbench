import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Snapshot files are read at request time on hosted builds (MINDFUL_SNAPSHOT=1).
  outputFileTracingIncludes: { "/**": ["./snapshot/**"] },
};

export default nextConfig;
