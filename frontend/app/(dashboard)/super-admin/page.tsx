import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { StatCard } from "@/components/stat-card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { Building2, Users, FileText, BarChart3 } from "lucide-react"
import { format } from "date-fns"

export default async function SuperAdminDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "SUPER_ADMIN") redirect("/")

  const [cbOrgCount, userCount, clientCount, auditCount] = await Promise.all([
    prisma.cbOrg.count(),
    prisma.user.count(),
    prisma.clientOrg.count(),
    prisma.audit.count(),
  ])

  const cbOrgs = await prisma.cbOrg.findMany({
    orderBy: { name: "asc" },
    include: { _count: { select: { users: true } } },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Super Admin</h1>
        <p className="text-muted-foreground">Platform-wide administration and oversight.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="CB Organisations" value={cbOrgCount} description="Certification bodies" icon={Building2} />
        <StatCard title="Users" value={userCount} description="Platform users" icon={Users} />
        <StatCard title="Client Orgs" value={clientCount} description="Auditee organisations" icon={FileText} />
        <StatCard title="Audits" value={auditCount} description="All time" icon={BarChart3} />
      </div>

      <div className="flex gap-3">
        <Button render={<Link href="/super-admin/cb-orgs" />} variant="outline" size="sm">
          CB Orgs
        </Button>
        <Button render={<Link href="/super-admin/users" />} variant="outline" size="sm">
          Users
        </Button>
        <Button render={<Link href="/super-admin/standards" />} variant="outline" size="sm">
          Standards
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Certification Bodies</CardTitle>
          <CardDescription>All registered certification body organisations</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {cbOrgs.length === 0 ? (
            <p className="px-6 py-8 text-sm text-muted-foreground text-center">No CB organisations registered.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead className="text-right">Users</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cbOrgs.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell className="font-medium">{org.name}</TableCell>
                    <TableCell className="text-sm font-mono text-muted-foreground">{org.code}</TableCell>
                    <TableCell className="text-right text-sm">{org._count.users}</TableCell>
                    <TableCell className="text-sm">{format(org.createdAt, "dd MMM yyyy")}</TableCell>
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
