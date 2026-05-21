import type { NextAuthConfig } from "next-auth"
import type { Role } from "@prisma/client"

export const authConfig = {
  pages: { signIn: "/login" },
  session: { strategy: "jwt" as const },
  providers: [],
  cookies: {
    sessionToken: {
      options: {
        httpOnly: true,
        sameSite: "lax" as const,
        path: "/",
        // In production, cookies are always Secure (HTTPS-only)
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.id = user.id
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        token.role = (user as any).role as Role
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        token.organizationId = (user as any).organizationId as string | null
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        token.clientOrgId = (user as any).clientOrgId as string | null
      }
      return token
    },
    session({ session, token }) {
      session.user.id = token.id as string
      session.user.role = token.role as Role
      session.user.organizationId = token.organizationId as string | null
      session.user.clientOrgId = token.clientOrgId as string | null
      return session
    },
  },
} satisfies NextAuthConfig
