import type { NextConfig } from "next"

const isDev = process.env.NODE_ENV !== "production"

// In development, Turbopack injects inline scripts so 'unsafe-inline' is required.
// In production, Next.js emits no inline scripts, so we can be strict.
const csp = [
  "default-src 'self'",
  isDev
    ? "script-src 'self' 'unsafe-eval' 'unsafe-inline'"
    : "script-src 'self' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'", // Tailwind injects inline styles
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self'",
  "frame-src 'none'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "upgrade-insecure-requests",
].join("; ")

const securityHeaders = [
  // Prevents clickjacking
  { key: "X-Frame-Options", value: "DENY" },
  // Prevents MIME-type sniffing
  { key: "X-Content-Type-Options", value: "nosniff" },
  // Controls referrer information
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // Restricts browser feature access
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
  },
  // HSTS — max 2 years, include subdomains, preload-ready
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  // Content Security Policy
  { key: "Content-Security-Policy", value: csp },
  // Cross-Origin policies (COEP relaxed in dev — Turbopack HMR uses cross-origin WS)
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ...(isDev
    ? []
    : [
        { key: "Cross-Origin-Embedder-Policy", value: "require-corp" },
        { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
      ]),
]

const nextConfig: NextConfig = {
  // Prevent Turbopack from bundling Prisma and its driver adapters — they must
  // run as native Node.js modules. Without this, Turbopack resolves the wrong
  // package exports (e.g. edge/browser builds) and model delegates are undefined.
  serverExternalPackages: ["@prisma/client", "@prisma/adapter-pg", "pg"],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ]
  },
  // Enforce strict mode for React
  reactStrictMode: true,
  // Disallow unknown props leaking to the DOM
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
}

export default nextConfig
