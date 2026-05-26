import { prisma } from "@/lib/prisma"
import { FileText } from "lucide-react"
import { StatCard } from "@/components/stat-card"

export default async function StatScheduled({ userId }: { userId: string }) {
  const count = await prisma.audit.count({ where: { leadAuditorId: userId, status: "SCHEDULED" } })
  return <StatCard title="Scheduled" value={count} description="Upcoming audits" icon={FileText} />
}
