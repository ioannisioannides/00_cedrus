import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { NewFindingForm } from "@/components/new-finding-form"
import { format } from "date-fns"

interface Props {
  params: Promise<{ id: string }>
}

export const metadata = { title: "New Finding — Cedrus" }

export default async function NewFindingPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["LEAD_AUDITOR", "CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id: auditId } = await params

  const audit = await prisma.audit.findUnique({
    where: { id: auditId },
    include: {
      clientOrg: { select: { name: true } },
      sites: { include: { site: true } },
      certifications: { include: { certification: { include: { standard: true } } } },
    },
  })

  if (!audit) redirect("/lead-auditor/audits")

  if (!["IN_PROGRESS", "REPORT_DRAFT"].includes(audit.status)) {
    redirect(`/lead-auditor/audits/${auditId}`)
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Finding</h1>
        <p className="text-muted-foreground">
          {audit.clientOrg.name} · {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
        </p>
      </div>

      <NewFindingForm
        auditId={auditId}
        sites={audit.sites.map((s) => ({ id: s.site.id, name: s.site.siteName }))}
        standards={audit.certifications.map((ac) => ({
          id: ac.certification.standard.id,
          code: ac.certification.standard.code,
          title: ac.certification.standard.title,
        }))}
      />
    </div>
  )
}
