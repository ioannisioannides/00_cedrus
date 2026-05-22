import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card"
import { NCResponseForm } from "@/components/nc-response-form"
import { submitNCResponse } from "@/lib/actions/nc-responses"
import { AuditProgressionMap } from "@/components/audit-progression-map"
import { FindingCommentsSection } from "@/components/finding-comments-section"
import { ChevronLeft, FileText } from "lucide-react"
import { format } from "date-fns"

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

const NC_STATUS_LABEL: Record<string, string> = {
  OPEN: "Open",
  CLIENT_RESPONDED: "Response Submitted",
  ACCEPTED: "Accepted",
  CLOSED: "Closed",
}

export default async function ClientAuditDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await auth()
  if (!session?.user || session.user.role !== "CLIENT_ADMIN") redirect("/")

  const clientOrgId = session.user.clientOrgId
  if (!clientOrgId) redirect("/client-admin")

  const { id } = await params

  const audit = await prisma.audit.findUnique({
    where: { id, clientOrgId },
    include: {
      clientOrg: { select: { name: true } },
      leadAuditor: { select: { name: true } },
      findings: {
        orderBy: [{ findingType: "asc" }, { createdAt: "asc" }],
        include: {
          standard: { select: { code: true } },
          comments: {
            include: {
              user: { select: { name: true, role: true } },
            },
            orderBy: { createdAt: "asc" },
          },
        },
      },
    },
  })

  if (!audit) notFound()

  const canRespond = ["IN_PROGRESS", "REPORT_DRAFT", "CLIENT_REVIEW", "SUBMITTED"].includes(
    audit.status
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <Button render={<Link href="/client-admin/audits" />} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Audits
        </Button>

        <Button
          render={<Link href={`/client-admin/audits/${audit.id}/report`} />}
          variant="outline"
          size="sm"
          className="flex items-center gap-1.5"
        >
          <FileText className="h-4 w-4" />
          Print / Download Formal Report
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">{audit.clientOrg.name}</h1>
        <p className="text-muted-foreground">
          {audit.auditType.replace(/_/g, " ")} ·{" "}
          {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
        </p>
      </div>

      {/* Audit Process Progression Map */}
      <AuditProgressionMap currentStatus={audit.status} />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>
            <Badge className="font-sans uppercase text-xs tracking-wider">
              {audit.status.replace(/_/g, " ")}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Lead Auditor</CardDescription>
          </CardHeader>
          <CardContent className="text-sm font-medium">
            {audit.leadAuditor?.name ?? "Not assigned"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Open Non-Conformances</CardDescription>
          </CardHeader>
          <CardContent className="text-sm font-medium">
            {audit.findings.filter((f) => (f.findingType === "NC_MAJOR" || f.findingType === "NC_MINOR") && f.verificationStatus === "OPEN").length}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Audit Findings & Observations</h2>

        {audit.findings.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No findings recorded for this audit yet.
            </CardContent>
          </Card>
        ) : (
          audit.findings.map((f) => {
            const isNC = f.findingType === "NC_MAJOR" || f.findingType === "NC_MINOR"
            const needsResponse = isNC && f.verificationStatus === "OPEN" && canRespond
            const boundAction = submitNCResponse.bind(null, f.id)

            return (
              <Card key={f.id} className="overflow-hidden">
                <CardHeader className="bg-muted/10 border-b py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={FINDING_BADGE[f.findingType] ?? "outline"}>
                        {f.findingType.replace(/_/g, " ")}
                      </Badge>
                      {isNC && (
                        <Badge variant="outline">
                          {NC_STATUS_LABEL[f.verificationStatus] ?? f.verificationStatus}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {f.standard && (
                        <span className="font-semibold">{f.standard.code}</span>
                      )}
                      {f.clause && (
                        <span>Clause {f.clause}</span>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 pt-4">
                  {f.statementOfNc && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                        Statement of Finding
                      </p>
                      <p className="text-sm">{f.statementOfNc}</p>
                    </div>
                  )}

                  {f.objectiveEvidence && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                        Objective Evidence
                      </p>
                      <p className="text-sm">{f.objectiveEvidence}</p>
                    </div>
                  )}

                  {f.dueDate && (
                    <p className="text-xs text-muted-foreground">
                      Response due: <span className="font-medium">{format(f.dueDate, "dd MMM yyyy")}</span>
                    </p>
                  )}

                  {isNC && f.verificationStatus !== "OPEN" && f.clientCorrectiveAction && (
                    <div className="rounded-md bg-muted/60 p-3 space-y-2 border">
                      <p className="text-xs font-bold text-primary uppercase tracking-wide">
                        Corrective Action Response
                      </p>
                      {f.clientRootCause && (
                        <div>
                          <p className="text-xs text-muted-foreground font-semibold">Root cause analysis</p>
                          <p className="text-sm">{f.clientRootCause}</p>
                        </div>
                      )}
                      {f.clientCorrection && (
                        <div>
                          <p className="text-xs text-muted-foreground font-semibold">Immediate correction</p>
                          <p className="text-sm">{f.clientCorrection}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs text-muted-foreground font-semibold">Preventive action plan</p>
                        <p className="text-sm">{f.clientCorrectiveAction}</p>
                      </div>
                    </div>
                  )}

                  {needsResponse && (
                    <div className="border-t pt-4">
                      <p className="text-sm font-medium mb-3">Submit your corrective action plan</p>
                      <NCResponseForm
                        action={boundAction}
                        defaultValues={{
                          clientRootCause: f.clientRootCause || undefined,
                          clientCorrection: f.clientCorrection || undefined,
                          clientCorrectiveAction: f.clientCorrectiveAction || undefined,
                        }}
                      />
                    </div>
                  )}

                  {/* Finding Comment Discussion section */}
                  <FindingCommentsSection findingId={f.id} comments={f.comments} />
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
