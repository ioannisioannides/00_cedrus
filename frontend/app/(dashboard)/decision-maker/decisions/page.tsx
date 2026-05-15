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
import { CheckSquare, Award, XCircle, Clock } from "lucide-react"

export default async function DecisionsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "DECISION_MAKER") redirect("/")

  const [pending, decided, granted, refused] = await Promise.all([
    prisma.audit.count({ where: { status: "DECISION_PENDING" } }),
    prisma.audit.count({ where: { status: "DECIDED" } }),
    prisma.certificationDecision.count({ where: { decision: "GRANT" } }),
    prisma.certificationDecision.count({ where: { decision: "REFUSE" } }),
  ])

  const pendingAudits = await prisma.audit.findMany({
    where: { status: "DECISION_PENDING" },
    orderBy: { updatedAt: "asc" },
    include: {
      clientOrg: { select: { name: true, customerId: true } },
      leadAuditor: { select: { name: true } },
      technicalReview: { select: { status: true, reviewerNotes: true } },
      certifications: { include: { certification: { include: { standard: true } } } },
      _count: { select: { findings: true } },
    },
  })

  const recentDecisions = await prisma.certificationDecision.findMany({
    orderBy: { decidedAt: "desc" },
    take: 10,
    include: {
      audit: {
        include: {
          clientOrg: { select: { name: true } },
        },
      },
      decisionMaker: { select: { name: true } },
    },
  })

  const DECISION_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    GRANT: "default",
    REFUSE: "destructive",
    SUSPEND: "secondary",
    WITHDRAW: "destructive",
    SPECIAL_AUDIT: "secondary",
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Certification Decisions</h1>
        <p className="text-muted-foreground">Grant, refuse, suspend, or withdraw certifications.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="Awaiting Decision" value={pending} description="Ready for your decision" icon={CheckSquare} />
        <StatCard title="Decided" value={decided} description="All time" icon={Clock} />
        <StatCard title="Grants" value={granted} description="Certifications granted" icon={Award} />
        <StatCard title="Refused" value={refused} description="Certifications refused" icon={XCircle} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckSquare className="h-5 w-5" />
            Pending Decisions
          </CardTitle>
          <CardDescription>Audits that have passed technical review and require your certification decision</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {pendingAudits.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No audits currently awaiting a decision.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Standards</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead className="text-right">Findings</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingAudits.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <div className="font-medium">{a.clientOrg.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{a.clientOrg.customerId}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {a.certifications.map((ac) => (
                          <Badge key={ac.certificationId} variant="outline" className="text-xs">
                            {ac.certification.standard.code}
                          </Badge>
                        ))}
                        {a.certifications.length === 0 && <span className="text-sm text-muted-foreground">—</span>}
                      </div>
                    </TableCell>
                    <TableCell><Badge variant="outline">{a.auditType.replace("_", " ")}</Badge></TableCell>
                    <TableCell className="text-sm">{a.leadAuditor?.name ?? "—"}</TableCell>
                    <TableCell className="text-right text-sm">{a._count.findings}</TableCell>
                    <TableCell className="text-sm whitespace-nowrap">
                      {format(a.dateFrom, "dd MMM")} – {format(a.dateTo, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/decision-maker/decisions/${a.id}`} />} variant="ghost" size="sm">
                        Decide
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {recentDecisions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Decisions</CardTitle>
            <CardDescription>Last 10 certification decisions</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Made by</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentDecisions.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.audit.clientOrg.name}</TableCell>
                    <TableCell>
                      <Badge variant={DECISION_COLOR[d.decision] ?? "outline"}>
                        {d.decision.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{d.decisionMaker.name}</TableCell>
                    <TableCell className="text-sm">{format(d.decidedAt, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <Button render={<Link href={`/decision-maker/decisions/${d.auditId}`} />} variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
