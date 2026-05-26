import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Building } from "lucide-react"

export const metadata = { title: "Client Organisations — Cedrus" }

export default async function ClientOrgsPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const isSuperAdmin = session.user.role === "SUPER_ADMIN"
  const cbOrgId = session.user.organizationId
  if (!isSuperAdmin && !cbOrgId) redirect("/")

  const auditScope = {
    OR: [
      { createdBy: { is: { cbOrgId } } },
      { leadAuditor: { is: { cbOrgId } } },
    ],
  }

  const clientScope = isSuperAdmin
    ? {}
    : {
        OR: [
          { audits: { some: auditScope } },
          { auditPrograms: { some: { createdBy: { is: { cbOrgId } } } } },
          { complaints: { some: { submittedBy: { is: { cbOrgId } } } } },
          { complaints: { some: { relatedAudit: { is: auditScope } } } },
        ],
      }

  const clients = await prisma.clientOrg.findMany({
    where: clientScope,
    orderBy: { name: "asc" },
    include: {
      _count: { select: { audits: true, certifications: true, sites: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Client Organisations</h1>
          <p className="text-muted-foreground">
            {clients.length} client{clients.length !== 1 ? "s" : ""} registered
          </p>
        </div>
        <Button render={<Link href="/cb-admin/clients/new" />}>
          <Plus className="h-4 w-4 mr-2" />
          Add Client
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            All Clients
          </CardTitle>
          <CardDescription>ISO 17021 auditee organisations</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Building className="h-10 w-10 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">No client organisations yet.</p>
              <Button render={<Link href="/cb-admin/clients/new" />} className="mt-4" variant="outline">
                Add your first client
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Customer ID</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead className="text-right">Audits</TableHead>
                  <TableHead className="text-right">Certs</TableHead>
                  <TableHead className="text-right">Sites</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {clients.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">
                        {c.customerId}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {c.contactEmail || "—"}
                    </TableCell>
                    <TableCell className="text-right text-sm">{c._count.audits}</TableCell>
                    <TableCell className="text-right text-sm">{c._count.certifications}</TableCell>
                    <TableCell className="text-right text-sm">{c._count.sites}</TableCell>
                    <TableCell className="text-right">
                      <Button render={<Link href={`/cb-admin/clients/${c.id}`} />} variant="ghost" size="sm">
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
