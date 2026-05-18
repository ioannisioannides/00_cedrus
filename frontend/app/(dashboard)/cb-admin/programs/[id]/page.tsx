import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { AuditProgramEditForm } from "@/components/audit-program-form"
import { updateAuditProgram } from "@/lib/actions/audit-programs"

interface Props { params: Promise<{ id: string }> }

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  ACTIVE: "default",
  COMPLETED: "secondary",
  CANCELLED: "destructive",
}

const AUDIT_STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  SUBMITTED: "secondary",
  TECHNICAL_REVIEW: "secondary",
  DECISION_PENDING: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
  CANCELLED: "destructive",
}

export default async function AuditProgramDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const program = await prisma.auditProgram.findUnique({
    where: { id },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      createdBy: { select: { name: true } },
      audits: {
        orderBy: { dateFrom: "asc" },
        include: { leadAuditor: { select: { name: true } } },
      },
    },
  })

  if (!program) notFound()

  const updateAction = updateAuditProgram.bind(null, id)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{program.title}</h1>
            <Badge variant={STATUS_BADGE[program.status] ?? "outline"}>
              {program.status}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {program.clientOrg.name} · {program.year} · Created by {program.createdBy.name}
          </p>
        </div>
        <Button render={<Link href="/cb-admin/programs" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      {/* Audits in program */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Audits in this Program ({program.audits.length})</CardTitle>
            <CardDescription>All audits assigned to this program</CardDescription>
          </div>
          <Button render={<Link href={`/cb-admin/audits/new?programId=${id}&clientOrgId=${program.clientOrg.customerId}`} />} size="sm">
            New Audit
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {program.audits.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No audits in this program yet.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {program.audits.map((audit) => (
                  <TableRow key={audit.id}>
                    <TableCell>
                      <Badge variant="outline">{audit.auditType.replace(/_/g, " ")}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell className="text-sm">
                      {audit.leadAuditor?.name ?? <span className="text-muted-foreground">Unassigned</span>}
                    </TableCell>
                    <TableCell>
                      <Badge variant={AUDIT_STATUS_BADGE[audit.status] ?? "outline"}>
                        {audit.status.replace(/_/g, " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/audits/${audit.id}`} />} variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Edit program */}
      <Card>
        <CardHeader>
          <CardTitle>Edit Program</CardTitle>
        </CardHeader>
        <CardContent>
          <AuditProgramEditForm program={program} action={updateAction} />
        </CardContent>
      </Card>
    </div>
  )
}
