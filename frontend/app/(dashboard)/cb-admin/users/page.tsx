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
import { Plus, Users } from "lucide-react"
import { toggleCbUserActive } from "@/lib/actions/users"

const ROLE_LABEL: Record<string, string> = {
  CB_ADMIN: "CB Admin",
  LEAD_AUDITOR: "Lead Auditor",
  TECHNICAL_REVIEWER: "Technical Reviewer",
  DECISION_MAKER: "Decision Maker",
}

export default async function CbAdminUsersPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) redirect("/")

  const users = await prisma.user.findMany({
    where: {
      cbOrgId: session.user.organizationId,
      role: { in: ["CB_ADMIN", "LEAD_AUDITOR", "TECHNICAL_REVIEWER", "DECISION_MAKER"] },
    },
    orderBy: [{ role: "asc" }, { name: "asc" }],
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">{users.length} user{users.length !== 1 ? "s" : ""} in your CB</p>
        </div>
        <Button render={<Link href="/cb-admin/users/new" />} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          New User
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            CB Users
          </CardTitle>
          <CardDescription>Auditors, reviewers, and administrators in your certification body</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
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
                  <TableCell>
                    <Badge variant={u.isActive ? "default" : "secondary"}>
                      {u.isActive ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{format(u.createdAt, "dd MMM yyyy")}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <form action={async () => {
                        "use server"
                        await toggleCbUserActive(u.id, !u.isActive)
                      }}>
                        <Button type="submit" variant="ghost" size="sm">
                          {u.isActive ? "Deactivate" : "Activate"}
                        </Button>
                      </form>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                    No users yet.{" "}
                    <Link href="/cb-admin/users/new" className="text-primary hover:underline">
                      Create one
                    </Link>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
