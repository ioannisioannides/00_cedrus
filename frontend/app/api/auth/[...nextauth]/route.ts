import { handlers } from "@/lib/auth"
import { Ratelimit } from "@upstash/ratelimit"
import { Redis } from "@upstash/redis"
import { NextRequest, NextResponse } from "next/server"

// Rate limiter — 5 login attempts per 15 minutes per IP.
// Requires UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN in .env for production.
// Falls through (no-op) when Redis is not configured (local dev without Upstash).
let ratelimit: Ratelimit | null = null
if (
  process.env.UPSTASH_REDIS_REST_URL &&
  process.env.UPSTASH_REDIS_REST_TOKEN
) {
  ratelimit = new Ratelimit({
    redis: Redis.fromEnv(),
    limiter: Ratelimit.slidingWindow(5, "15 m"),
    prefix: "cedrus:auth:ratelimit",
    analytics: false,
  })
}

function getClientIp(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    req.headers.get("x-real-ip") ??
    "unknown"
  )
}

// Only rate-limit the credentials sign-in POST (not GET/session/csrf)
async function POST(req: NextRequest) {
  if (ratelimit) {
    const ip = getClientIp(req)
    const { success, limit, remaining, reset } = await ratelimit.limit(ip)

    if (!success) {
      return NextResponse.json(
        { error: "Too many login attempts. Please wait before trying again." },
        {
          status: 429,
          headers: {
            "X-RateLimit-Limit": String(limit),
            "X-RateLimit-Remaining": String(remaining),
            "X-RateLimit-Reset": String(reset),
            "Retry-After": String(Math.ceil((reset - Date.now()) / 1000)),
          },
        },
      )
    }
  }

  return handlers.POST(req)
}

export { POST }
export const GET = handlers.GET
