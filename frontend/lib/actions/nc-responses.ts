"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"

const NCResponseSchema = z.object({
  clientRootCause: z.string().min(10, "Root cause must be at least 10 characters"),
  clientCorrection: z.string().min(5, "Correction must be at least 5 characters"),
  clientCorrectiveAction: z.string().min(20, "Corrective action must be at least 20 characters"),
})

type FormState = { error?: string; success?: boolean }

export async function submitNCResponse(
  findingId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user || session.user.role !== "CLIENT_ADMIN") {
    return { error: "Unauthorised" }
  }

  const finding = await prisma.finding.findUnique({
    where: { id: findingId },
    select: { id: true, verificationStatus: true, findingType: true, auditId: true },
  })

  if (!finding) return { error: "Finding not found" }
  if (!["NC_MAJOR", "NC_MINOR"].includes(finding.findingType)) {
    return { error: "Only non-conformities can have a client response" }
  }
  if (!["OPEN", "CLIENT_RESPONDED"].includes(finding.verificationStatus)) {
    return { error: "This finding is already closed" }
  }

  const parsed = NCResponseSchema.safeParse({
    clientRootCause: formData.get("clientRootCause"),
    clientCorrection: formData.get("clientCorrection"),
    clientCorrectiveAction: formData.get("clientCorrectiveAction"),
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  await prisma.finding.update({
    where: { id: findingId },
    data: {
      clientRootCause: parsed.data.clientRootCause,
      clientCorrection: parsed.data.clientCorrection,
      clientCorrectiveAction: parsed.data.clientCorrectiveAction,
      verificationStatus: "CLIENT_RESPONDED",
    },
  })

  revalidatePath(`/client-admin/audits/${finding.auditId}`)
  return { success: true }
}
