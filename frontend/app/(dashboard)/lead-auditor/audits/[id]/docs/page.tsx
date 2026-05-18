import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  AuditChangesForm,
  AuditPlanReviewForm,
  AuditSummaryForm,
  AddRecommendationForm,
} from "@/components/audit-docs-forms"
import {
  saveAuditChanges,
  saveAuditPlanReview,
  saveAuditSummary,
  addRecommendation,
  deleteRecommendation,
} from "@/lib/actions/audit-docs"
import { Trash2 } from "lucide-react"

interface Props { params: Promise<{ id: string }> }

export default async function AuditDocsPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }

  const { id: auditId } = await params

  const audit = await prisma.audit.findUnique({
    where: { id: auditId },
    include: {
      clientOrg: { select: { name: true } },
      changes: true,
      planReview: true,
      summary: true,
      recommendations: { orderBy: { createdAt: "asc" } },
    },
  })

  if (!audit) redirect("/lead-auditor/audits")

  const isEditable = ["IN_PROGRESS", "REPORT_DRAFT"].includes(audit.status)

  const changesAction = saveAuditChanges.bind(null, auditId)
  const planReviewAction = saveAuditPlanReview.bind(null, auditId)
  const summaryAction = saveAuditSummary.bind(null, auditId)
  const addRecAction = addRecommendation.bind(null, auditId)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Audit Documentation</h1>
          <p className="text-muted-foreground mt-1">
            {audit.clientOrg.name} · {audit.auditType.replace(/_/g, " ")} ·{" "}
            <span className="capitalize">{audit.status.replace(/_/g, " ")}</span>
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

      {!isEditable && (
        <div className="rounded border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          This audit is not in an editable state — documentation is read-only.
        </div>
      )}

      {/* Audit Changes */}
      <Card>
        <CardHeader>
          <CardTitle>Changes Since Last Audit</CardTitle>
          <CardDescription>
            Record any changes to the organisation since the previous audit.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isEditable ? (
            <AuditChangesForm
              auditId={auditId}
              data={audit.changes}
              action={changesAction}
            />
          ) : (
            <p className="text-sm text-muted-foreground">No changes recorded.</p>
          )}
        </CardContent>
      </Card>

      {/* Plan Review */}
      <Card>
        <CardHeader>
          <CardTitle>Audit Plan Review</CardTitle>
          <CardDescription>
            Review deviations from the audit plan and record next audit dates.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isEditable ? (
            <AuditPlanReviewForm data={audit.planReview} action={planReviewAction} />
          ) : (
            <p className="text-sm text-muted-foreground">No plan review recorded.</p>
          )}
        </CardContent>
      </Card>

      {/* Audit Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Audit Summary</CardTitle>
          <CardDescription>
            Evaluate key audit summary criteria and provide overall commentary.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isEditable ? (
            <AuditSummaryForm data={audit.summary} action={summaryAction} />
          ) : (
            <p className="text-sm text-muted-foreground">No summary recorded.</p>
          )}
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
          <CardDescription>
            Add recommendations arising from this audit.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {audit.recommendations.length > 0 ? (
            <ul className="space-y-2">
              {audit.recommendations.map((r) => (
                <li
                  key={r.id}
                  className="flex items-start justify-between gap-2 rounded border p-3 text-sm"
                >
                  <span>{r.recommendation}</span>
                  {isEditable && (
                    <form
                      action={async () => {
                        "use server"
                        await deleteRecommendation(r.id)
                      }}
                    >
                      <button
                        type="submit"
                        className="text-destructive hover:text-destructive/80 flex-shrink-0"
                        aria-label="Delete recommendation"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </form>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No recommendations added yet.</p>
          )}
          {isEditable && <AddRecommendationForm action={addRecAction} />}
        </CardContent>
      </Card>
    </div>
  )
}
