"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

type FormState = { error?: string; success?: boolean }

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

const WarningSchema = z.object({
  description: z.string().min(10, "Description must be at least 10 characters"),
})

export async function addCompetenceWarning(
  auditorId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireCbAdmin()

  const parsed = WarningSchema.safeParse({ description: formData.get("description") })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const auditor = await prisma.user.findUnique({ where: { id: auditorId } })
  if (!auditor) return { error: "Auditor not found" }

  await prisma.auditorCompetenceWarning.create({
    data: { userId: auditorId, description: parsed.data.description },
  })

  revalidatePath(`/cb-admin/auditors/${auditorId}`)
  return { success: true }
}

export async function removeCompetenceWarning(warningId: string): Promise<void> {
  await requireCbAdmin()
  const warning = await prisma.auditorCompetenceWarning.findUnique({ where: { id: warningId } })
  if (warning) {
    await prisma.auditorCompetenceWarning.delete({ where: { id: warningId } })
    revalidatePath(`/cb-admin/auditors/${warning.userId}`)
  }
}
