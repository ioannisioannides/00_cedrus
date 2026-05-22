"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { isRedirectError } from "next/dist/client/components/redirect-error"
import { AuditProgramStatus } from "@prisma/client"

const ProgramSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters"),
  clientOrgId: z.string().min(1, "Client organisation is required"),
  year: z.coerce.number().int().min(2000).max(2100),
  objectives: z.string().min(10, "Objectives must be at least 10 characters"),
  risksOpportunities: z.string().optional().default(""),
  status: z.nativeEnum(AuditProgramStatus).optional().default("DRAFT"),
})

type FormState = { error?: string; success?: boolean }

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  // Handle post-seed or database reset stale session cookies cleanly:
  const dbUser = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { id: true, role: true, cbOrgId: true },
  })

  if (!dbUser) {
    redirect("/login")
  }

  return session.user
}

export async function createAuditProgram(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const user = await requireCbAdmin()

    const parsed = ProgramSchema.safeParse({
      title: formData.get("title"),
      clientOrgId: formData.get("clientOrgId"),
      year: formData.get("year"),
      objectives: formData.get("objectives"),
      risksOpportunities: formData.get("risksOpportunities") || "",
      status: formData.get("status") || "DRAFT",
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const conflict = await prisma.auditProgram.findFirst({
      where: { clientOrgId: parsed.data.clientOrgId, year: parsed.data.year, title: parsed.data.title },
    })
    if (conflict) return { error: "An audit program with this title already exists for this client and year." }

    await prisma.auditProgram.create({ data: { ...parsed.data, createdById: user.id } })
    revalidatePath("/cb-admin/programs")
    return { success: true }
  } catch (error) {
    if (isRedirectError(error)) throw error;
    if (isRedirectError(error)) throw error
    console.error("Error creating audit program:", error)
    return { error: error instanceof Error ? error.message : "Failed to create audit program due to an unexpected error." }
  }
}

export async function updateAuditProgram(
  id: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const parsed = ProgramSchema.safeParse({
      title: formData.get("title"),
      clientOrgId: formData.get("clientOrgId"),
      year: formData.get("year"),
      objectives: formData.get("objectives"),
      risksOpportunities: formData.get("risksOpportunities") || "",
      status: formData.get("status") || "DRAFT",
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const conflict = await prisma.auditProgram.findFirst({
      where: {
        clientOrgId: parsed.data.clientOrgId,
        year: parsed.data.year,
        title: parsed.data.title,
        NOT: { id },
      },
    })
    if (conflict) return { error: "An audit program with this title already exists for this client and year." }

    await prisma.auditProgram.update({ where: { id }, data: parsed.data })
    revalidatePath("/cb-admin/programs")
    revalidatePath(`/cb-admin/programs/${id}`)
    return { success: true }
  } catch (error) {
    if (isRedirectError(error)) throw error;
    if (isRedirectError(error)) throw error
    console.error("Error updating audit program:", error)
    return { error: error instanceof Error ? error.message : "Failed to update audit program due to an unexpected error." }
  }
}

export async function deleteAuditProgram(id: string): Promise<FormState> {
  try {
    await requireCbAdmin()

    const hasAudits = await prisma.audit.findFirst({ where: { programId: id } })
    if (hasAudits) {
      return { error: "Cannot delete a program that contains audits. Cancel audits first." }
    }

    await prisma.auditProgram.delete({ where: { id } })
    revalidatePath("/cb-admin/programs")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    if (isRedirectError(err)) throw err
    console.error("Error deleting audit program:", err)
    return { error: err instanceof Error ? err.message : "Failed to delete audit program." }
  }
}
