import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { Building, Calendar, ClipboardList, Edit, Plus, Trash2 } from "lucide-react"
import { format } from "date-fns"
import { addSite, deleteSite, addCertification } from "@/lib/actions/client-orgs"
import { AddSiteForm, AddCertificationForm } from "@/components/client-management-forms"

interface Props {
  params: Promise<{ id: string }>
}

const STATUS_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  DRAFT: "outline",
  SCHEDULED: "secondary",
  IN_PROGRESS: "default",
  REPORT_DRAFT: "secondary",
  SUBMITTED: "secondary",
  TECHNICAL_REVIEW: "secondary",
  DECISION_PENDING: "secondary",
  DECIDED: "default",
  CLOSED: "outline",
  CANCELLED: "destructive",
}

export default async function ClientDetailPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const [client, standards] = await Promise.all([
    prisma.clientOrg.findUnique({
      where: { id },
      include: {
        sites: { orderBy: { siteName: "asc" } },
        certifications: {
          include: { standard: true },
          orderBy: { createdAt: "desc" },
        },
        audits: {
          orderBy: { dateFrom: "desc" },
          take: 10,
          include: {
            leadAuditor: { select: { name: true } },
          },
        },
      },
    }),
    prisma.standard.findMany({ orderBy: { code: "asc" } }),
  ])

  if (!client) notFound()

  const addSiteAction = addSite.bind(null, id)
  const addCertAction = addCertification.bind(null, id)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{client.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="font-mono text-xs">{client.customerId}</Badge>
            {client.registeredId && (
              <span className="text-sm text-muted-foreground">{client.registeredId}</span>
            )}
          </div>
        </div>
        <Button render={<Link href={`/cb-admin/clients/${id}/edit`} />} variant="outline" size="sm">
          <Edit className="h-4 w-4 mr-2" />
          Edit
        </Button>
      </div>

      {/* Info cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Building className="h-4 w-4" />
              Organisation Details
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <div className="text-muted-foreground">{client.registeredAddress || "—"}</div>
            <div>Employees: <span className="font-medium">{client.totalEmployeeCount}</span></div>
            {client.contactEmail && (
              <div>
                Email:{" "}
                <a href={`mailto:${client.contactEmail}`} className="text-primary hover:underline">
                  {client.contactEmail}
                </a>
              </div>
            )}
            {client.contactTelephone && <div>Tel: {client.contactTelephone}</div>}
            {client.signatoryName && (
              <div>
                Signatory: {client.signatoryName}
                {client.signatoryTitle ? ` — ${client.signatoryTitle}` : ""}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Certifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {client.certifications.length === 0 ? (
              <p className="text-sm text-muted-foreground">No certifications yet.</p>
            ) : (
              client.certifications.map((cert) => (
                <div key={cert.id} className="flex items-center justify-between text-sm">
                  <div>
                    <span className="font-medium">{cert.standard.code}</span>
                    {cert.certificationScope && (
                      <p className="text-xs text-muted-foreground line-clamp-1">{cert.certificationScope}</p>
                    )}
                  </div>
                  <Badge
                    variant={
                      cert.certificateStatus === "ACTIVE"
                        ? "default"
                        : cert.certificateStatus === "SUSPENDED" || cert.certificateStatus === "WITHDRAWN"
                        ? "destructive"
                        : "outline"
                    }
                  >
                    {cert.certificateStatus}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sites */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Sites ({client.sites.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {client.sites.length === 0 ? (
            <p className="text-sm text-muted-foreground">No sites registered.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Site Name</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead className="text-right">Employees</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {client.sites.map((site) => (
                  <TableRow key={site.id}>
                    <TableCell className="font-medium">{site.siteName}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{site.siteAddress}</TableCell>
                    <TableCell className="text-right text-sm">{site.siteEmployeeCount ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant={site.active ? "default" : "outline"}>
                        {site.active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <form
                        action={async () => {
                          "use server"
                          await deleteSite(site.id)
                        }}
                      >
                        <button
                          type="submit"
                          className="text-destructive hover:text-destructive/80"
                          aria-label="Delete site"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </form>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-1">
              <Plus className="h-4 w-4" /> Add Site
            </h3>
            <AddSiteForm action={addSiteAction} />
          </div>
        </CardContent>
      </Card>

      {/* Certifications */}
      <Card>
        <CardHeader>
          <CardTitle>Certifications ({client.certifications.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {client.certifications.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Standard</TableHead>
                  <TableHead>Scope</TableHead>
                  <TableHead>Certificate #</TableHead>
                  <TableHead>Expiry</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {client.certifications.map((cert) => (
                  <TableRow key={cert.id}>
                    <TableCell className="font-medium">{cert.standard.code}</TableCell>
                    <TableCell className="text-sm max-w-xs">
                      <p className="line-clamp-2">{cert.certificationScope}</p>
                    </TableCell>
                    <TableCell className="text-sm font-mono">{cert.certificateId || "—"}</TableCell>
                    <TableCell className="text-sm">
                      {cert.expiryDate ? format(cert.expiryDate, "dd MMM yyyy") : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          cert.certificateStatus === "ACTIVE"
                            ? "default"
                            : cert.certificateStatus === "SUSPENDED" || cert.certificateStatus === "WITHDRAWN"
                            ? "destructive"
                            : "outline"
                        }
                      >
                        {cert.certificateStatus}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/clients/${id}/certifications/${cert.id}`} />} variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-1">
              <Plus className="h-4 w-4" /> Add Certification
            </h3>
            <AddCertificationForm action={addCertAction} standards={standards} />
          </div>
        </CardContent>
      </Card>

      {/* Recent audits */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-4 w-4" />
              Recent Audits
            </CardTitle>
            <CardDescription>Last 10 audits for this client</CardDescription>
          </div>
          <Button render={<Link href={`/cb-admin/audits/new?clientOrgId=${id}`} />} size="sm">
            New Audit
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {client.audits.length === 0 ? (
            <div className="flex flex-col items-center py-10 text-center gap-3">
              <Calendar className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No audits yet.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Lead Auditor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {client.audits.map((audit) => (
                  <TableRow key={audit.id}>
                    <TableCell>
                      <Badge variant="outline">{audit.auditType}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {format(audit.dateFrom, "dd MMM yyyy")} – {format(audit.dateTo, "dd MMM yyyy")}
                    </TableCell>
                    <TableCell className="text-sm">{audit.leadAuditor?.name ?? "Unassigned"}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLOR[audit.status] ?? "outline"}>
                        {audit.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button render={<Link href={`/cb-admin/audits/${audit.id}`} />} variant="ghost" size="sm">
                        View
                      </Button>
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
