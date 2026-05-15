import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { FileText } from "lucide-react"

export default async function StandardsPage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "SUPER_ADMIN") redirect("/")

  const standards = await prisma.standard.findMany({
    orderBy: { code: "asc" },
    include: {
      _count: { select: { certifications: true } },
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Standards</h1>
        <p className="text-muted-foreground">{standards.length} standard{standards.length !== 1 ? "s" : ""} registered</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            ISO Standards
          </CardTitle>
          <CardDescription>Management system standards registered on the platform</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {standards.length === 0 ? (
            <p className="px-6 py-8 text-sm text-muted-foreground text-center">No standards registered yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>NACE</TableHead>
                  <TableHead>EA</TableHead>
                  <TableHead className="text-right">Certifications</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {standards.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono font-medium">{s.code}</TableCell>
                    <TableCell className="text-sm">{s.title}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{s.naceCode || "—"}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{s.eaCode || "—"}</TableCell>
                    <TableCell className="text-right text-sm">{s._count.certifications}</TableCell>
                    <TableCell className="text-sm">{format(s.createdAt, "dd MMM yyyy")}</TableCell>
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
