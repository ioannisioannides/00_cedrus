import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { NCVerifyForm } from "@/components/nc-verify-form"
import { verifyFindingAction } from "@/lib/actions/findings"
import { format } from "date-fns"

interface Props { params: Promise<{ id: string; findingId: string }> }

export default async function NCVerifyPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }

  const { id: auditId, findingId } = await params

  const finding = await prisma.finding.findUnique({
    where: { id: findingId },
    include: { audit: { select: { status: true, clientOrg: { select: { name: true } } } } },
  })

  if (
    !finding ||
    finding.auditId !== auditId ||
    (finding.findingType !== "NC_MAJOR" && finding.findingType !== "NC_MINOR")
  ) {
    redirect(`/lead-auditor/audits/${auditId}`)
  }

  if (finding.verificationStatus !== "CLIENT_RESPONDED") {
    redirect(`/lead-auditor/audits/${auditId}`)
  }

  const action = verifyFindingAction.bind(null, findingId)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Verify NC Response</h1>
          <p className="text-muted-foreground mt-1">
            {finding.audit.clientOrg.name} · Clause {finding.clause}
          </p>
        </div>
        <Button
          render={<Link href={`/lead-auditor/audits/${auditId}`} />}
          variant="outline"
          size="sm"
        >
          ← Back
        </Button>
      </div>

      {/* NC details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {finding.findingType === "NC_MAJOR" ? "Major" : "Minor"} Nonconformity
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <div className="font-medium text-muted-foreground">Statement of NC</div>
            <p>{finding.statementOfNc}</p>
          </div>
          {finding.objectiveEvidence && (
            <div>
              <div className="font-medium text-muted-foreground">Objective Evidence</div>
              <p>{finding.objectiveEvidence}</p>
            </div>
          )}
          {finding.dueDate && (
            <div>
              <div className="font-medium text-muted-foreground">Due Date</div>
              <p>{format(finding.dueDate, "dd MMM yyyy")}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Client response */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Client Response</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <div className="font-medium text-muted-foreground">Root Cause Analysis</div>
            <p>{finding.clientRootCause || <span className="italic text-muted-foreground">Not provided</span>}</p>
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Correction</div>
            <p>{finding.clientCorrection || <span className="italic text-muted-foreground">Not provided</span>}</p>
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Corrective Action</div>
            <p>{finding.clientCorrectiveAction || <span className="italic text-muted-foreground">Not provided</span>}</p>
          </div>
        </CardContent>
      </Card>

      {/* Verify form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Verification Decision</CardTitle>
        </CardHeader>
        <CardContent>
          <NCVerifyForm action={action} auditId={auditId} />
        </CardContent>
      </Card>
    </div>
  )
}
