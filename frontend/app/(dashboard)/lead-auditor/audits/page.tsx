import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { format } from "date-fns"
import { ClipboardList } from "lucide-react"

export const metadata = { title: "My Audits — Cedrus" }

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  CLIENT_REVIEW: "secondary",
  SUBMITTED: "secondary",
  TECHNICAL_REVIEW: "secondary",
  DECISION_PENDING: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
  CANCELLED: "destructive",
}

export default async function LeadAuditorAuditsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "LEAD_AUDITOR") redirect("/")

  const audits = await prisma.audit.findMany({
    where: { leadAuditorId: session.user.id },
    orderBy: { dateFrom: "desc" },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      _count: { select: { findings: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Audits</h1>
        <p className="text-muted-foreground">
          {audits.length} audit{audits.length !== 1 ? "s" : ""} assigned to you
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5" />
            Assigned Audits
          </CardTitle>
          <CardDescription>Audits where you are the lead auditor</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {audits.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              No audits assigned to you yet.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead className="text-right">Findings</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {audits.map((audit) => (
                  <TableRow key={audit.id}>
                    <TableCell>
                      <div className="font-medium">{audit.clientOrg.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{audit.clientOrg.customerId}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{audit.auditType.replace("_", " ")}</Badge>
                    </TableCell>
                    <TableCell className="text-sm whitespace-nowrap">
                      {format(audit.dateFrom, "dd MMM yyyy")}
                      <br />
                      <span className="text-muted-foreground">→ {format(audit.dateTo, "dd MMM yyyy")}</span>
                    </TableCell>
                    <TableCell className="text-right text-sm">{audit._count.findings}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLOR[audit.status] ?? "outline"}>
                        {audit.status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/lead-auditor/audits/${audit.id}`} />} variant="ghost" size="sm">
                        Open
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
