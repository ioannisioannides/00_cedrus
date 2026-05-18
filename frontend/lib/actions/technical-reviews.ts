"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

type FormState = { error?: string; success?: boolean }

const ReviewSchema = z.object({
  scopeVerified: z.coerce.boolean(),
  objectivesVerified: z.coerce.boolean(),
  findingsReviewed: z.coerce.boolean(),
  conclusionClear: z.coerce.boolean(),
  reviewerNotes: z.string().min(10, "Please provide review notes (min 10 characters)"),
  decision: z.enum(["APPROVED", "REQUIRES_CLARIFICATION", "REJECTED"]),
  clarificationRequested: z.string().optional().default(""),
})

export async function submitTechnicalReview(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user || session.user.role !== "TECHNICAL_REVIEWER") redirect("/")

  const parsed = ReviewSchema.safeParse({
    scopeVerified: formData.get("scopeVerified") === "on",
    objectivesVerified: formData.get("objectivesVerified") === "on",
    findingsReviewed: formData.get("findingsReviewed") === "on",
    conclusionClear: formData.get("conclusionClear") === "on",
    reviewerNotes: formData.get("reviewerNotes"),
    decision: formData.get("decision"),
    clarificationRequested: formData.get("clarificationRequested") || "",
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const audit = await prisma.audit.findUnique({ where: { id: auditId } })
  if (!audit) return { error: "Audit not found." }
  if (audit.status !== "TECHNICAL_REVIEW") {
    return { error: "This audit is not in the Technical Review stage." }
  }

  const nextStatus = parsed.data.decision === "APPROVED" ? "DECISION_PENDING" : "SUBMITTED"

  await prisma.$transaction([
    prisma.technicalReview.upsert({
      where: { auditId },
      create: {
        auditId,
        reviewerId: session.user.id,
        ...parsed.data,
      },
      update: {
        ...parsed.data,
        reviewedAt: new Date(),
      },
    }),
    prisma.audit.update({
      where: { id: auditId },
      data: { status: nextStatus },
    }),
    prisma.auditStatusLog.create({
      data: {
        auditId,
        fromStatus: "TECHNICAL_REVIEW",
        toStatus: nextStatus,
        notes: parsed.data.reviewerNotes,
        changedById: session.user.id,
      },
    }),
  ])

  revalidatePath(`/technical-reviewer/reviews/${auditId}`)
  revalidatePath(`/technical-reviewer/reviews`)
  return { success: true }
}
