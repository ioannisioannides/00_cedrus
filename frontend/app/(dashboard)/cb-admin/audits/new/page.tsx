import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { AuditForm } from "@/components/audit-form"
import { createAudit } from "@/lib/actions/audits"

interface Props {
  searchParams: Promise<{ clientOrgId?: string }>
}

export default async function NewAuditPage({ searchParams }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { clientOrgId } = await searchParams

  const [clientOrgs, auditors, programs] = await Promise.all([
    prisma.clientOrg.findMany({ orderBy: { name: "asc" }, select: { id: true, name: true, customerId: true } }),
    prisma.user.findMany({
      where: { role: "LEAD_AUDITOR", isActive: true },
      orderBy: { name: "asc" },
      select: { id: true, name: true },
    }),
    prisma.auditProgram.findMany({
      where: { status: "ACTIVE" },
      orderBy: [{ year: "desc" }, { title: "asc" }],
      select: { id: true, title: true, year: true, clientOrgId: true },
    }),
  ])

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Audit</h1>
        <p className="text-muted-foreground">Schedule an audit for a client organisation.</p>
      </div>
      <AuditForm
        action={createAudit}
        clientOrgs={clientOrgs}
        auditors={auditors}
        programs={programs}
        defaultClientOrgId={clientOrgId}
      />
    </div>
  )
}
