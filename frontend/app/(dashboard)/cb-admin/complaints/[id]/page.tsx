import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { format } from "date-fns"
import { ComplaintUpdateForm } from "@/components/complaint-update-form"
import { updateComplaintStatus } from "@/lib/actions/complaints"

interface Props { params: Promise<{ id: string }> }

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  RECEIVED: "outline",
  UNDER_INVESTIGATION: "secondary",
  RESOLVED: "default",
  CLOSED: "outline",
  ESCALATED: "destructive",
}

export default async function ComplaintDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const complaint = await prisma.complaint.findUnique({
    where: { id },
    include: {
      clientOrg: { select: { name: true } },
      relatedAudit: { select: { id: true, auditType: true, dateFrom: true } },
      submittedBy: { select: { name: true } },
      assignedInvestigator: { select: { name: true } },
    },
  })

  if (!complaint) notFound()

  const updateAction = updateComplaintStatus.bind(null, id)
  const isClosed = complaint.status === "CLOSED"

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{complaint.complaintNumber}</h1>
            <Badge variant={STATUS_BADGE[complaint.status] ?? "outline"}>
              {complaint.status.replace(/_/g, " ")}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {complaint.complainantName} · {complaint.complaintType.replace(/_/g, " ")} ·{" "}
            Submitted {format(complaint.submittedAt, "dd MMM yyyy")}
          </p>
        </div>
        <Button render={<Link href="/cb-admin/complaints" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      {/* Details */}
      <Card>
        <CardHeader>
          <CardTitle>Complaint Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <div className="font-medium text-muted-foreground">Complainant</div>
              <p>{complaint.complainantName}</p>
              {complaint.complainantEmail && (
                <p className="text-muted-foreground">{complaint.complainantEmail}</p>
              )}
            </div>
            <div>
              <div className="font-medium text-muted-foreground">Related Client</div>
              <p>{complaint.clientOrg?.name ?? "—"}</p>
            </div>
            {complaint.relatedAudit && (
              <div>
                <div className="font-medium text-muted-foreground">Related Audit</div>
                <Link
                  href={`/cb-admin/audits/${complaint.relatedAudit.id}`}
                  className="text-primary hover:underline"
                >
                  {complaint.relatedAudit.auditType.replace(/_/g, " ")} —{" "}
                  {format(complaint.relatedAudit.dateFrom, "dd MMM yyyy")}
                </Link>
              </div>
            )}
            {complaint.assignedInvestigator && (
              <div>
                <div className="font-medium text-muted-foreground">Investigator</div>
                <p>{complaint.assignedInvestigator.name}</p>
              </div>
            )}
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Description</div>
            <p className="whitespace-pre-wrap">{complaint.description}</p>
          </div>
          {complaint.investigationNotes && (
            <div>
              <div className="font-medium text-muted-foreground">Investigation Notes</div>
              <p className="whitespace-pre-wrap">{complaint.investigationNotes}</p>
            </div>
          )}
          {complaint.resolutionDetails && (
            <div>
              <div className="font-medium text-muted-foreground">Resolution Details</div>
              <p className="whitespace-pre-wrap">{complaint.resolutionDetails}</p>
            </div>
          )}
          {complaint.correctiveActions && (
            <div>
              <div className="font-medium text-muted-foreground">Corrective Actions</div>
              <p className="whitespace-pre-wrap">{complaint.correctiveActions}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Update status */}
      {!isClosed && (
        <Card>
          <CardHeader>
            <CardTitle>Update Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ComplaintUpdateForm
              currentStatus={complaint.status}
              investigationNotes={complaint.investigationNotes}
              resolutionDetails={complaint.resolutionDetails}
              correctiveActions={complaint.correctiveActions}
              action={updateAction}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
