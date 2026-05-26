import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"

export default async function AuditorsPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const isSuperAdmin = session.user.role === "SUPER_ADMIN"
  const cbOrgId = session.user.organizationId
  if (!isSuperAdmin && !cbOrgId) redirect("/")

  const auditorScope = isSuperAdmin ? {} : { cbOrgId }

  const auditors = await prisma.user.findMany({
    where: { ...auditorScope, role: "LEAD_AUDITOR", isActive: true },
    orderBy: { name: "asc" },
    include: {
      cbOrg: { select: { name: true } },
      _count: {
        select: {
          auditsLed: {
            where: { status: { in: ["SCHEDULED", "IN_PROGRESS", "REPORT_DRAFT"] } },
          },
        },
      },
    },
  })

  const allAuditors = await prisma.user.count({ where: { ...auditorScope, role: "LEAD_AUDITOR" } })
  const active = await prisma.user.count({ where: { ...auditorScope, role: "LEAD_AUDITOR", isActive: true } })
  // Count auditors with at least one active audit (assigned)
  const assigned = await prisma.user.count({
    where: {
      ...auditorScope,
      role: "LEAD_AUDITOR",
      isActive: true,
      auditsLed: {
        some: { status: { in: ["SCHEDULED", "IN_PROGRESS", "REPORT_DRAFT"] } },
      },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Auditors</h1>
        <p className="text-muted-foreground">Manage lead auditors in your certification body.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Auditors</CardDescription>
            <CardTitle className="text-3xl">{allAuditors}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active</CardDescription>
            <CardTitle className="text-3xl">{active}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Currently Assigned</CardDescription>
            <CardTitle className="text-3xl">{assigned}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lead Auditors</CardTitle>
          <CardDescription>{active} active auditor{active !== 1 ? "s" : ""}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {auditors.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              No auditors registered yet.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>CB Organisation</TableHead>
                  <TableHead>Active Audits</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditors.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{a.email}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.cbOrg?.name ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {a._count.auditsLed > 0 ? (
                        <Badge>{a._count.auditsLed}</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={a.isActive ? "default" : "outline"}>
                        {a.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(a.createdAt, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/auditors/${a.id}`} />} variant="ghost" size="sm">
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
