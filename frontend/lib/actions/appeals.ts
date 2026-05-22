"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { isRedirectError } from "next/dist/client/components/redirect-error"

type FormState = { error?: string; success?: boolean }

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

function generateAppealNumber(): string {
  const year = new Date().getFullYear()
  const rand = Math.floor(Math.random() * 90000) + 10000
  return `APL-${year}-${rand}`
}

const CreateAppealSchema = z.object({
  appellantName: z.string().min(2, "Appellant name is required"),
  appellantEmail: z.string().email("Invalid email").or(z.literal("")).default(""),
  grounds: z.string().min(20, "Grounds for appeal must be at least 20 characters"),
  relatedComplaintId: z.string().optional(),
  relatedDecisionId: z.string().optional(),
})

export async function createAppeal(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const user = await requireCbAdmin()

    const parsed = CreateAppealSchema.safeParse({
      appellantName: formData.get("appellantName"),
      appellantEmail: formData.get("appellantEmail") || "",
      grounds: formData.get("grounds"),
      relatedComplaintId: formData.get("relatedComplaintId") || undefined,
      relatedDecisionId: formData.get("relatedDecisionId") || undefined,
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    await prisma.appeal.create({
      data: {
        appealNumber: generateAppealNumber(),
        appellantName: parsed.data.appellantName,
        appellantEmail: parsed.data.appellantEmail,
        grounds: parsed.data.grounds,
        relatedComplaintId: parsed.data.relatedComplaintId ?? null,
        relatedDecisionId: parsed.data.relatedDecisionId ?? null,
        submittedById: user.id,
      },
    })

    revalidatePath("/cb-admin/appeals")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error creating appeal:", err)
    return { error: err instanceof Error ? err.message : "Failed to create appeal due to an unexpected error." }
  }
}

export async function updateAppealStatus(
  appealId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const status = formData.get("status") as string | null
    const panelDecision = (formData.get("panelDecision") as string) || null
    const panelJustification = (formData.get("panelJustification") as string) || ""

    const validStatuses = ["RECEIVED", "PANEL_REVIEW", "DECIDED", "CLOSED"]
    if (!status || !validStatuses.includes(status)) {
      return { error: "Valid status is required" }
    }

    const updateData: Record<string, unknown> = { status, panelJustification }

    if (panelDecision && ["UPHELD", "REJECTED", "PARTIALLY_UPHELD"].includes(panelDecision)) {
      updateData.panelDecision = panelDecision
      updateData.panelDecisionDate = new Date()
    }

    await prisma.appeal.update({ where: { id: appealId }, data: updateData })
    revalidatePath(`/cb-admin/appeals/${appealId}`)
    revalidatePath("/cb-admin/appeals")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error updating appeal:", err)
    return { error: err instanceof Error ? err.message : "Failed to update appeal due to an unexpected error." }
  }
}