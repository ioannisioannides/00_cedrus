import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/stat-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ClipboardList, AlertTriangle, FileText, CheckCircle } from "lucide-react"
import { format } from "date-fns"

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  SUBMITTED: "secondary",
  CLOSED: "outline",
  CANCELLED: "destructive",
}

export default async function LeadAuditorDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "LEAD_AUDITOR") redirect("/")

  const userId = session.user.id

  const [activeCount, scheduledCount, openFindings, submittedCount] = await Promise.all([
    prisma.audit.count({ where: { leadAuditorId: userId, status: "IN_PROGRESS" } }),
    prisma.audit.count({ where: { leadAuditorId: userId, status: "SCHEDULED" } }),
    prisma.finding.count({
      where: {
        audit: { leadAuditorId: userId },
        findingType: { in: ["NC_MAJOR", "NC_MINOR"] },
        verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
      },
    }),
    prisma.audit.count({ where: { leadAuditorId: userId, status: { in: ["SUBMITTED", "TECHNICAL_REVIEW", "DECISION_PENDING", "DECIDED", "CLOSED"] } } }),
  ])

  const audits = await prisma.audit.findMany({
    where: {
      leadAuditorId: userId,
      status: { in: ["SCHEDULED", "IN_PROGRESS", "REPORT_DRAFT"] },
    },
    orderBy: { dateFrom: "asc" },
    take: 8,
    include: {
      clientOrg: { select: { name: true } },
      _count: { select: { findings: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Lead Auditor Dashboard</h1>
        <p className="text-muted-foreground">
          Your active audits, findings, and evidence submissions.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="In Progress" value={activeCount} description="Currently conducting" icon={ClipboardList} />
        <StatCard title="Scheduled" value={scheduledCount} description="Upcoming audits" icon={FileText} />
        <StatCard title="Open Findings" value={openFindings} description="Awaiting client response" icon={AlertTriangle} />
        <StatCard title="Completed" value={submittedCount} description="Submitted or closed" icon={CheckCircle} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>My Active Audits</CardTitle>
              <CardDescription>Scheduled, in progress, and report-draft audits</CardDescription>
            </div>
            <Button render={<Link href="/lead-auditor/audits" />} variant="outline" size="sm">
              View all
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {audits.length === 0 ? (
            <p className="py-6 text-sm text-muted-foreground text-center">No active audits assigned to you.</p>
          ) : (
            <div className="divide-y">
              {audits.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium">{a.clientOrg.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {a.auditType.replace("_", " ")} · {format(a.dateFrom, "dd MMM")} – {format(a.dateTo, "dd MMM yyyy")} · {a._count.findings} findings
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={STATUS_COLOR[a.status] ?? "outline"}>
                      {a.status.replace("_", " ")}
                    </Badge>
                    <Button render={<Link href={`/lead-auditor/audits/${a.id}`} />} variant="ghost" size="sm">
                      Open
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
