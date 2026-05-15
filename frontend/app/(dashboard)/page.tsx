import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import type { Role } from "@prisma/client"

const ROLE_HOME: Record<Role, string> = {
  SUPER_ADMIN: "/super-admin",
  CB_ADMIN: "/cb-admin",
  LEAD_AUDITOR: "/lead-auditor",
  TECHNICAL_REVIEWER: "/technical-reviewer",
  DECISION_MAKER: "/decision-maker",
  CLIENT_ADMIN: "/client-admin",
}

export default async function RootPage() {
  const session = await auth()
  if (!session?.user) redirect("/login")
  redirect(ROLE_HOME[session.user.role])
}
