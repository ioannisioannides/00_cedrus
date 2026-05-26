import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { AuditForm } from "@/components/audit-form"
import { updateAudit } from "@/lib/actions/audits"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ChevronLeft } from "lucide-react"

export default async function EditAuditPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const isSuperAdmin = session.user.role === "SUPER_ADMIN"
  const cbOrgId = session.user.organizationId
  if (!isSuperAdmin && !cbOrgId) redirect("/")

  const { id } = await params

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

  const [audit, clientOrgs, auditors, programs] = await Promise.all([
    prisma.audit.findFirst({
      where: isSuperAdmin ? { id } : { id, ...auditScope },
      select: {
        id: true,
        status: true,
        clientOrgId: true,
        auditType: true,
        dateFrom: true,
        dateTo: true,
        leadAuditorId: true,
        programId: true,
        plannedDurationHours: true,
        durationJustification: true,
      },
    }),
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
      where: isSuperAdmin ? {} : { createdBy: { is: { cbOrgId } } },
      orderBy: [{ year: "desc" }, { title: "asc" }],
      select: { id: true, title: true, year: true, clientOrgId: true },
    }),
  ])

  if (!audit) notFound()

  // Only allow editing audits that are still in DRAFT or SCHEDULED
  if (!["DRAFT", "SCHEDULED"].includes(audit.status)) {
    redirect(`/cb-admin/audits/${id}`)
  }

  const boundAction = updateAudit.bind(null, id)

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-2">
        <Button render={<Link href={`/cb-admin/audits/${id}`} />} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Audit
        </Button>
      </div>
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Edit Audit</h1>
        <p className="text-muted-foreground">Update audit details. Status must be Draft or Scheduled.</p>
      </div>
      <AuditForm
        action={boundAction}
        clientOrgs={clientOrgs}
        auditors={auditors}
        programs={programs}
        defaultClientOrgId={audit.clientOrgId}
        defaultValues={{
          auditType: audit.auditType,
          dateFrom: audit.dateFrom.toISOString().split("T")[0],
          dateTo: audit.dateTo.toISOString().split("T")[0],
          leadAuditorId: audit.leadAuditorId ?? "",
          programId: audit.programId ?? "",
          plannedDurationHours: audit.plannedDurationHours?.toString() ?? "",
          durationJustification: audit.durationJustification,
        }}
      />
    </div>
  )
}
