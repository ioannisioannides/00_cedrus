import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FindingEditForm } from "@/components/finding-edit-form"
import { updateFinding } from "@/lib/actions/findings"

interface Props { params: Promise<{ id: string; findingId: string }> }

export default async function FindingEditPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }

  const { id: auditId, findingId } = await params

  const finding = await prisma.finding.findUnique({
    where: { id: findingId },
    include: { audit: { select: { status: true, clientOrg: { select: { name: true } } } } },
  })

  if (!finding || finding.auditId !== auditId) redirect(`/lead-auditor/audits/${auditId}`)

  const isEditable = ["IN_PROGRESS", "REPORT_DRAFT"].includes(finding.audit.status)
  if (!isEditable) redirect(`/lead-auditor/audits/${auditId}`)

  const action = updateFinding.bind(null, findingId)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Edit Finding</h1>
          <p className="text-muted-foreground mt-1">
            {finding.audit.clientOrg.name} · {finding.findingType.replace(/_/g, " ")} · Clause {finding.clause}
          </p>
        </div>
        <Button
          render={<Link href={`/lead-auditor/audits/${auditId}`} />}
          variant="outline"
          size="sm"
        >
          ← Back to Audit
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {finding.findingType === "NC_MAJOR"
              ? "Major Nonconformity"
              : finding.findingType === "NC_MINOR"
              ? "Minor Nonconformity"
              : finding.findingType === "OBSERVATION"
              ? "Observation"
              : "Opportunity for Improvement"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FindingEditForm finding={finding} action={action} auditId={auditId} />
        </CardContent>
      </Card>
    </div>
  )
}
