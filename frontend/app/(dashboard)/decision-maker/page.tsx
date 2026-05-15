import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/stat-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckSquare, Award, XCircle, BarChart3 } from "lucide-react"
import { format } from "date-fns"

export default async function DecisionMakerDashboard() {
  const session = await auth()
  if (!session?.user || session.user.role !== "DECISION_MAKER") redirect("/")

  const [pending, decided, granted, refused] = await Promise.all([
    prisma.audit.count({ where: { status: "DECISION_PENDING" } }),
    prisma.audit.count({ where: { status: "DECIDED" } }),
    prisma.certificationDecision.count({ where: { decision: "GRANT" } }),
    prisma.certificationDecision.count({ where: { decision: "REFUSE" } }),
  ])

  const queue = await prisma.audit.findMany({
    where: { status: "DECISION_PENDING" },
    orderBy: { updatedAt: "asc" },
    take: 8,
    include: {
      clientOrg: { select: { name: true } },
      leadAuditor: { select: { name: true } },
      certifications: { include: { certification: { include: { standard: { select: { code: true } } } } } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Decision Maker Dashboard</h1>
        <p className="text-muted-foreground">
          Grant, suspend, or revoke certifications based on completed audit reviews.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Awaiting Decision" value={pending} description="Ready for your decision" icon={CheckSquare} />
        <StatCard title="Decided" value={decided} description="All time" icon={BarChart3} />
        <StatCard title="Grants" value={granted} description="Certifications granted" icon={Award} />
        <StatCard title="Refused" value={refused} description="Certifications refused" icon={XCircle} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Pending Decisions</CardTitle>
              <CardDescription>Audits that have passed technical review and require a certification decision</CardDescription>
            </div>
            <Button render={<Link href="/decision-maker/decisions" />} variant="outline" size="sm">
              View all
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {queue.length === 0 ? (
            <p className="py-6 text-sm text-muted-foreground text-center">No audits awaiting a decision.</p>
          ) : (
            <div className="divide-y">
              {queue.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium">{a.clientOrg.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {a.certifications.map((ac) => ac.certification.standard.code).join(", ") || a.auditType.replace("_", " ")}
                      {" · "}{format(a.updatedAt, "dd MMM")}
                    </p>
                  </div>
                  <Button render={<Link href={`/decision-maker/decisions/${a.id}`} />} variant="ghost" size="sm">
                    Decide
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


