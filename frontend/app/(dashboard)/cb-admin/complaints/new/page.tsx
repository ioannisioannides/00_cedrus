import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import NewComplaintForm from "@/components/new-complaint-form"

export default async function NewComplaintPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const clientOrgs = await prisma.clientOrg.findMany({
    orderBy: { name: "asc" },
    select: { id: true, name: true },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New Complaint</h1>
          <p className="text-muted-foreground">Record a new complaint.</p>
        </div>
        <Button render={<Link href="/cb-admin/complaints" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Complaint Details</CardTitle>
        </CardHeader>
        <CardContent>
          <NewComplaintForm clientOrgs={clientOrgs} />
        </CardContent>
      </Card>
    </div>
  )
}
