"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { ComplaintType } from "@prisma/client"

type FormState = { error?: string; success?: boolean }

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

function generateComplaintNumber(): string {
  const year = new Date().getFullYear()
  const rand = Math.floor(Math.random() * 90000) + 10000
  return `CMP-${year}-${rand}`
}

const CreateComplaintSchema = z.object({
  complainantName: z.string().min(2, "Complainant name is required"),
  complainantEmail: z.string().email("Invalid email").or(z.literal("")).default(""),
  complaintType: z.nativeEnum(ComplaintType),
  description: z.string().min(20, "Description must be at least 20 characters"),
  clientOrgId: z.string().optional(),
  relatedAuditId: z.string().optional(),
})

export async function createComplaint(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const user = await requireCbAdmin()

  const parsed = CreateComplaintSchema.safeParse({
    complainantName: formData.get("complainantName"),
    complainantEmail: formData.get("complainantEmail") || "",
    complaintType: formData.get("complaintType"),
    description: formData.get("description"),
    clientOrgId: formData.get("clientOrgId") || undefined,
    relatedAuditId: formData.get("relatedAuditId") || undefined,
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  await prisma.complaint.create({
    data: {
      complaintNumber: generateComplaintNumber(),
      complainantName: parsed.data.complainantName,
      complainantEmail: parsed.data.complainantEmail,
      complaintType: parsed.data.complaintType,
      description: parsed.data.description,
      clientOrgId: parsed.data.clientOrgId ?? null,
      relatedAuditId: parsed.data.relatedAuditId ?? null,
      submittedById: user.id,
    },
  })

  revalidatePath("/cb-admin/complaints")
  return { success: true }
}

export async function updateComplaintStatus(
  complaintId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const user = await requireCbAdmin()

  const status = formData.get("status") as string | null
  const investigationNotes = (formData.get("investigationNotes") as string) || ""
  const resolutionDetails = (formData.get("resolutionDetails") as string) || ""
  const correctiveActions = (formData.get("correctiveActions") as string) || ""

  const validStatuses = ["RECEIVED", "UNDER_INVESTIGATION", "RESOLVED", "CLOSED", "ESCALATED"]
  if (!status || !validStatuses.includes(status)) {
    return { error: "Valid status is required" }
  }

  const complaint = await prisma.complaint.findUnique({ where: { id: complaintId } })
  if (!complaint) return { error: "Complaint not found" }

  const updateData: Record<string, unknown> = {
    status,
    investigationNotes,
    resolutionDetails,
    correctiveActions,
  }

  if (status === "UNDER_INVESTIGATION" && !complaint.investigationStartedAt) {
    updateData.investigationStartedAt = new Date()
    updateData.assignedInvestigatorId = user.id
  }
  if ((status === "RESOLVED" || status === "CLOSED") && !complaint.investigationCompletedAt) {
    updateData.investigationCompletedAt = new Date()
  }

  await prisma.complaint.update({ where: { id: complaintId }, data: updateData })
  revalidatePath(`/cb-admin/complaints/${complaintId}`)
  revalidatePath("/cb-admin/complaints")
  return { success: true }
}
