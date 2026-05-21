import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  CLIENT_REVIEW: "default",
  SUBMITTED: "secondary",
  TECHNICAL_REVIEW: "secondary",
  DECISION_PENDING: "secondary",
  DECIDED: "secondary",
  CLOSED: "secondary",
  CANCELLED: "destructive",
}

export default async function ClientAuditsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "CLIENT_ADMIN") redirect("/")

  const clientOrgId = session.user.clientOrgId
  if (!clientOrgId) redirect("/client-admin")

  const audits = await prisma.audit.findMany({
    where: {
      clientOrgId,
      status: {
        in: [
          "SCHEDULED",
          "IN_PROGRESS",
          "REPORT_DRAFT",
          "CLIENT_REVIEW",
          "SUBMITTED",
          "DECIDED",
          "CLOSED",
        ],
      },
    },
    orderBy: { dateFrom: "desc" },
    include: {
      clientOrg: { select: { name: true } },
      leadAuditor: { select: { name: true } },
      _count: {
        select: {
          findings: {
            where: {
              findingType: { in: ["NC_MAJOR", "NC_MINOR"] },
              verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
            },
          },
        },
      },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Audits</h1>
        <p className="text-muted-foreground">View your audit history and respond to findings.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Audit History</CardTitle>
          <CardDescription>{audits.length} audit{audits.length !== 1 ? "s" : ""}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {audits.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">No audits found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead>Open NCs</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {audits.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.clientOrg.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.auditType.replace("_", " ")}
                    </TableCell>
                    <TableCell className="text-sm">
                      {format(a.dateFrom, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.leadAuditor?.name ?? "—"}
                    </TableCell>
                    <TableCell>
                      {a._count.findings > 0 ? (
                        <Badge variant="destructive">{a._count.findings}</Badge>
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLOR[a.status] ?? "outline"}>
                        {a.status.replace(/_/g, " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        render={<Link href={`/client-admin/audits/${a.id}`} />}
                        variant="ghost"
                        size="sm"
                      >
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
