import { prisma } from "@/lib/prisma"
import { CheckCircle } from "lucide-react"
import { StatCard } from "@/components/stat-card"

export default async function StatSubmitted({ userId }: { userId: string }) {
  const count = await prisma.audit.count({
    where: {
      leadAuditorId: userId,
      status: { in: ["SUBMITTED", "TECHNICAL_REVIEW", "DECISION_PENDING", "DECIDED", "CLOSED"] },
    },
  })
  return <StatCard title="Completed" value={count} description="Submitted or closed" icon={CheckCircle} />
}
