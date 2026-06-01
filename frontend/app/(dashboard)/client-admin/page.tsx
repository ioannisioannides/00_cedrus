import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { Suspense } from "react"
import { StatCard } from "@/components/stat-card"
import StatCardSkeleton from "@/components/stat-card-skeleton"
import OpenFindingsSkeleton from "@/components/open-findings-skeleton"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ClipboardList, AlertCircle, FileText, Award } from "lucide-react"
import { format } from "date-fns"

const FINDING_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  NC_MAJOR: "destructive",
  NC_MINOR: "secondary",
  OBSERVATION: "outline",
  OFI: "outline",
}

export default async function ClientAdminDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "CLIENT_ADMIN") redirect("/")

  const clientOrgId = session.user.clientOrgId
  if (!clientOrgId) {
    // CLIENT_ADMIN with no org assigned — show empty state
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Client Admin Dashboard</h1>
          <p className="text-muted-foreground">Your account is not yet linked to a client organisation. Contact your administrator.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Client Admin Dashboard</h1>
        <p className="text-muted-foreground">
          Track your audit progress, respond to findings, and manage documents.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Suspense fallback={<StatCardSkeleton />}><StatActiveAudits clientOrgId={clientOrgId} /></Suspense>
        <Suspense fallback={<StatCardSkeleton />}><StatOpenFindings clientOrgId={clientOrgId} /></Suspense>
        <Suspense fallback={<StatCardSkeleton />}><StatActiveCerts clientOrgId={clientOrgId} /></Suspense>
        <StatCard title="My Audits" value={0} description="View your audit history" icon={FileText} />
      </div>

      <Suspense fallback={<OpenFindingsSkeleton />}>
        <OpenFindingsList clientOrgId={clientOrgId} />
      </Suspense>
    </div>
  )
}

async function StatActiveAudits({ clientOrgId }: { clientOrgId: string }) {
  const count = await prisma.audit.count({
    where: { clientOrgId, status: { in: ["SCHEDULED", "IN_PROGRESS", "REPORT_DRAFT", "CLIENT_REVIEW"] } },
  })
  return <StatCard title="Active Audits" value={count} description="Currently under audit" icon={ClipboardList} />
}

async function StatOpenFindings({ clientOrgId }: { clientOrgId: string }) {
  const count = await prisma.finding.count({
    where: {
      audit: { clientOrgId },
      findingType: { in: ["NC_MAJOR", "NC_MINOR"] },
      verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
    },
  })
  return <StatCard title="Open Findings" value={count} description="Requiring your response" icon={AlertCircle} />
}

async function StatActiveCerts({ clientOrgId }: { clientOrgId: string }) {
  const count = await prisma.certification.count({
    where: { clientOrgId, certificateStatus: "ACTIVE" },
  })
  return <StatCard title="Certificates" value={count} description="Active certifications" icon={Award} />
}

async function OpenFindingsList({ clientOrgId }: { clientOrgId: string }) {
  const openFindings = await prisma.finding.findMany({
    where: {
      audit: { clientOrgId },
      findingType: { in: ["NC_MAJOR", "NC_MINOR"] },
      verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
    },
    orderBy: [{ findingType: "asc" }, { createdAt: "desc" }],
    take: 10,
    include: {
      audit: { include: { clientOrg: { select: { name: true } } } },
    },
  })
  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Non-Conformances</CardTitle>
        <CardDescription>Findings requiring your corrective action response</CardDescription>
      </CardHeader>
      <CardContent>
        {openFindings.length === 0 ? (
          <p className="py-6 text-sm text-muted-foreground text-center">No open findings requiring action.</p>
        ) : (
          <div className="divide-y">
            {openFindings.map((f) => (
              <div key={f.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium">
                    <span className="text-muted-foreground mr-2 font-mono text-xs">{f.clause}</span>
                    {f.statementOfNc ?? "Non-conformance"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {f.audit.clientOrg.name}
                    {f.dueDate ? ` · Due ${format(f.dueDate, "dd MMM yyyy")}` : ""}
                  </p>
                </div>
                <Badge variant={FINDING_BADGE[f.findingType] ?? "outline"}>
                  {f.findingType.replace("_", " ")}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
