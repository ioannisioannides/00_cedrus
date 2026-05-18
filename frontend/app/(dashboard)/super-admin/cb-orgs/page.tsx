import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { Building2, Plus } from "lucide-react"
import { CreateCbOrgForm } from "@/components/super-admin-forms"
import { toggleCbOrgActive } from "@/lib/actions/super-admin"

export default async function CbOrgsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "SUPER_ADMIN") redirect("/")

  const cbOrgs = await prisma.cbOrg.findMany({
    orderBy: { name: "asc" },
    include: {
      _count: { select: { users: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">CB Organisations</h1>
        <p className="text-muted-foreground">{cbOrgs.length} certification body organisation{cbOrgs.length !== 1 ? "s" : ""}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Certification Bodies
          </CardTitle>
          <CardDescription>All organisations registered as certification bodies on the platform</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {cbOrgs.length === 0 ? (
            <p className="px-6 py-8 text-sm text-muted-foreground text-center">No CB organisations found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead className="text-right">Users</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {cbOrgs.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell className="font-medium">{org.name}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">{org.code}</TableCell>
                    <TableCell className="text-right text-sm">{org._count.users}</TableCell>
                    <TableCell>
                      <Badge variant={org.isActive ? "default" : "outline"}>
                        {org.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{format(org.createdAt, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <form action={async () => {
                        "use server"
                        await toggleCbOrgActive(org.id, !org.isActive)
                      }}>
                        <Button type="submit" variant="ghost" size="sm">
                          {org.isActive ? "Deactivate" : "Activate"}
                        </Button>
                      </form>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add CB Organisation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CreateCbOrgForm />
        </CardContent>
      </Card>
    </div>
  )
}
