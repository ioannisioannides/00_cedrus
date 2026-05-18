import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"

interface Props { params: Promise<{ id: string; certId: string }> }

const CERT_STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  ACTIVE: "default",
  SUSPENDED: "destructive",
  WITHDRAWN: "destructive",
  EXPIRED: "secondary",
}

const ACTION_LABEL: Record<string, string> = {
  ISSUED: "Issued",
  RENEWED: "Renewed",
  SURVEILLANCE_PASSED: "Surveillance Passed",
  SUSPENDED: "Suspended",
  SUSPENSION_LIFTED: "Suspension Lifted",
  WITHDRAWN: "Withdrawn",
  EXPIRED: "Expired",
  SCOPE_EXTENDED: "Scope Extended",
  SCOPE_REDUCED: "Scope Reduced",
  TRANSFER_IN: "Transfer In",
  TRANSFER_OUT: "Transfer Out",
}

export default async function CertificationDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id, certId } = await params
  const cert = await prisma.certification.findUnique({
    where: { id: certId },
    include: {
      standard: true,
      clientOrg: { select: { name: true } },
      surveillanceSchedule: true,
      history: {
        orderBy: { actionDate: "desc" },
        include: { actionBy: { select: { name: true } } },
      },
    },
  })

  if (!cert || cert.clientOrgId !== id) notFound()

  const schedule = cert.surveillanceSchedule

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {cert.standard.code} — {cert.clientOrg.name}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            {cert.certificateId && (
              <span className="text-sm font-mono text-muted-foreground">#{cert.certificateId}</span>
            )}
            <Badge variant={CERT_STATUS_COLOR[cert.certificateStatus] ?? "outline"}>
              {cert.certificateStatus}
            </Badge>
          </div>
        </div>
        <Button render={<Link href={`/cb-admin/clients/${id}`} />} variant="outline" size="sm">
          ← Back to Client
        </Button>
      </div>

      {/* Certification details */}
      <Card>
        <CardHeader>
          <CardTitle>Certificate Details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <div className="font-medium text-muted-foreground">Standard</div>
            <p>{cert.standard.code} — {cert.standard.title}</p>
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Certificate #</div>
            <p className="font-mono">{cert.certificateId || "—"}</p>
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Issue Date</div>
            <p>{cert.issueDate ? format(cert.issueDate, "dd MMM yyyy") : "—"}</p>
          </div>
          <div>
            <div className="font-medium text-muted-foreground">Expiry Date</div>
            <p>{cert.expiryDate ? format(cert.expiryDate, "dd MMM yyyy") : "—"}</p>
          </div>
          <div className="sm:col-span-2">
            <div className="font-medium text-muted-foreground">Scope</div>
            <p className="whitespace-pre-wrap">{cert.certificationScope || "—"}</p>
          </div>
        </CardContent>
      </Card>

      {/* Surveillance Schedule */}
      <Card>
        <CardHeader>
          <CardTitle>Surveillance Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          {!schedule ? (
            <p className="text-sm text-muted-foreground">No surveillance schedule has been set for this certification.</p>
          ) : (
            <div className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <div className="font-medium text-muted-foreground">Cycle Start</div>
                <p>{format(schedule.cycleStart, "dd MMM yyyy")}</p>
              </div>
              <div>
                <div className="font-medium text-muted-foreground">Cycle End</div>
                <p>{format(schedule.cycleEnd, "dd MMM yyyy")}</p>
              </div>
              <div>
                <div className="font-medium text-muted-foreground">Surveillance 1 Due</div>
                <p>{format(schedule.surveillance1DueDate, "dd MMM yyyy")}</p>
              </div>
              <div>
                <div className="font-medium text-muted-foreground">Surveillance 2 Due</div>
                <p>{format(schedule.surveillance2DueDate, "dd MMM yyyy")}</p>
              </div>
              <div>
                <div className="font-medium text-muted-foreground">Recertification Due</div>
                <p>{format(schedule.recertificationDueDate, "dd MMM yyyy")}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Certificate History */}
      <Card>
        <CardHeader>
          <CardTitle>Certificate History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {cert.history.length === 0 ? (
            <p className="px-6 py-8 text-sm text-muted-foreground text-center">No history recorded.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Valid From</TableHead>
                  <TableHead>Valid To</TableHead>
                  <TableHead>By</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cert.history.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="text-sm">{format(h.actionDate, "dd MMM yyyy")}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{ACTION_LABEL[h.action] ?? h.action}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {h.validFrom ? format(h.validFrom, "dd MMM yyyy") : "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {h.validTo ? format(h.validTo, "dd MMM yyyy") : "—"}
                    </TableCell>
                    <TableCell className="text-sm">{h.actionBy?.name ?? "—"}</TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-xs">
                      <p className="line-clamp-2">{h.actionReason || h.internalNotes || "—"}</p>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
