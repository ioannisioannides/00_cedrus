import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { AuditProgramForm } from "@/components/audit-program-form"
import { createAuditProgram } from "@/lib/actions/audit-programs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ChevronLeft } from "lucide-react"

export default async function NewAuditProgramPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const clientOrgs = await prisma.clientOrg.findMany({
    select: { id: true, name: true },
    orderBy: { name: "asc" },
  })

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-2">
        <Button render={<Link href="/cb-admin/programs" />} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Programs
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Audit Program</CardTitle>
          <CardDescription>
            Create a multi-year audit program for a client organisation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AuditProgramForm action={createAuditProgram} clientOrgs={clientOrgs} />
        </CardContent>
      </Card>
    </div>
  )
}
