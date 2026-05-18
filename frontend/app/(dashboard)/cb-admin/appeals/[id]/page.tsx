import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { format } from "date-fns"
import { AppealUpdateForm } from "@/components/appeal-update-form"
import { updateAppealStatus } from "@/lib/actions/appeals"

interface Props { params: Promise<{ id: string }> }

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  RECEIVED: "outline",
  PANEL_REVIEW: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
}

const DECISION_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  UPHELD: "default",
  REJECTED: "destructive",
  PARTIALLY_UPHELD: "secondary",
}

export default async function AppealDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const appeal = await prisma.appeal.findUnique({
    where: { id },
    include: {
      relatedComplaint: { select: { id: true, complaintNumber: true } },
      relatedDecision: {
        include: { audit: { select: { id: true, clientOrg: { select: { name: true } } } } },
      },
      submittedBy: { select: { name: true } },
    },
  })

  if (!appeal) notFound()

  const updateAction = updateAppealStatus.bind(null, id)
  const isClosed = appeal.status === "CLOSED"

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{appeal.appealNumber}</h1>
            <Badge variant={STATUS_BADGE[appeal.status] ?? "outline"}>
              {appeal.status.replace(/_/g, " ")}
            </Badge>
            {appeal.panelDecision && (
              <Badge variant={DECISION_BADGE[appeal.panelDecision] ?? "outline"}>
                {appeal.panelDecision.replace(/_/g, " ")}
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground mt-1">
            {appeal.appellantName} · Submitted {format(appeal.submittedAt, "dd MMM yyyy")}
          </p>
        </div>
        <Button render={<Link href="/cb-admin/appeals" />} variant="outline" size="sm">
          ← Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Appeal Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <div className="font-medium text-muted-foreground">Appellant</div>
              <p>{appeal.appellantName}</p>
              {appeal.appellantEmail && (
                <p className="text-muted-foreground">{appeal.appellantEmail}</p>
              )}
            </div>
            {appeal.relatedComplaint && (
              <div>
                <div className="font-medium text-muted-foreground">Related Complaint</div>
                <Link
                  href={`/cb-admin/complaints/${appeal.relatedComplaint.id}`}
                  className="text-primary hover:underline"
                >
                  {appeal.relatedComplaint.complaintNumber}
                </Link>
              </div>
            )}
            {appeal.relatedDecision && (
              <div>
                <div className="font-medium text-muted-foreground">Related Decision</div>
                <Link
                  href={`/cb-admin/audits/${appeal.relatedDecision.audit.id}`}
                  className="text-primary hover:underline"
                >
                  Decision — {appeal.relatedDecision.audit.clientOrg.name}
                </Link>
              </div>
            )}
            {appeal.panelDecisionDate && (
              <div>
                <div className="font-medium text-muted-foreground">Decision Date</div>
                <p>{format(appeal.panelDecisionDate, "dd MMM yyyy")}</p>
              </div>
            )}
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Grounds for Appeal</div>
            <p className="whitespace-pre-wrap">{appeal.grounds}</p>
          </div>
          {appeal.panelJustification && (
            <div>
              <div className="font-medium text-muted-foreground">Panel Justification</div>
              <p className="whitespace-pre-wrap">{appeal.panelJustification}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {!isClosed && (
        <Card>
          <CardHeader>
            <CardTitle>Update Appeal</CardTitle>
          </CardHeader>
          <CardContent>
            <AppealUpdateForm
              currentStatus={appeal.status}
              currentDecision={appeal.panelDecision ?? null}
              panelJustification={appeal.panelJustification}
              action={updateAction}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
