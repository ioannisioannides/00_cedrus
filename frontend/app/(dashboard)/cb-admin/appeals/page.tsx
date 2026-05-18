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
  PANEL_REVIEW: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
}

export default async function AppealsPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const appeals = await prisma.appeal.findMany({
    orderBy: { submittedAt: "desc" },
    include: {
      relatedComplaint: { select: { complaintNumber: true } },
    },
  })

  const byStatus = {
    open: appeals.filter((a) => ["RECEIVED", "PANEL_REVIEW"].includes(a.status)).length,
    decided: appeals.filter((a) => a.status === "DECIDED").length,
    closed: appeals.filter((a) => a.status === "CLOSED").length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Appeals</h1>
          <p className="text-muted-foreground">Manage certification appeals.</p>
        </div>
        <Button render={<Link href="/cb-admin/appeals/new" />}>
          <Plus className="mr-2 h-4 w-4" />
          New Appeal
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
            <CardDescription>Decided</CardDescription>
            <CardTitle className="text-3xl">{byStatus.decided}</CardTitle>
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
          <CardTitle>All Appeals</CardTitle>
          <CardDescription>{appeals.length} appeal{appeals.length !== 1 ? "s" : ""} total</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {appeals.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">No appeals on record.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Number</TableHead>
                  <TableHead>Appellant</TableHead>
                  <TableHead>Related Complaint</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {appeals.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-mono text-sm">{a.appealNumber}</TableCell>
                    <TableCell className="font-medium">{a.appellantName}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.relatedComplaint?.complaintNumber ?? "—"}
                    </TableCell>
                    <TableCell className="text-sm">{format(a.submittedAt, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[a.status] ?? "outline"}>
                        {a.status.replace(/_/g, " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {a.panelDecision
                        ? <Badge variant={a.panelDecision === "UPHELD" ? "default" : a.panelDecision === "REJECTED" ? "destructive" : "secondary"}>
                            {a.panelDecision.replace(/_/g, " ")}
                          </Badge>
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/appeals/${a.id}`} />} variant="ghost" size="sm">
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
