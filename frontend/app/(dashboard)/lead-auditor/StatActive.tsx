import { prisma } from "@/lib/prisma"
import { ClipboardList } from "lucide-react"
import { StatCard } from "@/components/stat-card"

export default async function StatActive({ userId }: { userId: string }) {
  const count = await prisma.audit.count({ where: { leadAuditorId: userId, status: "IN_PROGRESS" } })
  return <StatCard title="In Progress" value={count} description="Currently conducting" icon={ClipboardList} />
}
