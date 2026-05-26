import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

export default async function ActiveAuditsList({ userId }: { userId: string }) {
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
      <CardContent className="p-0">
        {audits.length === 0 ? (
          <div className="py-10 text-center text-sm text-muted-foreground">No active audits.</div>
        ) : (
          <div className="divide-y">
            {audits.map((a) => (
              <div key={a.id} className="flex items-center justify-between px-6 py-3">
                <div>
                  <p className="text-sm font-medium">{a.clientOrg.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {a.status.replace("_", " ")} · {format(a.dateFrom, "dd MMM")} – {format(a.dateTo, "dd MMM yyyy")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">{a._count.findings} findings</Badge>
                  <Badge variant={STATUS_COLOR[a.status] ?? "outline"}>{a.status.replace("_", " ")}</Badge>
                  <Button render={<Link href={`/lead-auditor/audits/${a.id}`} />} variant="ghost" size="sm">
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
