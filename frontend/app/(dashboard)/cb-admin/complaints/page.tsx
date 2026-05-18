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
import { Plus } from "lucide-react"

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  RECEIVED: "outline",
  UNDER_INVESTIGATION: "secondary",
  RESOLVED: "default",
  CLOSED: "outline",
  ESCALATED: "destructive",
}

export default async function ComplaintsPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const complaints = await prisma.complaint.findMany({
    orderBy: { submittedAt: "desc" },
    include: {
      clientOrg: { select: { name: true } },
      assignedInvestigator: { select: { name: true } },
    },
  })

  const byStatus = {
    open: complaints.filter((c) => ["RECEIVED", "UNDER_INVESTIGATION", "ESCALATED"].includes(c.status)).length,
    resolved: complaints.filter((c) => c.status === "RESOLVED").length,
    closed: complaints.filter((c) => c.status === "CLOSED").length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Complaints</h1>
          <p className="text-muted-foreground">Manage complaints from clients and other parties.</p>
        </div>
        <Button render={<Link href="/cb-admin/complaints/new" />}>
          <Plus className="mr-2 h-4 w-4" />
          New Complaint
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Open</CardDescription>
            <CardTitle className="text-3xl">{byStatus.open}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Resolved</CardDescription>
            <CardTitle className="text-3xl">{byStatus.resolved}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Closed</CardDescription>
            <CardTitle className="text-3xl">{byStatus.closed}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Complaints</CardTitle>
          <CardDescription>{complaints.length} complaint{complaints.length !== 1 ? "s" : ""} total</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {complaints.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">No complaints on record.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Number</TableHead>
                  <TableHead>Complainant</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {complaints.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-mono text-sm">{c.complaintNumber}</TableCell>
                    <TableCell className="font-medium">{c.complainantName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{c.complaintType.replace(/_/g, " ")}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {c.clientOrg?.name ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm">{format(c.submittedAt, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[c.status] ?? "outline"}>
                        {c.status.replace(/_/g, " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/complaints/${c.id}`} />} variant="ghost" size="sm">
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
