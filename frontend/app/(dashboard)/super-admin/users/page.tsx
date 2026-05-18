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
import { Plus, Users } from "lucide-react"
import { CreateUserForm } from "@/components/create-user-form"
import { toggleUserActive } from "@/lib/actions/super-admin"

const ROLE_LABEL: Record<string, string> = {
  SUPER_ADMIN: "Super Admin",
  CB_ADMIN: "CB Admin",
  LEAD_AUDITOR: "Lead Auditor",
  TECHNICAL_REVIEWER: "Technical Reviewer",
  DECISION_MAKER: "Decision Maker",
  CLIENT_ADMIN: "Client Admin",
}

export default async function UsersPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "SUPER_ADMIN") redirect("/")

  const [users, cbOrgs] = await Promise.all([
    prisma.user.findMany({
      orderBy: [{ role: "asc" }, { name: "asc" }],
      include: { cbOrg: { select: { name: true } } },
    }),
    prisma.cbOrg.findMany({ orderBy: { name: "asc" }, select: { id: true, name: true } }),
  ])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Users</h1>
        <p className="text-muted-foreground">{users.length} platform user{users.length !== 1 ? "s" : ""}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            All Users
          </CardTitle>
          <CardDescription>Platform users across all certification bodies</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>CB Organisation</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {ROLE_LABEL[u.role] ?? u.role}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{u.cbOrg?.name ?? <span className="text-muted-foreground">—</span>}</TableCell>
                  <TableCell>
                    <Badge variant={u.isActive ? "default" : "secondary"}>
                      {u.isActive ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{format(u.createdAt, "dd MMM yyyy")}</TableCell>
                  <TableCell>
                    <form action={async () => {
                      "use server"
                      await toggleUserActive(u.id, !u.isActive)
                    }}>
                      <Button type="submit" variant="ghost" size="sm">
                        {u.isActive ? "Deactivate" : "Activate"}
                      </Button>
                    </form>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create User
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CreateUserForm cbOrgs={cbOrgs} />
        </CardContent>
      </Card>
    </div>
  )
}
