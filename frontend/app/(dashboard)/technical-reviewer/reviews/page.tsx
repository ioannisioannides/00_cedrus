import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { StatCard } from "@/components/stat-card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { Eye, CheckCircle, AlertCircle, Clock } from "lucide-react"

export default async function TechnicalReviewsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "TECHNICAL_REVIEWER") redirect("/")

  const [pending, approved, clarification] = await Promise.all([
    prisma.audit.count({ where: { status: "TECHNICAL_REVIEW" } }),
    prisma.technicalReview.count({ where: { status: "APPROVED" } }),
    prisma.technicalReview.count({ where: { status: "REQUIRES_CLARIFICATION" } }),
    prisma.audit.count({ where: { status: "SUBMITTED" } }),
  ])

  const reviews = await prisma.audit.findMany({
    where: { status: "TECHNICAL_REVIEW" },
    orderBy: { updatedAt: "asc" },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      leadAuditor: { select: { name: true } },
      technicalReview: { select: { status: true, reviewerNotes: true } },
      _count: { select: { findings: true } },
    },
  })

  const submitted = await prisma.audit.findMany({
    where: { status: "SUBMITTED" },
    orderBy: { updatedAt: "asc" },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      leadAuditor: { select: { name: true } },
      _count: { select: { findings: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Technical Reviews</h1>
        <p className="text-muted-foreground">Review submitted audit reports for compliance and completeness.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard title="In Review" value={pending} description="Awaiting your review" icon={Eye} />
        <StatCard title="Approved" value={approved} description="Reviews signed off" icon={CheckCircle} />
        <StatCard title="Clarification Needed" value={clarification} description="Sent back to auditor" icon={AlertCircle} />
      </div>

      {submitted.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Submitted — Awaiting Pickup
            </CardTitle>
            <CardDescription>These audits have been submitted and are queued for review</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead className="text-right">Findings</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {submitted.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <div className="font-medium">{a.clientOrg.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{a.clientOrg.customerId}</div>
                    </TableCell>
                    <TableCell><Badge variant="outline">{a.auditType.replace("_", " ")}</Badge></TableCell>
                    <TableCell className="text-sm">{a.leadAuditor?.name ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm">{a._count.findings}</TableCell>
                    <TableCell className="text-sm">{format(a.updatedAt, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <Button render={<Link href={`/technical-reviewer/reviews/${a.id}`} />} variant="ghost" size="sm">
                        Pick up
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            In Technical Review
          </CardTitle>
          <CardDescription>Audit reports currently under review</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {reviews.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No audits currently in technical review.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead className="text-right">Findings</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead>Review Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {reviews.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <div className="font-medium">{a.clientOrg.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{a.clientOrg.customerId}</div>
                    </TableCell>
                    <TableCell><Badge variant="outline">{a.auditType.replace("_", " ")}</Badge></TableCell>
                    <TableCell className="text-sm">{a.leadAuditor?.name ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm">{a._count.findings}</TableCell>
                    <TableCell className="text-sm whitespace-nowrap">
                      {format(a.dateFrom, "dd MMM")} – {format(a.dateTo, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell>
                      {a.technicalReview ? (
                        <Badge variant={
                          a.technicalReview.status === "APPROVED" ? "default" :
                          a.technicalReview.status === "REJECTED" ? "destructive" : "secondary"
                        }>
                          {a.technicalReview.status.replace("_", " ")}
                        </Badge>
                      ) : (
                        <Badge variant="outline">Pending</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/technical-reviewer/reviews/${a.id}`} />} variant="ghost" size="sm">
                        Review
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
