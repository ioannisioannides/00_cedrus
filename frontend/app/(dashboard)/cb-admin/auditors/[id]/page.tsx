import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { AlertTriangle, Trash2 } from "lucide-react"
import { AddCompetenceWarningForm } from "@/components/add-competence-warning-form"
import { addCompetenceWarning, removeCompetenceWarning } from "@/lib/actions/auditors"

interface Props { params: Promise<{ id: string }> }

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
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

export default async function AuditorDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const auditor = await prisma.user.findUnique({
    where: { id },
    include: {
      cbOrg: { select: { name: true } },
      competenceWarnings: { orderBy: { raisedAt: "desc" } },
      auditsLed: {
        orderBy: { dateFrom: "desc" },
        take: 20,
        include: {
          clientOrg: { select: { name: true } },
        },
      },
      auditTeamAssignments: {
        orderBy: { dateFrom: "desc" },
        take: 10,
        include: {
          audit: {
            include: { clientOrg: { select: { name: true } } },
          },
        },
      },
    },
  })

  if (!auditor) notFound()

  const addWarningAction = addCompetenceWarning.bind(null, id)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{auditor.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm text-muted-foreground">{auditor.email}</span>
            <Badge variant={auditor.isActive ? "default" : "outline"}>
              {auditor.isActive ? "Active" : "Inactive"}
            </Badge>
            <Badge variant="outline">
              {auditor.role.replace(/_/g, " ")}
            </Badge>
          </div>
          {auditor.cbOrg && (
            <p className="text-sm text-muted-foreground mt-1">{auditor.cbOrg.name}</p>
          )}
        </div>
        <Button render={<Link href="/cb-admin/auditors" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <div className="text-sm font-medium text-muted-foreground">Audits Led</div>
            <div className="text-3xl font-bold">{auditor.auditsLed.length}</div>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="text-sm font-medium text-muted-foreground">Team Assignments</div>
            <div className="text-3xl font-bold">{auditor.auditTeamAssignments.length}</div>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="text-sm font-medium text-muted-foreground">Competence Warnings</div>
            <div className={`text-3xl font-bold ${auditor.competenceWarnings.length > 0 ? "text-destructive" : ""}`}>
              {auditor.competenceWarnings.length}
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Competence Warnings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            Competence Warnings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {auditor.competenceWarnings.length === 0 ? (
            <p className="text-sm text-muted-foreground">No competence warnings on record.</p>
          ) : (
            <div className="space-y-2">
              {auditor.competenceWarnings.map((w) => (
                <div key={w.id} className="flex items-start justify-between border rounded p-3 gap-3">
                  <div>
                    <p className="text-sm">{w.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {format(w.raisedAt, "dd MMM yyyy")}
                    </p>
                  </div>
                  <form action={async () => {
                    "use server"
                    await removeCompetenceWarning(w.id)
                  }}>
                    <button type="submit" className="text-destructive hover:text-destructive/80" aria-label="Remove warning">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </form>
                </div>
              ))}
            </div>
          )}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-3">Add Warning</h3>
            <AddCompetenceWarningForm action={addWarningAction} />
          </div>
        </CardContent>
      </Card>

      {/* Audits Led */}
      <Card>
        <CardHeader>
          <CardTitle>Audits Led ({auditor.auditsLed.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {auditor.auditsLed.length === 0 ? (
            <p className="px-6 py-8 text-sm text-muted-foreground text-center">No audits led yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditor.auditsLed.map((audit) => (
                  <TableRow key={audit.id}>
                    <TableCell className="font-medium">{audit.clientOrg.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{audit.auditType.replace(/_/g, " ")}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {format(audit.dateFrom, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[audit.status] ?? "outline"}>
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
    </div>
  )
}
