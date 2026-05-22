"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { AuditType, AuditStatus } from "@prisma/client"

const AuditSchema = z.object({
  clientOrgId: z.string().min(1, "Client organisation is required"),
  programId: z.string().optional(),
  auditType: z.nativeEnum(AuditType),
  dateFrom: z.string().refine((v) => !isNaN(Date.parse(v)), "Invalid start date"),
  dateTo: z.string().refine((v) => !isNaN(Date.parse(v)), "Invalid end date"),
  plannedDurationHours: z.coerce.number().positive().optional(),
  leadAuditorId: z.string().optional(),
  durationJustification: z.string().optional().default(""),
})

type FormState = { error?: string; success?: boolean; id?: string }

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

export async function createAudit(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const user = await requireCbAdmin()

    const parsed = AuditSchema.safeParse({
      clientOrgId: formData.get("clientOrgId"),
      programId: formData.get("programId") || undefined,
      auditType: formData.get("auditType"),
      dateFrom: formData.get("dateFrom"),
      dateTo: formData.get("dateTo"),
      plannedDurationHours: formData.get("plannedDurationHours") || undefined,
      leadAuditorId: formData.get("leadAuditorId") || undefined,
      durationJustification: formData.get("durationJustification") || "",
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const { dateFrom, dateTo, ...rest } = parsed.data
    const from = new Date(dateFrom)
    const to = new Date(dateTo)

    if (to < from) return { error: "End date must be on or after the start date." }

    const audit = await prisma.audit.create({
      data: {
        ...rest,
        dateFrom: from,
        dateTo: to,
        createdById: user.id,
      },
    })

    // Log the initial status
    await prisma.auditStatusLog.create({
      data: {
        auditId: audit.id,
        fromStatus: null,
        toStatus: "DRAFT",
        changedById: user.id,
      },
    })

    revalidatePath("/cb-admin/audits")
    revalidatePath(`/cb-admin/clients/${rest.clientOrgId}`)
    return { success: true, id: audit.id }
  } catch (error) {
    console.error("Error creating audit:", error)
    return { error: error instanceof Error ? error.message : "Failed to create audit due to an unexpected error." }
  }
}

export async function updateAudit(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const parsed = AuditSchema.partial({ clientOrgId: true }).safeParse({
      clientOrgId: formData.get("clientOrgId") || undefined,
      programId: formData.get("programId") || undefined,
      auditType: formData.get("auditType"),
      dateFrom: formData.get("dateFrom"),
      dateTo: formData.get("dateTo"),
      plannedDurationHours: formData.get("plannedDurationHours") || undefined,
      leadAuditorId: formData.get("leadAuditorId") || undefined,
      durationJustification: formData.get("durationJustification") || "",
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const { dateFrom, dateTo, ...rest } = parsed.data
    const from = new Date(dateFrom!)
    const to = new Date(dateTo!)

    if (to < from) return { error: "End date must be on or after the start date." }

    await prisma.audit.update({
      where: { id: auditId },
      data: {
        ...rest,
        dateFrom: from,
        dateTo: to,
      },
    })

    revalidatePath(`/cb-admin/audits/${auditId}`)
    return { success: true, id: auditId }
  } catch (error) {
    console.error("Error updating audit:", error)
    return { error: error instanceof Error ? error.message : "Failed to update audit due to an unexpected error." }
  }
}

export async function updateAuditStatus(
  auditId: string,
  newStatus: AuditStatus,
  notes?: string
): Promise<FormState> {
  try {
    const session = await auth()
    if (!session?.user) redirect("/")

    const audit = await prisma.audit.findUnique({ where: { id: auditId } })
    if (!audit) return { error: "Audit not found." }

    // Business rules — valid transitions
    const TRANSITIONS: Partial<Record<AuditStatus, AuditStatus[]>> = {
      DRAFT: ["SCHEDULED", "CANCELLED"],
      SCHEDULED: ["IN_PROGRESS", "CANCELLED"],
      IN_PROGRESS: ["REPORT_DRAFT", "CANCELLED"],
      REPORT_DRAFT: ["CLIENT_REVIEW", "SUBMITTED"],
      CLIENT_REVIEW: ["SUBMITTED"],
      SUBMITTED: ["TECHNICAL_REVIEW"],
      TECHNICAL_REVIEW: ["DECISION_PENDING"],
      DECISION_PENDING: ["DECIDED"],
      DECIDED: ["CLOSED"],
    }

    const allowed = TRANSITIONS[audit.status] ?? []
    if (!allowed.includes(newStatus)) {
      return { error: `Cannot transition from ${audit.status} to ${newStatus}.` }
    }

    await prisma.$transaction([
      prisma.audit.update({ where: { id: auditId }, data: { status: newStatus } }),
      prisma.auditStatusLog.create({
        data: {
          auditId,
          fromStatus: audit.status,
          toStatus: newStatus,
          notes: notes ?? "",
          changedById: session.user.id,
        },
      }),
    ])

    revalidatePath(`/cb-admin/audits/${auditId}`)
    revalidatePath(`/lead-auditor/audits/${auditId}`)
    return { success: true }
  } catch (err) {
    console.error("Error updating audit status:", err)
    return { error: err instanceof Error ? err.message : "Failed to update audit status due to an unexpected error." }
  }
}

export async function assignLeadAuditor(
  auditId: string,
  leadAuditorId: string
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const auditor = await prisma.user.findUnique({
      where: { id: leadAuditorId },
      select: { role: true },
    })
    if (!auditor || auditor.role !== "LEAD_AUDITOR") {
      return { error: "Selected user is not a Lead Auditor." }
    }

    await prisma.audit.update({ where: { id: auditId }, data: { leadAuditorId } })
    revalidatePath(`/cb-admin/audits/${auditId}`)
    return { success: true }
  } catch (err) {
    console.error("Error assigning lead auditor:", err)
    return { error: err instanceof Error ? err.message : "Failed to assign lead auditor." }
  }
}
