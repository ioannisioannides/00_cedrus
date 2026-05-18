import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { Trash2 } from "lucide-react"
import { addTeamMember, removeTeamMember } from "@/lib/actions/team-members"
import { AddTeamMemberForm } from "@/components/team-member-form"

interface Props { params: Promise<{ id: string }> }

const ROLE_LABEL: Record<string, string> = {
  LEAD_AUDITOR: "Lead Auditor",
  AUDITOR: "Auditor",
  TECHNICAL_EXPERT: "Technical Expert",
  TRAINEE: "Trainee",
  OBSERVER: "Observer",
}

export default async function AuditTeamPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }

  const { id: auditId } = await params

  const audit = await prisma.audit.findUnique({
    where: { id: auditId },
    include: {
      clientOrg: { select: { name: true } },
      teamMembers: {
        include: { user: { select: { name: true, email: true } } },
        orderBy: { dateFrom: "asc" },
      },
    },
  })

  if (!audit) redirect("/lead-auditor/audits")

  const isEditable = ["IN_PROGRESS", "REPORT_DRAFT", "SCHEDULED"].includes(audit.status)
  const addAction = addTeamMember.bind(null, auditId)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Audit Team</h1>
          <p className="text-muted-foreground mt-1">
            {audit.clientOrg.name} · {audit.auditType.replace(/_/g, " ")}
          </p>
        </div>
        <Button
          render={<Link href={`/lead-auditor/audits/${auditId}`} />}
          variant="outline"
          size="sm"
        >
          ← Back to Audit
        </Button>
      </div>

      {/* Current team */}
      <Card>
        <CardHeader>
          <CardTitle>Current Team Members ({audit.teamMembers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {audit.teamMembers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No team members added yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  {isEditable && <TableHead className="w-12" />}
                </TableRow>
              </TableHeader>
              <TableBody>
                {audit.teamMembers.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">
                      {m.user?.name ?? m.name}
                      {m.user?.email && (
                        <div className="text-xs text-muted-foreground">{m.user.email}</div>
                      )}
                    </TableCell>
                    <TableCell>{m.title || <span className="text-muted-foreground">—</span>}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{ROLE_LABEL[m.role] ?? m.role}</Badge>
                    </TableCell>
                    <TableCell>{format(m.dateFrom, "dd MMM yyyy")}</TableCell>
                    <TableCell>{format(m.dateTo, "dd MMM yyyy")}</TableCell>
                    {isEditable && (
                      <TableCell>
                        <form
                          action={async () => {
                            "use server"
                            await removeTeamMember(m.id)
                          }}
                        >
                          <button
                            type="submit"
                            className="text-destructive hover:text-destructive/80"
                            aria-label="Remove team member"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </form>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add team member */}
      {isEditable && (
        <Card>
          <CardHeader>
            <CardTitle>Add Team Member</CardTitle>
          </CardHeader>
          <CardContent>
            <AddTeamMemberForm action={addAction} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
