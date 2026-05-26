import { prisma } from "@/lib/prisma"
import { AlertTriangle } from "lucide-react"
import { StatCard } from "@/components/stat-card"

export default async function StatOpenFindings({ userId }: { userId: string }) {
  const count = await prisma.finding.count({
    where: {
      audit: { leadAuditorId: userId },
      findingType: { in: ["NC_MAJOR", "NC_MINOR"] },
      verificationStatus: { in: ["OPEN", "CLIENT_RESPONDED"] },
    },
  })
  return <StatCard title="Open Findings" value={count} description="Awaiting client response" icon={AlertTriangle} />
}
