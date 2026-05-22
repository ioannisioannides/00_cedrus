import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ChevronLeft, Printer } from "lucide-react"
import { format } from "date-fns"

export default async function AuditPrintReportPage({
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
      clientOrg: true,
      leadAuditor: { select: { name: true, email: true } },
      summary: true,
      recommendations: true,
      findings: {
        include: {
          standard: { select: { code: true, title: true } },
          createdBy: { select: { name: true } },
          comments: {
            include: {
              user: { select: { name: true, role: true } },
            },
            orderBy: { createdAt: "asc" },
          },
        },
        orderBy: [{ findingType: "asc" }, { clause: "asc" }],
      },
    },
  })

  if (!audit) notFound()

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4 sm:p-8 bg-card rounded-xl border print:border-none print:shadow-none print:p-0 print:bg-transparent">
      {/* Action panel hidden when page is printed */}
      <div className="flex items-center justify-between gap-4 print:hidden border-b pb-4">
        <Button render={<Link href={`/client-admin/audits/${audit.id}`} />} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Audit
        </Button>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary/95 h-9 px-4 rounded-md text-sm font-medium transition-colors cursor-pointer"
        >
          <Printer className="h-4 w-4" />
          Print / Save as PDF
        </button>
      </div>

      {/* Printable Report Container */}
      <div className="space-y-8 font-sans">
        {/* Header Block */}
        <div className="border-b pb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <span className="text-[10px] font-bold font-mono text-primary uppercase tracking-widest">ISO 17021 Formal Audit Report</span>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground mt-1">Audit Assessment & Findings</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Reference ID: {audit.id}</p>
          </div>
          <div className="text-right sm:text-right">
            <span className="text-sm font-bold bg-muted/60 px-3 py-1.5 rounded border uppercase">
              {audit.status.replace(/_/g, " ")}
            </span>
            <p className="text-xs text-muted-foreground mt-2">Compiled on: {format(new Date(), "dd MMM yyyy")}</p>
          </div>
        </div>

        {/* Client & CB Information */}
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground border-b pb-1">Client Details (Auditee)</h2>
            <div className="text-sm space-y-1">
              <p className="font-semibold text-foreground">{audit.clientOrg.name}</p>
              <p className="text-muted-foreground">Reg. Number: {audit.clientOrg.registeredId || "—"}</p>
              <p className="text-muted-foreground">{audit.clientOrg.registeredAddress}</p>
              <p className="text-muted-foreground">Email: {audit.clientOrg.contactEmail || "—"}</p>
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground border-b pb-1">Assessment Schedule & Team</h2>
            <div className="text-sm space-y-1">
              <p className="text-muted-foreground">
                <span className="font-semibold text-foreground">Type:</span> {audit.auditType.replace(/_/g, " ")}
              </p>
              <p className="text-muted-foreground">
                <span className="font-semibold text-foreground">Dates:</span>{" "}
                {format(new Date(audit.dateFrom), "dd MMM yyyy")} – {format(new Date(audit.dateTo), "dd MMM yyyy")}
              </p>
              <p className="text-muted-foreground">
                <span className="font-semibold text-foreground">Lead Auditor:</span> {audit.leadAuditor?.name ?? "—"} ({audit.leadAuditor?.email ?? ""})
              </p>
            </div>
          </div>
        </div>

        {/* Executive Summary Section */}
        {audit.summary && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-foreground border-b pb-1 mt-6">1. Executive Summary</h2>
            <div className="grid gap-4 sm:grid-cols-2 text-sm">
              <div className="space-y-2 border p-3 rounded-lg">
                <p className="font-semibold text-muted-foreground text-xs uppercase">Audit Objectives</p>
                <p className="font-medium text-foreground">{audit.summary.objectivesMet ? "Met successfully" : "Not fully met"}</p>
                <p className="text-xs text-muted-foreground">{audit.summary.objectivesComments || "No additional comments"}</p>
              </div>

              <div className="space-y-2 border p-3 rounded-lg">
                <p className="font-semibold text-muted-foreground text-xs uppercase">Management System Performance</p>
                <p className="font-medium text-foreground">{audit.summary.msMeetsRequirements ? "Complies with standards" : "Deficiencies identified"}</p>
                <p className="text-xs text-muted-foreground">{audit.summary.msComments || "No additional comments"}</p>
              </div>

              <div className="space-y-2 border p-3 rounded-lg">
                <p className="font-semibold text-muted-foreground text-xs uppercase">Internal Audit Capability</p>
                <p className="font-medium text-foreground">{audit.summary.internalAuditEffective ? "Effective" : "Ineffective/Needs improvement"}</p>
                <p className="text-xs text-muted-foreground">{audit.summary.internalAuditComments || "No additional comments"}</p>
              </div>

              <div className="space-y-2 border p-3 rounded-lg">
                <p className="font-semibold text-muted-foreground text-xs uppercase">Management Review Process</p>
                <p className="font-medium text-foreground">{audit.summary.managementReviewEffective ? "Effective" : "Ineffective/Needs improvement"}</p>
                <p className="text-xs text-muted-foreground">{audit.summary.managementReviewComments || "No additional comments"}</p>
              </div>
            </div>

            {audit.summary.generalCommentary && (
              <div className="text-sm space-y-1.5 mt-2">
                <p className="font-semibold text-muted-foreground text-xs uppercase">General Commentary</p>
                <p className="text-muted-foreground whitespace-pre-wrap">{audit.summary.generalCommentary}</p>
              </div>
            )}
          </div>
        )}

        {/* Audit Recommendations */}
        {audit.recommendations.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground border-b pb-1 mt-6">2. Certification Recommendation</h2>
            <ul className="list-disc pl-5 text-sm space-y-1 text-muted-foreground">
              {audit.recommendations.map((rec) => (
                <li key={rec.id}>{rec.recommendation}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Findings and Nonconformities Section */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-foreground border-b pb-1 mt-6">3. Detailed Findings</h2>

          {audit.findings.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No findings (Major NC, Minor NC, OFI, or Observations) recorded.</p>
          ) : (
            <div className="space-y-6">
              {audit.findings.map((f, idx) => (
                <div key={f.id} className="border p-4 rounded-lg space-y-3 print:break-inside-avoid">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm bg-muted px-2 py-0.5 rounded">Finding #{idx + 1}</span>
                      <Badge variant={f.findingType === "NC_MAJOR" ? "destructive" : f.findingType === "NC_MINOR" ? "secondary" : "outline"}>
                        {f.findingType.replace(/_/g, " ")}
                      </Badge>
                      <Badge variant="outline">{f.verificationStatus}</Badge>
                    </div>
                    {f.standard && (
                      <span className="text-xs font-semibold text-muted-foreground">
                        {f.standard.code} ({f.standard.title}) · Clause {f.clause}
                      </span>
                    )}
                  </div>

                  <div className="text-sm grid gap-4 sm:grid-cols-2">
                    {f.statementOfNc && (
                      <div className="space-y-1">
                        <p className="font-semibold text-xs text-muted-foreground uppercase">Statement of Nonconformity / Finding</p>
                        <p className="text-foreground">{f.statementOfNc}</p>
                      </div>
                    )}
                    {f.objectiveEvidence && (
                      <div className="space-y-1">
                        <p className="font-semibold text-xs text-muted-foreground uppercase">Objective Evidence Observed</p>
                        <p className="text-foreground">{f.objectiveEvidence}</p>
                      </div>
                    )}
                  </div>

                  {/* Root cause and action answers */}
                  {f.clientCorrectiveAction && (
                    <div className="bg-muted/30 p-3 rounded border border-muted text-sm space-y-2">
                      <p className="font-bold text-xs uppercase text-primary">Client Corrective Action Response</p>
                      {f.clientRootCause && (
                        <div>
                          <span className="font-semibold text-xs text-muted-foreground block">Root Cause analysis</span>
                          <span className="text-foreground">{f.clientRootCause}</span>
                        </div>
                      )}
                      {f.clientCorrection && (
                        <div>
                          <span className="font-semibold text-xs text-muted-foreground block">Immediate Correction</span>
                          <span className="text-foreground">{f.clientCorrection}</span>
                        </div>
                      )}
                      <div>
                        <span className="font-semibold text-xs text-muted-foreground block">Preventive Corrective Action</span>
                        <span className="text-foreground">{f.clientCorrectiveAction}</span>
                      </div>
                    </div>
                  )}

                  {/* Comments/Discussion view on printed report */}
                  {f.comments.length > 0 && (
                    <div className="space-y-2 border-t pt-2">
                      <p className="font-bold text-xs uppercase text-muted-foreground">Discussion & Clarifications History</p>
                      <div className="space-y-1.5">
                        {f.comments.map((comment) => (
                          <div key={comment.id} className="text-xs bg-muted/20 p-2 rounded border">
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-bold text-primary">{comment.user.name} ({comment.user.role.replace(/_/g, " ")})</span>
                              <span className="text-[10px] text-muted-foreground">{format(new Date(comment.createdAt), "dd MMM yyyy HH:mm")}</span>
                            </div>
                            <p className="text-muted-foreground">{comment.comment}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
