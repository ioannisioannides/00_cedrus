"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { hash } from "bcryptjs"
import { Role } from "@prisma/client"

type FormState = { error?: string; success?: boolean }

const CB_ROLES: Role[] = ["CB_ADMIN", "LEAD_AUDITOR", "TECHNICAL_REVIEWER", "DECISION_MAKER"]

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

const CreateCbUserSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["CB_ADMIN", "LEAD_AUDITOR", "TECHNICAL_REVIEWER", "DECISION_MAKER"]),
})

export async function createCbUser(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const actor = await requireCbAdmin()

    const parsed = CreateCbUserSchema.safeParse({
      name: formData.get("name"),
      email: formData.get("email"),
      password: formData.get("password"),
      role: formData.get("role"),
    })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const passwordHash = await hash(parsed.data.password, 12)

    await prisma.user.create({
      data: {
        name: parsed.data.name,
        email: parsed.data.email,
        passwordHash,
        role: parsed.data.role,
        cbOrgId: actor.organizationId,
      },
    })

    revalidatePath("/cb-admin/users")
    return { success: true }
  } catch (err) {
    console.error("Error creating CB user:", err)
    return { error: err instanceof Error ? err.message : "Failed to create user." }
  }
}

export async function toggleCbUserActive(userId: string, isActive: boolean): Promise<void> {
  try {
    const actor = await requireCbAdmin()

    // Ensure the target user belongs to the same CB org
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { cbOrgId: true, role: true },
    })

    if (!user) return
    if (
      user.cbOrgId !== actor.organizationId &&
      actor.role !== "SUPER_ADMIN"
    ) {
      return
    }
    if (!CB_ROLES.includes(user.role)) return

    await prisma.user.update({ where: { id: userId }, data: { isActive } })
    revalidatePath("/cb-admin/users")
  } catch (err) {
    console.error("Error toggling CB user active:", err)
  }
}
