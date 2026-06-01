// Enriched health check endpoint for Docker/infra probes verifying DB connection
import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function GET() {
  try {
    // Run a fast, lightweight connectivity query with a timeout race
    const dbPromise = prisma.$queryRaw`SELECT 1`
    
    // Hard cap DB query latency at 3 seconds for health checks to fail-fast
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Database response timeout")), 3000)
    )

    await Promise.race([dbPromise, timeoutPromise])

    return NextResponse.json({
      status: "healthy",
      database: "connected",
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error("Health check database probe failed:", error)
    return NextResponse.json(
      {
        status: "unhealthy",
        database: "error",
        error: error instanceof Error ? error.message : "Database connection failed",
        timestamp: new Date().toISOString()
      },
      { status: 503 }
    )
  }
}
