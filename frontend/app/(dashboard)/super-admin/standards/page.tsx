import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { FileText, Plus, Trash2 } from "lucide-react"
import { CreateStandardForm } from "@/components/super-admin-forms"
import { deleteStandard } from "@/lib/actions/super-admin"

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
                  <TableHead />
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
                    <TableCell>
                      {s._count.certifications === 0 && (
                        <form action={async () => {
                          "use server"
                          await deleteStandard(s.id)
                        }}>
                          <Button type="submit" variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </form>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Standard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CreateStandardForm />
        </CardContent>
      </Card>
    </div>
  )
}
