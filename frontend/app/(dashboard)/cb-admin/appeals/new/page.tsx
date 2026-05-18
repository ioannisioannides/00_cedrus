import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import NewAppealForm from "@/components/new-appeal-form"

export default async function NewAppealPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const [complaints, decisions] = await Promise.all([
    prisma.complaint.findMany({
      orderBy: { submittedAt: "desc" },
      select: { id: true, complaintNumber: true, complainantName: true },
    }),
    prisma.certificationDecision.findMany({
      orderBy: { decidedAt: "desc" },
      take: 20,
      include: { audit: { select: { clientOrg: { select: { name: true } } } } },
    }),
  ])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New Appeal</h1>
          <p className="text-muted-foreground">Record a new appeal.</p>
        </div>
        <Button render={<Link href="/cb-admin/appeals" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Appeal Details</CardTitle>
        </CardHeader>
        <CardContent>
          <NewAppealForm complaints={complaints} decisions={decisions} />
        </CardContent>
      </Card>
    </div>
  )
}
