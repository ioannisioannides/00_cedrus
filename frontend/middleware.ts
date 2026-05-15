import NextAuth from "next-auth"
import { authConfig } from "./auth.config"
import { NextResponse } from "next/server"

const ROLE_HOME: Record<string, string> = {
  SUPER_ADMIN: "/super-admin",
  CB_ADMIN: "/cb-admin",
  LEAD_AUDITOR: "/lead-auditor",
  TECHNICAL_REVIEWER: "/technical-reviewer",
  DECISION_MAKER: "/decision-maker",
  CLIENT_ADMIN: "/client-admin",
}

const { auth } = NextAuth(authConfig)

export default auth(function middleware(req) {
  const { nextUrl } = req
  const session = req.auth
  const isLoggedIn = !!session?.user

  if (nextUrl.pathname === "/login") {
    if (isLoggedIn) {
      const home = ROLE_HOME[session.user.role as string] ?? "/"
      return NextResponse.redirect(new URL(home, nextUrl))
    }
    return NextResponse.next()
  }

  if (!isLoggedIn) {
    return NextResponse.redirect(new URL("/login", nextUrl))
  }

  return NextResponse.next()
})

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
