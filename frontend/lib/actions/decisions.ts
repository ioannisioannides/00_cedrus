"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

type FormState = { error?: string; success?: boolean }

const DecisionSchema = z.object({
  decision: z.enum(["GRANT", "REFUSE", "SUSPEND", "WITHDRAW", "SPECIAL_AUDIT"]),
  decisionNotes: z.string().min(20, "Decision notes must be at least 20 characters"),
})

export async function makeCertificationDecision(
  auditId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user || session.user.role !== "DECISION_MAKER") redirect("/")

  const parsed = DecisionSchema.safeParse({
    decision: formData.get("decision"),
    decisionNotes: formData.get("decisionNotes"),
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const audit = await prisma.audit.findUnique({
    where: { id: auditId },
    include: { certificationDecision: true },
  })
  if (!audit) return { error: "Audit not found." }
  if (audit.status !== "DECISION_PENDING") {
    return { error: "This audit is not awaiting a certification decision." }
  }
  if (audit.certificationDecision) {
    return { error: "A decision has already been recorded for this audit." }
  }

  await prisma.$transaction([
    prisma.certificationDecision.create({
      data: {
        auditId,
        decisionMakerId: session.user.id,
        decision: parsed.data.decision,
        decisionNotes: parsed.data.decisionNotes,
      },
    }),
    prisma.audit.update({
      where: { id: auditId },
      data: { status: "DECIDED" },
    }),
    prisma.auditStatusLog.create({
      data: {
        auditId,
        fromStatus: "DECISION_PENDING",
        toStatus: "DECIDED",
        notes: `Decision: ${parsed.data.decision}. ${parsed.data.decisionNotes}`,
        changedById: session.user.id,
      },
    }),
  ])

  revalidatePath(`/decision-maker/decisions/${auditId}`)
  revalidatePath(`/decision-maker/decisions`)
  revalidatePath(`/cb-admin/audits/${auditId}`)
  return { success: true }
}
