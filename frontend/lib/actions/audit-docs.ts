"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

type FormState = { error?: string; success?: boolean }

async function requireAuditorRole(auditId: string) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }
  if (auditId) {
    const exists = await prisma.audit.findUnique({ where: { id: auditId }, select: { id: true } })
    if (!exists) throw new Error("Referenced Audit target not found.")
  }
  return session.user
}

// ─── Audit Changes ────────────────────────────────────────────────────────────

export async function saveAuditChanges(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireAuditorRole(auditId)

  const data = {
    changeOfName: formData.get("changeOfName") === "true",
    changeOfScope: formData.get("changeOfScope") === "true",
    changeOfSites: formData.get("changeOfSites") === "true",
    changeOfMsRep: formData.get("changeOfMsRep") === "true",
    changeOfSignatory: formData.get("changeOfSignatory") === "true",
    changeOfEmployeeCount: formData.get("changeOfEmployeeCount") === "true",
    changeOfContactInfo: formData.get("changeOfContactInfo") === "true",
    otherHasChange: formData.get("otherHasChange") === "true",
    otherDescription: (formData.get("otherDescription") as string) || "",
  }

  await prisma.auditChanges.upsert({
    where: { auditId },
    create: { auditId, ...data },
    update: data,
  })

  revalidatePath(`/lead-auditor/audits/${auditId}/docs`)
  revalidatePath(`/cb-admin/audits/${auditId}`)
  return { success: true }
}

// ─── Audit Plan Review ────────────────────────────────────────────────────────

const PlanReviewSchema = z.object({
  deviationsYesNo: z.boolean(),
  deviationsDetails: z.string().default(""),
  issuesAffectingYesNo: z.boolean(),
  issuesAffectingDetails: z.string().default(""),
  nextAuditDateFrom: z.string().optional(),
  nextAuditDateTo: z.string().optional(),
})

export async function saveAuditPlanReview(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireAuditorRole(auditId)

  const parsed = PlanReviewSchema.safeParse({
    deviationsYesNo: formData.get("deviationsYesNo") === "true",
    deviationsDetails: (formData.get("deviationsDetails") as string) || "",
    issuesAffectingYesNo: formData.get("issuesAffectingYesNo") === "true",
    issuesAffectingDetails: (formData.get("issuesAffectingDetails") as string) || "",
    nextAuditDateFrom: formData.get("nextAuditDateFrom") || undefined,
    nextAuditDateTo: formData.get("nextAuditDateTo") || undefined,
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const data = {
    deviationsYesNo: parsed.data.deviationsYesNo,
    deviationsDetails: parsed.data.deviationsDetails,
    issuesAffectingYesNo: parsed.data.issuesAffectingYesNo,
    issuesAffectingDetails: parsed.data.issuesAffectingDetails,
    nextAuditDateFrom: parsed.data.nextAuditDateFrom
      ? new Date(parsed.data.nextAuditDateFrom)
      : null,
    nextAuditDateTo: parsed.data.nextAuditDateTo
      ? new Date(parsed.data.nextAuditDateTo)
      : null,
  }

  await prisma.auditPlanReview.upsert({
    where: { auditId },
    create: { auditId, ...data },
    update: data,
  })

  revalidatePath(`/lead-auditor/audits/${auditId}/docs`)
  revalidatePath(`/cb-admin/audits/${auditId}`)
  return { success: true }
}

// ─── Audit Summary ────────────────────────────────────────────────────────────

export async function saveAuditSummary(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireAuditorRole(auditId)

  const data = {
    objectivesMet: formData.get("objectivesMet") === "true",
    objectivesComments: (formData.get("objectivesComments") as string) || "",
    scopeAppropriate: formData.get("scopeAppropriate") === "true",
    scopeComments: (formData.get("scopeComments") as string) || "",
    msMeetsRequirements: formData.get("msMeetsRequirements") === "true",
    msComments: (formData.get("msComments") as string) || "",
    managementReviewEffective: formData.get("managementReviewEffective") === "true",
    managementReviewComments: (formData.get("managementReviewComments") as string) || "",
    internalAuditEffective: formData.get("internalAuditEffective") === "true",
    internalAuditComments: (formData.get("internalAuditComments") as string) || "",
    msEffective: formData.get("msEffective") === "true",
    msEffectiveComments: (formData.get("msEffectiveComments") as string) || "",
    correctUseOfLogos: formData.get("correctUseOfLogos") === "true",
    logosComments: (formData.get("logosComments") as string) || "",
    promotedToCommittee: formData.get("promotedToCommittee") === "true",
    committeeComments: (formData.get("committeeComments") as string) || "",
    generalCommentary: (formData.get("generalCommentary") as string) || "",
  }

  await prisma.auditSummary.upsert({
    where: { auditId },
    create: { auditId, ...data },
    update: data,
  })

  revalidatePath(`/lead-auditor/audits/${auditId}/docs`)
  revalidatePath(`/cb-admin/audits/${auditId}`)
  return { success: true }
}

// ─── Recommendations ──────────────────────────────────────────────────────────

export async function addRecommendation(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireAuditorRole(auditId)

  const recommendation = (formData.get("recommendation") as string)?.trim()
  if (!recommendation || recommendation.length < 5) {
    return { error: "Recommendation must be at least 5 characters" }
  }

  await prisma.auditRecommendation.create({ data: { auditId, recommendation } })
  revalidatePath(`/lead-auditor/audits/${auditId}/docs`)
  return { success: true }
}

export async function deleteRecommendation(id: string): Promise<void> {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    return
  }

  const rec = await prisma.auditRecommendation.findUnique({ where: { id } })
  if (!rec) return

  await prisma.auditRecommendation.delete({ where: { id } })
  revalidatePath(`/lead-auditor/audits/${rec.auditId}/docs`)
}
