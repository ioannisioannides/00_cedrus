"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

import { CertDecisionType, CertHistoryAction, CertificateStatus } from "@prisma/client"

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
  try {
    const session = await auth()
    if (!session?.user || session.user.role !== "DECISION_MAKER") redirect("/")

    const parsed = DecisionSchema.safeParse({
      decision: formData.get("decision"),
      decisionNotes: formData.get("decisionNotes"),
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const audit = await prisma.audit.findUnique({
      where: { id: auditId },
      include: {
        certificationDecision: true,
        certifications: {
          include: {
            certification: true,
          },
        },
      },
    })
    if (!audit) return { error: "Audit not found." }
    if (audit.status !== "DECISION_PENDING") {
      return { error: "This audit is not awaiting a certification decision." }
    }
    if (audit.certificationDecision) {
      return { error: "A decision has already been recorded for this audit." }
    }

    const decisionType = parsed.data.decision as CertDecisionType
    const notes = parsed.data.decisionNotes
    const now = new Date()

    // We'll perform updates across all associated certifications
    const linkedCerts = audit.certifications.map((ac) => ac.certification)

    await prisma.$transaction(async (tx) => {
      // 1. Create the Decision
      const decision = await tx.certificationDecision.create({
        data: {
          auditId,
          decisionMakerId: session.user.id,
          decision: decisionType,
          decisionNotes: notes,
        },
      })

      // 2. Log status transition
      await tx.auditStatusLog.create({
        data: {
          auditId,
          fromStatus: "DECISION_PENDING",
          toStatus: "DECIDED",
          notes: `Decision: ${decisionType}. ${notes}`,
          changedById: session.user.id,
        },
      })

      // 3. Update Audit Status
      await tx.audit.update({
        where: { id: auditId },
        data: { status: "DECIDED" },
      })

      // 4. Process all linked certifications
      for (const cert of linkedCerts) {
        // Link decision to affected cert
        await tx.certificationDecisionCert.create({
          data: {
            decisionId: decision.id,
            certificationId: cert.id,
          },
        })

        let certStatus: CertificateStatus = "DRAFT"
        let historyAction: CertHistoryAction = "ISSUED"

        if (decisionType === "GRANT") {
          certStatus = "ACTIVE"
          historyAction = cert.issueDate ? "RENEWED" : "ISSUED"

          const issueDate = now
          const expiryDate = new Date(now.getFullYear() + 3, now.getMonth(), now.getDate())

          // Update certification dates
          await tx.certification.update({
            where: { id: cert.id },
            data: {
              certificateStatus: certStatus,
              issueDate,
              expiryDate,
              certificateId: cert.certificateId || `CERT-${cert.id.slice(-6).toUpperCase()}`,
            },
          })

          // Setup automated 3-year surveillance schedule
          const cycleStart = now
          const cycleEnd = expiryDate
          const surveillance1DueDate = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())
          const surveillance2DueDate = new Date(now.getFullYear() + 2, now.getMonth(), now.getDate())
          const recertificationDueDate = new Date(now.getFullYear() + 3, now.getMonth() - 2, now.getDate())

          await tx.surveillanceSchedule.upsert({
            where: { certificationId: cert.id },
            create: {
              certificationId: cert.id,
              cycleStart,
              cycleEnd,
              surveillance1DueDate,
              surveillance2DueDate,
              recertificationDueDate,
            },
            update: {
              cycleStart,
              cycleEnd,
              surveillance1DueDate,
              surveillance2DueDate,
              recertificationDueDate,
            },
          })
        } else if (decisionType === "SUSPEND") {
          certStatus = "SUSPENDED"
          historyAction = "SUSPENDED"

          await tx.certification.update({
            where: { id: cert.id },
            data: { certificateStatus: certStatus },
          })
        } else if (decisionType === "WITHDRAW") {
          certStatus = "WITHDRAWN"
          historyAction = "WITHDRAWN"

          await tx.certification.update({
            where: { id: cert.id },
            data: { certificateStatus: certStatus },
          })
        }

        // Record audit trail history
        await tx.certificateHistory.create({
          data: {
            certificationId: cert.id,
            action: historyAction,
            actionDate: now,
            relatedAuditId: auditId,
            relatedDecisionId: decision.id,
            certificateNumberSnapshot: cert.certificateId || `CERT-${cert.id.slice(-6).toUpperCase()}`,
            certificationScopeSnapshot: cert.certificationScope,
            actionById: session.user.id,
            actionReason: notes,
          },
        })
      }
    })

    revalidatePath(`/decision-maker/decisions/${auditId}`)
    revalidatePath(`/decision-maker/decisions`)
    revalidatePath(`/cb-admin/audits/${auditId}`)
    return { success: true }
  } catch (err) {
    console.error("Error committing decision:", err)
    return { error: err instanceof Error ? err.message : "Failed to make certification decision." }
  }
}
