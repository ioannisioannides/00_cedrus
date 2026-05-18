"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { FindingType, NCVerificationStatus } from "@prisma/client"

const FindingBaseSchema = z.object({
  auditId: z.string().min(1),
  clause: z.string().min(1, "Clause reference is required"),
  findingType: z.nativeEnum(FindingType),
  standardId: z.string().optional(),
  siteId: z.string().optional(),
})

const NCFindingSchema = FindingBaseSchema.extend({
  findingType: z.literal("NC_MAJOR").or(z.literal("NC_MINOR")),
  objectiveEvidence: z.string().min(10, "Objective evidence must be at least 10 characters"),
  statementOfNc: z.string().min(10, "Statement of nonconformity must be at least 10 characters"),
  auditorExplanation: z.string().optional(),
  dueDate: z.string().optional(),
})

const ObservationSchema = FindingBaseSchema.extend({
  findingType: z.literal("OBSERVATION"),
  observationStatement: z.string().min(10, "Observation statement must be at least 10 characters"),
  observationExplanation: z.string().optional().default(""),
})

const OFISchema = FindingBaseSchema.extend({
  findingType: z.literal("OFI"),
  ofiDescription: z.string().min(10, "Description must be at least 10 characters"),
})

type FormState = { error?: string; success?: boolean; id?: string }

async function requireAuditorOrAdmin() {
  const session = await auth()
  const allowed = ["SUPER_ADMIN", "CB_ADMIN", "LEAD_AUDITOR"]
  if (!session?.user || !allowed.includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

export async function createFinding(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const user = await requireAuditorOrAdmin()

  const findingType = formData.get("findingType") as FindingType | null
  if (!findingType) return { error: "Finding type is required." }

  const base = {
    auditId: formData.get("auditId") as string,
    clause: formData.get("clause") as string,
    findingType,
    standardId: (formData.get("standardId") as string) || undefined,
    siteId: (formData.get("siteId") as string) || undefined,
  }

  // Validate the audit is accessible and in an editable state
  const audit = await prisma.audit.findUnique({
    where: { id: base.auditId },
    select: { status: true, leadAuditorId: true },
  })
  if (!audit) return { error: "Audit not found." }

  const editableStatuses = ["IN_PROGRESS", "REPORT_DRAFT"]
  if (!editableStatuses.includes(audit.status)) {
    return { error: `Cannot add findings to an audit in '${audit.status}' status.` }
  }

  let data: Parameters<typeof prisma.finding.create>[0]["data"]

  if (findingType === "NC_MAJOR" || findingType === "NC_MINOR") {
    const parsed = NCFindingSchema.safeParse({ ...base, ...Object.fromEntries(formData) })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    data = {
      ...base,
      objectiveEvidence: parsed.data.objectiveEvidence,
      statementOfNc: parsed.data.statementOfNc,
      auditorExplanation: parsed.data.auditorExplanation,
      dueDate: parsed.data.dueDate ? new Date(parsed.data.dueDate) : null,
      createdById: user.id,
    }
  } else if (findingType === "OBSERVATION") {
    const parsed = ObservationSchema.safeParse({ ...base, ...Object.fromEntries(formData) })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    data = {
      ...base,
      observationStatement: parsed.data.observationStatement,
      observationExplanation: parsed.data.observationExplanation,
      createdById: user.id,
    }
  } else {
    // OFI
    const parsed = OFISchema.safeParse({ ...base, ...Object.fromEntries(formData) })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    data = {
      ...base,
      ofiDescription: parsed.data.ofiDescription,
      createdById: user.id,
    }
  }

  const finding = await prisma.finding.create({ data })
  revalidatePath(`/lead-auditor/audits/${base.auditId}`)
  revalidatePath(`/cb-admin/audits/${base.auditId}`)
  return { success: true, id: finding.id }
}

export async function updateNCResponse(
  findingId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user) redirect("/")

  const schema = z.object({
    clientRootCause: z.string().min(10, "Root cause analysis is required"),
    clientCorrection: z.string().optional().default(""),
    clientCorrectiveAction: z.string().min(10, "Corrective action is required"),
  })

  const parsed = schema.safeParse(Object.fromEntries(formData))
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  await prisma.finding.update({
    where: { id: findingId },
    data: {
      ...parsed.data,
      verificationStatus: "CLIENT_RESPONDED",
    },
  })

  const finding = await prisma.finding.findUnique({
    where: { id: findingId },
    select: { auditId: true },
  })
  revalidatePath(`/lead-auditor/audits/${finding?.auditId}`)
  revalidatePath(`/client-admin/findings/${findingId}`)
  return { success: true }
}

export async function verifyFinding(
  findingId: string,
  status: NCVerificationStatus,
  notes?: string
): Promise<FormState> {
  const session = await auth()
  if (!session?.user || !["LEAD_AUDITOR", "CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    return { error: "Not authorised to verify findings." }
  }

  const finding = await prisma.finding.findUnique({ where: { id: findingId } })
  if (!finding) return { error: "Finding not found." }
  if (finding.findingType !== "NC_MAJOR" && finding.findingType !== "NC_MINOR") {
    return { error: "Only nonconformities can be verified." }
  }

  await prisma.finding.update({
    where: { id: findingId },
    data: {
      verificationStatus: status,
      verifiedById: session.user.id,
      verifiedAt: new Date(),
      verificationNotes: notes ?? "",
    },
  })

  revalidatePath(`/lead-auditor/audits/${finding.auditId}`)
  return { success: true }
}
