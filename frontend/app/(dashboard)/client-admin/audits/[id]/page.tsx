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
  CardTitle,
} from "@/components/ui/card"
import { NCResponseForm } from "@/components/nc-response-form"
import { submitNCResponse } from "@/lib/actions/nc-responses"
import { ChevronLeft } from "lucide-react"
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

  const { id } = await params

  const audit = await prisma.audit.findUnique({
    where: { id },
    include: {
      clientOrg: { select: { name: true } },
      leadAuditor: { select: { name: true } },
      findings: {
        where: { findingType: { in: ["NC_MAJOR", "NC_MINOR"] } },
        orderBy: [{ findingType: "asc" }, { createdAt: "asc" }],
        include: {
          standard: { select: { code: true } },
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
      <div className="flex items-center gap-2">
        <Button render={<Link href="/client-admin/audits" />} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Audits
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">{audit.clientOrg.name}</h1>
        <p className="text-muted-foreground">
          {audit.auditType.replace(/_/g, " ")} ·{" "}
          {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>
            <Badge>{audit.status.replace(/_/g, " ")}</Badge>
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
            {audit.findings.filter((f) => f.verificationStatus === "OPEN").length}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Non-Conformances</h2>

        {audit.findings.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No non-conformances recorded for this audit.
            </CardContent>
          </Card>
        ) : (
          audit.findings.map((f) => {
            const needsResponse = f.verificationStatus === "OPEN" && canRespond
            const boundAction = submitNCResponse.bind(null, f.id)

            return (
              <Card key={f.id}>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Badge variant={FINDING_BADGE[f.findingType] ?? "outline"}>
                      {f.findingType.replace(/_/g, " ")}
                    </Badge>
                    <Badge variant="outline">
                      {NC_STATUS_LABEL[f.verificationStatus] ?? f.verificationStatus}
                    </Badge>
                    {f.standard && (
                      <span className="text-xs text-muted-foreground">{f.standard.code}</span>
                    )}
                    {f.clause && (
                      <span className="text-xs text-muted-foreground">cl. {f.clause}</span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {f.statementOfNc && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                        Statement of Non-Conformance
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

                  {f.verificationStatus !== "OPEN" && f.clientCorrectiveAction && (
                    <div className="rounded-md bg-muted/50 p-3 space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                        Your Response
                      </p>
                      {f.clientRootCause && (
                        <div>
                          <p className="text-xs text-muted-foreground">Root cause</p>
                          <p className="text-sm">{f.clientRootCause}</p>
                        </div>
                      )}
                      {f.clientCorrection && (
                        <div>
                          <p className="text-xs text-muted-foreground">Correction</p>
                          <p className="text-sm">{f.clientCorrection}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs text-muted-foreground">Corrective action</p>
                        <p className="text-sm">{f.clientCorrectiveAction}</p>
                      </div>
                    </div>
                  )}

                  {needsResponse && (
                    <div className="border-t pt-4">
                      <p className="text-sm font-medium mb-3">Submit your response</p>
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
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
