"use server"

import { z } from "zod"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { compare, hash } from "bcryptjs"

type FormState = { error?: string; success?: boolean }

const ChangePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, "Current password is required"),
    newPassword: z.string().min(8, "New password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Please confirm your new password"),
  })
  .refine((d) => d.newPassword === d.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })

export async function changePassword(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const session = await auth()
    if (!session?.user) redirect("/login")

    const parsed = ChangePasswordSchema.safeParse({
      currentPassword: formData.get("currentPassword"),
      newPassword: formData.get("newPassword"),
      confirmPassword: formData.get("confirmPassword"),
    })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
      select: { passwordHash: true },
    })
    if (!user) return { error: "User not found." }

    const valid = await compare(parsed.data.currentPassword, user.passwordHash)
    if (!valid) return { error: "Current password is incorrect." }

    const passwordHash = await hash(parsed.data.newPassword, 12)
    await prisma.user.update({
      where: { id: session.user.id },
      data: { passwordHash },
    })

    return { success: true }
  } catch (err) {
    console.error("Error changing password:", err)
    return { error: err instanceof Error ? err.message : "Failed to change password." }
  }
}
