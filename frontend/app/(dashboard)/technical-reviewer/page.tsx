import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/stat-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Eye, CheckCircle, AlertCircle, Clock } from "lucide-react"
import { format } from "date-fns"

export default async function TechnicalReviewerDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "TECHNICAL_REVIEWER") redirect("/")

  const [pending, approved, clarification, submitted] = await Promise.all([
    prisma.audit.count({ where: { status: "TECHNICAL_REVIEW" } }),
    prisma.technicalReview.count({ where: { status: "APPROVED" } }),
    prisma.technicalReview.count({ where: { status: "REQUIRES_CLARIFICATION" } }),
    prisma.audit.count({ where: { status: "SUBMITTED" } }),
  ])

  const queue = await prisma.audit.findMany({
    where: { status: { in: ["SUBMITTED", "TECHNICAL_REVIEW"] } },
    orderBy: { updatedAt: "asc" },
    take: 8,
    include: {
      clientOrg: { select: { name: true } },
      leadAuditor: { select: { name: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Technical Reviewer Dashboard</h1>
        <p className="text-muted-foreground">
          Review submitted audit reports for completeness and compliance.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="In Review" value={pending} description="Awaiting your review" icon={Eye} />
        <StatCard title="Submitted" value={submitted} description="Queued for pickup" icon={Clock} />
        <StatCard title="Approved" value={approved} description="Reviews signed off" icon={CheckCircle} />
        <StatCard title="Clarification" value={clarification} description="Sent back to auditor" icon={AlertCircle} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Review Queue</CardTitle>
              <CardDescription>Submitted and in-review audit reports</CardDescription>
            </div>
            <Button render={<Link href="/technical-reviewer/reviews" />} variant="outline" size="sm">
              View all
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {queue.length === 0 ? (
            <p className="py-6 text-sm text-muted-foreground text-center">No audits awaiting review.</p>
          ) : (
            <div className="divide-y">
              {queue.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium">{a.clientOrg.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {a.auditType.replace("_", " ")} · {a.leadAuditor?.name ?? "Unassigned"} · {format(a.updatedAt, "dd MMM")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={a.status === "TECHNICAL_REVIEW" ? "default" : "secondary"}>
                      {a.status === "TECHNICAL_REVIEW" ? "In Review" : "Submitted"}
                    </Badge>
                    <Button render={<Link href={`/technical-reviewer/reviews/${a.id}`} />} variant="ghost" size="sm">
                      {a.status === "TECHNICAL_REVIEW" ? "Review" : "Pick up"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


