import type { NextConfig } from "next";

// Turnover build: the civilian/public portal and legacy pages were removed. Every removed
// public URL goes to the sign-in screen (temporary redirect; /privacy stays as a static notice).
const REMOVED_PUBLIC_PATHS = [
  "/",
  "/register",
  "/verify-sent",
  "/verify",
  "/report",
  "/tracking",
  "/tracking/:path*",
  "/fire-stations",
  "/information",
  "/community",
  "/community/:path*",
  "/contributor",
  "/incidents",
  "/incidents/:path*",
  "/home",
];

const nextConfig: NextConfig = {
  output: "standalone",
  async redirects() {
    return REMOVED_PUBLIC_PATHS.map((source) => ({
      source,
      destination: "/login",
      permanent: false,
    }));
  },
  typescript: {
    // Type errors are enforced via `npx tsc --noEmit` (builds fail on errors).
    // tsconfig.json has no test file exclusions; all .ts/.tsx files are type-checked.
  },
};

export default nextConfig;
