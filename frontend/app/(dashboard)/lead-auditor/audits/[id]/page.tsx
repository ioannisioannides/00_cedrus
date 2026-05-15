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
import { AlertTriangle, Plus } from "lucide-react"
import { StatusTransitionButton } from "@/components/status-transition-button"

interface Props { params: Promise<{ id: string }> }

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

export default async function LeadAuditorAuditDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || session.user.role !== "LEAD_AUDITOR") redirect("/")

  const { id } = await params
  const audit = await prisma.audit.findUnique({
    where: { id, leadAuditorId: session.user.id },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      findings: {
        orderBy: { createdAt: "desc" },
        include: { createdBy: { select: { name: true } } },
      },
      certifications: {
        include: { certification: { include: { standard: true } } },
      },
      sites: { include: { site: { select: { siteName: true } } } },
    },
  })

  if (!audit) redirect("/lead-auditor/audits")

  const isEditable = ["IN_PROGRESS", "REPORT_DRAFT"].includes(audit.status)
  const canSubmit = audit.status === "REPORT_DRAFT"

  const ncMajor = audit.findings.filter((f) => f.findingType === "NC_MAJOR").length
  const ncMinor = audit.findings.filter((f) => f.findingType === "NC_MINOR").length
  const observations = audit.findings.filter((f) => f.findingType === "OBSERVATION").length
  const ofis = audit.findings.filter((f) => f.findingType === "OFI").length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight">
              {audit.auditType.replace("_", " ")} — {audit.clientOrg.name}
            </h1>
            <Badge>{audit.status.replace("_", " ")}</Badge>
          </div>
          <p className="text-muted-foreground text-sm mt-1">
            {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
          </p>
        </div>
        <Button render={<Link href="/lead-auditor/audits" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      {/* Quick stats */}
      <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
        {[
          { label: "Major NC", value: ncMajor, color: "text-destructive" },
          { label: "Minor NC", value: ncMinor, color: "text-amber-600" },
          { label: "Observations", value: observations, color: "" },
          { label: "OFIs", value: ofis, color: "text-muted-foreground" },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="pt-4">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Workflow actions */}
      {audit.status === "IN_PROGRESS" && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Workflow Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusTransitionButton
              auditId={audit.id}
              targetStatus="REPORT_DRAFT"
              label="Mark Report as Draft"
              variant="outline"
            />
          </CardContent>
        </Card>
      )}

      {canSubmit && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Ready to Submit?</CardTitle>
            <CardDescription>
              Submitting will send the audit for client review. Ensure all findings are complete.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StatusTransitionButton
              auditId={audit.id}
              targetStatus="SUBMITTED"
              label="Submit for Client Review"
            />
          </CardContent>
        </Card>
      )}

      {/* Findings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Findings ({audit.findings.length})
            </CardTitle>
            <CardDescription>Nonconformities, observations, and OFIs</CardDescription>
          </div>
          {isEditable && (
            <Button render={<Link href={`/lead-auditor/audits/${id}/findings/new`} />} size="sm">
              <Plus className="h-4 w-4 mr-1" />
              Add Finding
            </Button>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {audit.findings.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              No findings yet.{" "}
              {isEditable && (
                <Link href={`/lead-auditor/audits/${id}/findings/new`} className="text-primary hover:underline">
                  Add the first finding
                </Link>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Clause</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Due</TableHead>
                  <TableHead>Status</TableHead>
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
                    <TableCell className="font-mono text-sm">{f.clause}</TableCell>
                    <TableCell className="text-sm max-w-xs">
                      <p className="line-clamp-2">
                        {f.statementOfNc ?? f.observationStatement ?? f.ofiDescription ?? "—"}
                      </p>
                    </TableCell>
                    <TableCell className="text-sm">
                      {f.dueDate ? format(f.dueDate, "dd MMM yyyy") : "—"}
                    </TableCell>
                    <TableCell>
                      {(f.findingType === "NC_MAJOR" || f.findingType === "NC_MINOR") ? (
                        <Badge variant={f.verificationStatus === "CLOSED" ? "default" : "outline"}>
                          {f.verificationStatus.replace("_", " ")}
                        </Badge>
                      ) : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
