// Minimal health check endpoint for Docker/infra probes
import { NextResponse } from "next/server"

export async function GET() {
  // Optionally, add DB check here in the future
  return NextResponse.json({ status: "ok" })
}
