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
import { AlertTriangle, CheckSquare, Eye, Plus } from "lucide-react"

interface Props { params: Promise<{ id: string }> }

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

export default async function AuditDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR", "TECHNICAL_REVIEWER", "DECISION_MAKER"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const audit = await prisma.audit.findUnique({
    where: { id },
    include: {
      clientOrg: true,
      leadAuditor: { select: { id: true, name: true, email: true } },
      teamMembers: { include: { user: { select: { name: true } } } },
      findings: {
        orderBy: { createdAt: "desc" },
        include: { createdBy: { select: { name: true } } },
      },
      statusLogs: {
        orderBy: { changedAt: "desc" },
        include: { changedBy: { select: { name: true } } },
      },
      certifications: {
        include: { certification: { include: { standard: true } } },
      },
    },
  })

  if (!audit) redirect("/cb-admin/audits")

  const isEditable = ["IN_PROGRESS", "REPORT_DRAFT"].includes(audit.status)
  const canAddFindings =
    isEditable &&
    ["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{audit.auditType.replace("_", " ")} Audit</h1>
            <Badge variant={audit.status === "CANCELLED" ? "destructive" : audit.status === "CLOSED" ? "outline" : "default"}>
              {audit.status.replace("_", " ")}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {audit.clientOrg.name} · {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
          </p>
        </div>
        <Button render={<Link href="/cb-admin/audits" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      {/* Info */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Client</CardTitle></CardHeader>
          <CardContent className="text-sm">
            <div className="font-medium">{audit.clientOrg.name}</div>
            <div className="text-muted-foreground font-mono text-xs">{audit.clientOrg.customerId}</div>
            <div className="text-muted-foreground mt-1">{audit.clientOrg.registeredAddress}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Audit Team</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-1">
            <div>
              <span className="text-muted-foreground">Lead Auditor: </span>
              {audit.leadAuditor?.name ?? <span className="text-muted-foreground italic">Unassigned</span>}
            </div>
            {audit.teamMembers.map((m) => (
              <div key={m.id} className="text-muted-foreground">
                {m.user?.name ?? m.name} ({m.role})
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Certifications in Scope</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-1">
            {audit.certifications.length === 0 ? (
              <p className="text-muted-foreground">None assigned</p>
            ) : (
              audit.certifications.map((ac) => (
                <div key={ac.certificationId} className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">{ac.certification.standard.code}</Badge>
                  <span className="text-muted-foreground text-xs">{ac.certification.certificateStatus}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

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
          {canAddFindings && (
            <Button render={<Link href={`/lead-auditor/audits/${id}/findings/new`} />} size="sm">
              <Plus className="h-4 w-4 mr-1" />
              Add Finding
            </Button>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {audit.findings.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              No findings recorded yet.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Clause</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>By</TableHead>
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
                    <TableCell className="text-sm max-w-xs truncate">
                      {f.statementOfNc ?? f.observationStatement ?? f.ofiDescription ?? "—"}
                    </TableCell>
                    <TableCell>
                      {(f.findingType === "NC_MAJOR" || f.findingType === "NC_MINOR") ? (
                        <Badge variant={f.verificationStatus === "CLOSED" ? "default" : "outline"}>
                          {f.verificationStatus}
                        </Badge>
                      ) : "—"}
                    </TableCell>
                    <TableCell className="text-sm">{f.createdBy.name}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Status history */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Status History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="relative border-l border-border space-y-4 pl-6">
            {audit.statusLogs.map((log) => (
              <li key={log.id} className="relative">
                <span className="absolute -left-[25px] flex h-4 w-4 items-center justify-center rounded-full bg-background border border-border">
                  <CheckSquare className="h-2.5 w-2.5 text-muted-foreground" />
                </span>
                <div className="text-sm">
                  <span className="font-medium">{log.toStatus.replace("_", " ")}</span>
                  {log.fromStatus && (
                    <span className="text-muted-foreground"> from {log.fromStatus.replace("_", " ")}</span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {log.changedBy.name} · {format(log.changedAt, "dd MMM yyyy HH:mm")}
                </div>
                {log.notes && <p className="text-xs text-muted-foreground mt-0.5">{log.notes}</p>}
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}
