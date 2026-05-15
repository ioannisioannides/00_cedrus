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
import { DecisionForm } from "@/components/decision-form"
import { makeCertificationDecision } from "@/lib/actions/decisions"

interface Props { params: Promise<{ id: string }> }

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

export default async function DecisionDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || session.user.role !== "DECISION_MAKER") redirect("/")

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
      certifications: {
        include: { certification: { include: { standard: true } } },
      },
      technicalReview: {
        include: { reviewer: { select: { name: true } } },
      },
      certificationDecision: {
        include: { decisionMaker: { select: { name: true } } },
      },
      statusLogs: {
        orderBy: { changedAt: "desc" },
        take: 8,
        include: { changedBy: { select: { name: true } } },
      },
    },
  })

  if (!audit) redirect("/decision-maker/decisions")

  const isPending = audit.status === "DECISION_PENDING"
  const action = makeCertificationDecision.bind(null, id)

  const DECISION_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    GRANT: "default",
    REFUSE: "destructive",
    SUSPEND: "secondary",
    WITHDRAW: "destructive",
    SPECIAL_AUDIT: "secondary",
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">
              {audit.auditType.replace("_", " ")} — {audit.clientOrg.name}
            </h1>
            <Badge variant={audit.status === "DECISION_PENDING" ? "default" : "outline"}>
              {audit.status.replace("_", " ")}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
            {" · "}Lead: {audit.leadAuditor?.name ?? "Unassigned"}
          </p>
        </div>
        <Button render={<Link href="/decision-maker/decisions" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Standards */}
          {audit.certifications.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Standards</CardTitle></CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {audit.certifications.map((ac) => (
                  <Badge key={ac.certificationId} variant="outline">
                    {ac.certification.standard.code} — {ac.certification.certificationScope}
                  </Badge>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Technical review */}
          {audit.technicalReview && (
            <Card>
              <CardHeader>
                <CardTitle>Technical Review</CardTitle>
                <CardDescription>By {audit.technicalReview.reviewer.name}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Badge variant={audit.technicalReview.status === "APPROVED" ? "default" : "secondary"}>
                    {audit.technicalReview.status.replace("_", " ")}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {[
                    { label: "Scope verified", val: audit.technicalReview.scopeVerified },
                    { label: "Objectives verified", val: audit.technicalReview.objectivesVerified },
                    { label: "Findings reviewed", val: audit.technicalReview.findingsReviewed },
                    { label: "Conclusion clear", val: audit.technicalReview.conclusionClear },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-1.5">
                      <span className={item.val ? "text-green-600" : "text-destructive"}>
                        {item.val ? "✓" : "✗"}
                      </span>
                      <span className="text-muted-foreground">{item.label}</span>
                    </div>
                  ))}
                </div>
                {audit.technicalReview.reviewerNotes && (
                  <p className="text-sm text-muted-foreground border-t pt-3">
                    {audit.technicalReview.reviewerNotes}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Findings */}
          <Card>
            <CardHeader>
              <CardTitle>Findings</CardTitle>
              <CardDescription>{audit.findings.length} total</CardDescription>
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
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {audit.findings.map((f) => (
                      <TableRow key={f.id}>
                        <TableCell>
                          <Badge variant={FINDING_BADGE[f.findingType] ?? "outline"}>
                            {f.findingType.replace("_", " ")}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs">{f.clause}</TableCell>
                        <TableCell className="text-sm max-w-xs truncate">
                          {f.statementOfNc || f.observationStatement || f.ofiDescription || "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Decision panel */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Certification Decision</CardTitle>
              <CardDescription>
                {isPending
                  ? "Record your certification decision for this audit."
                  : "A decision has already been recorded."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {audit.certificationDecision ? (
                <div className="space-y-3 text-sm">
                  <Badge variant={DECISION_COLOR[audit.certificationDecision.decision] ?? "outline"}>
                    {audit.certificationDecision.decision.replace("_", " ")}
                  </Badge>
                  <p className="text-muted-foreground">{audit.certificationDecision.decisionNotes}</p>
                  <p className="text-xs text-muted-foreground">
                    By {audit.certificationDecision.decisionMaker.name} on{" "}
                    {format(audit.certificationDecision.decidedAt, "dd MMM yyyy")}
                  </p>
                </div>
              ) : isPending ? (
                <DecisionForm action={action} clientName={audit.clientOrg.name} />
              ) : (
                <p className="text-sm text-muted-foreground">
                  This audit is not currently awaiting a certification decision.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Status log */}
          <Card className="mt-4">
            <CardHeader><CardTitle className="text-sm">Status History</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {audit.statusLogs.map((log) => (
                <div key={log.id} className="text-xs">
                  <span className="text-muted-foreground">{log.fromStatus ?? "—"}</span>
                  {" → "}
                  <span className="font-medium">{log.toStatus}</span>
                  <div className="text-muted-foreground">
                    {log.changedBy.name} · {format(log.changedAt, "dd MMM")}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
