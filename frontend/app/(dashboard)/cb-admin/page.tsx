import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Suspense } from "react"
import { StatCard } from "@/components/stat-card"
import StatCardSkeleton from "@/components/stat-card-skeleton"
import RecentAuditsSkeleton from "@/components/recent-audits-skeleton"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ClipboardList, UserCheck, Building, AlertTriangle } from "lucide-react"
import { format } from "date-fns"

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  SUBMITTED: "secondary",
  TECHNICAL_REVIEW: "secondary",
  DECISION_PENDING: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
  CANCELLED: "destructive",
}

export default async function CbAdminDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "CB_ADMIN") redirect("/")

  const cbOrgId = session.user.organizationId
  if (!cbOrgId) redirect("/")

  const auditScope = {
    OR: [
      { createdBy: { is: { cbOrgId } } },
      { leadAuditor: { is: { cbOrgId } } },
    ],
  }

  const clientScope = {
    OR: [
      { audits: { some: auditScope } },
      { auditPrograms: { some: { createdBy: { is: { cbOrgId } } } } },
      { complaints: { some: { submittedBy: { is: { cbOrgId } } } } },
      { complaints: { some: { relatedAudit: { is: auditScope } } } },
    ],
  }


  // Split each stat and recent audits into their own async components for Suspense
  function StatClientCount() {
    const count = prisma.clientOrg.count({ where: clientScope })
    return <StatCard title="Client Organisations" value={count} description="Registered clients" icon={Building} />
  }
  function StatAuditorCount() {
    const count = prisma.user.count({ where: { cbOrgId, role: "LEAD_AUDITOR", isActive: true } })
    return <StatCard title="Lead Auditors" value={count} description="Active lead auditors" icon={UserCheck} />
  }
  function StatActiveAudits() {
    const count = prisma.audit.count({ where: { ...auditScope, status: { in: ["IN_PROGRESS", "REPORT_DRAFT", "SUBMITTED", "TECHNICAL_REVIEW", "DECISION_PENDING"] } } })
    return <StatCard title="Active Audits" value={count} description="Audits in progress or review" icon={ClipboardList} />
  }
  function StatOpenFindings() {
    const count = prisma.finding.count({
      where: {
        verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
        audit: { is: auditScope },
      },
    })
    return <StatCard title="Open Findings" value={count} description="Pending client response" icon={AlertTriangle} />
  }

  async function RecentAudits() {
    const audits = await prisma.audit.findMany({
      where: { ...auditScope, status: { notIn: ["CLOSED", "CANCELLED"] } },
      orderBy: { dateFrom: "asc" },
      take: 8,
      include: {
        clientOrg: { select: { name: true } },
        leadAuditor: { select: { name: true } },
        _count: { select: { findings: true } },
      },
    })
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Active Audits</CardTitle>
            <CardDescription>Audits currently in progress or awaiting review</CardDescription>
          </div>
          <Button render={<Link href="/cb-admin/audits" />} variant="outline" size="sm">
            View all
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {audits.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              No active audits.{' '}
              <Link href="/cb-admin/audits/new" className="text-primary hover:underline">
                Create one
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {audits.map((a) => (
                <div key={a.id} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <p className="text-sm font-medium">{a.clientOrg.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {a.auditType.replace("_", " ")} · {a.leadAuditor?.name ?? "Unassigned"} ·{' '}
                      {format(a.dateFrom, "dd MMM")} – {format(a.dateTo, "dd MMM yyyy")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">{a._count.findings} findings</Badge>
                    <Badge variant={STATUS_COLOR[a.status] ?? "outline"}>{a.status.replace("_", " ")}</Badge>
                    <Button render={<Link href={`/cb-admin/audits/${a.id}`} />} variant="ghost" size="sm">
                      View
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">CB Admin Dashboard</h1>
        <p className="text-muted-foreground">
          Manage your certification body — audit programs, auditors, and clients.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Suspense fallback={<StatCardSkeleton />}><StatActiveAudits /></Suspense>
        <Suspense fallback={<StatCardSkeleton />}><StatAuditorCount /></Suspense>
        <Suspense fallback={<StatCardSkeleton />}><StatClientCount /></Suspense>
        <Suspense fallback={<StatCardSkeleton />}><StatOpenFindings /></Suspense>
      </div>

      <Suspense fallback={<RecentAuditsSkeleton />}>
        <RecentAudits />
      </Suspense>
    </div>
  )
}
