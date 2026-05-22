"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { isRedirectError } from "next/dist/client/components/redirect-error"
import { TeamMemberRole } from "@prisma/client"

type FormState = { error?: string; success?: boolean }

const TeamMemberSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  title: z.string().default(""),
  role: z.nativeEnum(TeamMemberRole),
  dateFrom: z.string().min(1, "Start date is required"),
  dateTo: z.string().min(1, "End date is required"),
  userId: z.string().optional(),
})

async function requireAuditorRole() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

export async function addTeamMember(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireAuditorRole()

    const parsed = TeamMemberSchema.safeParse({
      name: formData.get("name"),
      title: formData.get("title") || "",
      role: formData.get("role"),
      dateFrom: formData.get("dateFrom"),
      dateTo: formData.get("dateTo"),
      userId: formData.get("userId") || undefined,
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const dateFrom = new Date(parsed.data.dateFrom)
    const dateTo = new Date(parsed.data.dateTo)
    if (dateTo < dateFrom) return { error: "End date must be after start date" }

    await prisma.auditTeamMember.create({
      data: {
        auditId,
        name: parsed.data.name,
        title: parsed.data.title,
        role: parsed.data.role,
        dateFrom,
        dateTo,
        userId: parsed.data.userId || null,
      },
    })

    revalidatePath(`/lead-auditor/audits/${auditId}/team`)
    revalidatePath(`/cb-admin/audits/${auditId}`)
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error adding team member:", err)
    return { error: err instanceof Error ? err.message : "Failed to add team member." }
  }
}

export async function removeTeamMember(id: string): Promise<void> {
  try {
    const session = await auth()
    if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN", "LEAD_AUDITOR"].includes(session.user.role)) {
      return
    }

    const member = await prisma.auditTeamMember.findUnique({ where: { id } })
    if (!member) return

    await prisma.auditTeamMember.delete({ where: { id } })
    revalidatePath(`/lead-auditor/audits/${member.auditId}/team`)
    revalidatePath(`/cb-admin/audits/${member.auditId}`)
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error removing team member:", err)
  }
}