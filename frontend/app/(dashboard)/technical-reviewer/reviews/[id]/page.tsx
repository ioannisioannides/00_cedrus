import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { TechnicalReviewForm } from "@/components/technical-review-form"
import { submitTechnicalReview } from "@/lib/actions/technical-reviews"

interface Props { params: Promise<{ id: string }> }

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

export default async function ReviewDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || session.user.role !== "TECHNICAL_REVIEWER") redirect("/")

  const { id } = await params
  const audit = await prisma.audit.findUnique({
    where: { id },
    include: {
      clientOrg: true,
      leadAuditor: { select: { name: true } },
      findings: {
        orderBy: [{ findingType: "asc" }, { createdAt: "desc" }],
        include: { createdBy: { select: { name: true } } },
      },
      statusLogs: {
        orderBy: { changedAt: "desc" },
        take: 5,
        include: { changedBy: { select: { name: true } } },
      },
      technicalReview: true,
      certifications: {
        include: { certification: { include: { standard: true } } },
      },
    },
  })

  if (!audit) redirect("/technical-reviewer/reviews")

  const reviewable = ["SUBMITTED", "TECHNICAL_REVIEW"].includes(audit.status)
  const action = submitTechnicalReview.bind(null, id)

  const ncMajor = audit.findings.filter((f) => f.findingType === "NC_MAJOR")
  const ncMinor = audit.findings.filter((f) => f.findingType === "NC_MINOR")
  const observations = audit.findings.filter((f) => f.findingType === "OBSERVATION")

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">
              {audit.auditType.replace("_", " ")} Audit — {audit.clientOrg.name}
            </h1>
            <Badge variant={audit.status === "TECHNICAL_REVIEW" ? "default" : "secondary"}>
              {audit.status.replace("_", " ")}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
            {" · "}Lead: {audit.leadAuditor?.name ?? "Unassigned"}
          </p>
        </div>
        <Button render={<Link href="/technical-reviewer/reviews" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Standards */}
          {audit.certifications.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Standards Under Review</CardTitle></CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {audit.certifications.map((ac) => (
                  <Badge key={ac.certificationId} variant="outline">
                    {ac.certification.standard.code}
                  </Badge>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Findings summary */}
          <Card>
            <CardHeader>
              <CardTitle>Findings Summary</CardTitle>
              <CardDescription>
                {ncMajor.length} major NC · {ncMinor.length} minor NC · {observations.length} observations
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {audit.findings.length === 0 ? (
                <p className="px-6 py-8 text-sm text-muted-foreground text-center">No findings recorded.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Clause</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Raised by</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {audit.findings.map((f) => (
                      <TableRow key={f.id}>
                        <TableCell>
                          <Badge variant={FINDING_BADGE[f.findingType] ?? "outline"} className="whitespace-nowrap">
                            {f.findingType.replace("_", " ")}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs">{f.clause}</TableCell>
                        <TableCell className="text-sm max-w-xs">
                          {f.statementOfNc || f.observationStatement || f.ofiDescription || "—"}
                        </TableCell>
                        <TableCell className="text-sm">{f.createdBy.name}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Status log */}
          <Card>
            <CardHeader><CardTitle>Status History</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {audit.statusLogs.map((log) => (
                <div key={log.id} className="flex items-start justify-between text-sm">
                  <div>
                    <span className="text-muted-foreground">{log.fromStatus ?? "—"}</span>
                    {" → "}
                    <span className="font-medium">{log.toStatus}</span>
                    {log.notes && <p className="text-xs text-muted-foreground mt-0.5">{log.notes}</p>}
                  </div>
                  <div className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                    {log.changedBy.name} · {format(log.changedAt, "dd MMM")}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Review form */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Technical Review</CardTitle>
              <CardDescription>
                {reviewable
                  ? "Complete the checklist and submit your review decision."
                  : "This audit is no longer in the review stage."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reviewable ? (
                <TechnicalReviewForm action={action} existing={audit.technicalReview} />
              ) : (
                audit.technicalReview && (
                  <div className="space-y-2 text-sm">
                    <Badge variant={audit.technicalReview.status === "APPROVED" ? "default" : "secondary"}>
                      {audit.technicalReview.status.replace("_", " ")}
                    </Badge>
                    <p className="text-muted-foreground">{audit.technicalReview.reviewerNotes}</p>
                  </div>
                )
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
