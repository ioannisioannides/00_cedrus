"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"

const CommentSchema = z.object({
  comment: z.string().min(1, "Comment cannot be empty").max(2000, "Comment is too long"),
})

type FormState = { error?: string; success?: boolean }

export async function addFindingComment(
  findingId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user) {
    return { error: "Unauthorised - please log in" }
  }

  const userId = session.user.id
  const userRole = session.user.role

  const finding = await prisma.finding.findUnique({
    where: { id: findingId },
    select: {
      id: true,
      auditId: true,
      audit: {
        select: {
          clientOrgId: true,
          leadAuditorId: true,
        },
      },
    },
  })

  if (!finding) {
    return { error: "Finding not found" }
  }

  // Authorisation check: Client Admin can only comment on their own organisation's findings
  if (userRole === "CLIENT_ADMIN") {
    if (!session.user.clientOrgId || finding.audit.clientOrgId !== session.user.clientOrgId) {
      return { error: "Unauthorised" }
    }
  }

  const parsed = CommentSchema.safeParse({
    comment: formData.get("comment"),
  })

  if (!parsed.success) {
    return { error: parsed.error.issues[0].message }
  }

  try {
    await prisma.findingComment.create({
      data: {
        findingId,
        userId,
        comment: parsed.data.comment,
      },
    })
  } catch (err) {
    console.error("Failed to save comment:", err)
    return { error: "Failed to add comment" }
  }

  // Revalidate appropriate dashboard paths
  if (userRole === "CLIENT_ADMIN") {
    revalidatePath(`/client-admin/audits/${finding.auditId}`)
  } else {
    revalidatePath(`/cb-admin/audits/${finding.auditId}`)
  }

  return { success: true }
}
