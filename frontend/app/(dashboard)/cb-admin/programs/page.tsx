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
import { Plus } from "lucide-react"
import { format } from "date-fns"

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  ACTIVE: "default",
  COMPLETED: "secondary",
  CANCELLED: "destructive",
}

export default async function AuditProgramsPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const programs = await prisma.auditProgram.findMany({
    orderBy: [{ year: "desc" }, { createdAt: "desc" }],
    include: {
      clientOrg: { select: { name: true } },
      _count: { select: { audits: true } },
    },
  })

  const byStatus = {
    ACTIVE: programs.filter((p) => p.status === "ACTIVE").length,
    DRAFT: programs.filter((p) => p.status === "DRAFT").length,
    COMPLETED: programs.filter((p) => p.status === "COMPLETED").length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Audit Programs</h1>
          <p className="text-muted-foreground">
            Manage multi-year audit programs for client organisations.
          </p>
        </div>
        <Button render={<Link href="/cb-admin/programs/new" />}>
          <Plus className="mr-2 h-4 w-4" />
          New Program
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Programs</CardDescription>
            <CardTitle className="text-3xl">{byStatus.ACTIVE}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Draft</CardDescription>
            <CardTitle className="text-3xl">{byStatus.DRAFT}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Completed</CardDescription>
            <CardTitle className="text-3xl">{byStatus.COMPLETED}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Programs</CardTitle>
          <CardDescription>{programs.length} audit program{programs.length !== 1 ? "s" : ""} total</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {programs.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              No audit programs yet.{" "}
              <Link href="/cb-admin/programs/new" className="text-primary hover:underline">
                Create one
              </Link>
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Audits</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {programs.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.title}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{p.clientOrg.name}</TableCell>
                    <TableCell className="font-mono text-sm">{p.year}</TableCell>
                    <TableCell className="text-sm">{p._count.audits}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLOR[p.status] ?? "outline"}>
                        {p.status.charAt(0) + p.status.slice(1).toLowerCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(p.createdAt, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell>
                      <Button
                        render={<Link href={`/cb-admin/programs/${p.id}`} />}
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
