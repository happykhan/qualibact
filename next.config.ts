import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    // GitHub Pages cannot run the Next.js image optimizer, so use static images.
    unoptimized: true,
  },
};

export default nextConfig;
