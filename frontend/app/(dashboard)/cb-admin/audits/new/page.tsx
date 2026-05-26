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

  const isSuperAdmin = session.user.role === "SUPER_ADMIN"
  const cbOrgId = session.user.organizationId
  if (!isSuperAdmin && !cbOrgId) redirect("/")

  const { clientOrgId } = await searchParams

  const auditScope = {
    OR: [
      { createdBy: { is: { cbOrgId } } },
      { leadAuditor: { is: { cbOrgId } } },
    ],
  }

  const clientScope = isSuperAdmin
    ? {}
    : {
        OR: [
          { audits: { some: auditScope } },
          { auditPrograms: { some: { createdBy: { is: { cbOrgId } } } } },
          { complaints: { some: { submittedBy: { is: { cbOrgId } } } } },
          { complaints: { some: { relatedAudit: { is: auditScope } } } },
        ],
      }

  const [clientOrgs, auditors, programs] = await Promise.all([
    prisma.clientOrg.findMany({
      where: clientScope,
      orderBy: { name: "asc" },
      select: { id: true, name: true, customerId: true },
    }),
    prisma.user.findMany({
      where: {
        ...(isSuperAdmin ? {} : { cbOrgId }),
        role: "LEAD_AUDITOR",
        isActive: true,
      },
      orderBy: { name: "asc" },
      select: { id: true, name: true },
    }),
    prisma.auditProgram.findMany({
      where: {
        ...(isSuperAdmin ? {} : { createdBy: { is: { cbOrgId } } }),
        status: "ACTIVE",
      },
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
