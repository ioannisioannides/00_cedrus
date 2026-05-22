"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { isRedirectError } from "next/dist/client/components/redirect-error"
import { Role } from "@prisma/client"
import { hash } from "bcryptjs"

type FormState = { error?: string; success?: boolean }

async function requireSuperAdmin() {
  const session = await auth()
  if (!session?.user || session.user.role !== "SUPER_ADMIN") redirect("/")
  return session.user
}

// ── CbOrg ───────────────────────────────────────────────────────────────────

const CbOrgSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  code: z.string().min(2, "Code must be at least 2 characters").toUpperCase(),
})

export async function createCbOrg(_prev: FormState, formData: FormData): Promise<FormState> {
  try {
    await requireSuperAdmin()

    const parsed = CbOrgSchema.safeParse({
      name: formData.get("name"),
      code: formData.get("code"),
    })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    await prisma.cbOrg.create({ data: { name: parsed.data.name, code: parsed.data.code } })

    revalidatePath("/super-admin/cb-orgs")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error creating CB Org:", err)
    return { error: err instanceof Error ? err.message : "Failed to create CB Organisation." }
  }
}

export async function toggleCbOrgActive(cbOrgId: string, isActive: boolean): Promise<void> {
  try {
    await requireSuperAdmin()
    await prisma.cbOrg.update({ where: { id: cbOrgId }, data: { isActive } })
    revalidatePath("/super-admin/cb-orgs")
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error toggling CB Org:", err)
  }
}

// ── Standard ─────────────────────────────────────────────────────────────────

const StandardSchema = z.object({
  code: z.string().min(2, "Code is required"),
  title: z.string().min(3, "Title must be at least 3 characters"),
  naceCode: z.string().default(""),
  eaCode: z.string().default(""),
})

export async function createStandard(_prev: FormState, formData: FormData): Promise<FormState> {
  try {
    await requireSuperAdmin()

    const parsed = StandardSchema.safeParse({
      code: formData.get("code"),
      title: formData.get("title"),
      naceCode: formData.get("naceCode") || "",
      eaCode: formData.get("eaCode") || "",
    })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    await prisma.standard.create({ data: parsed.data })

    revalidatePath("/super-admin/standards")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error creating Standard:", err)
    return { error: err instanceof Error ? err.message : "Failed to create Standard." }
  }
}

export async function deleteStandard(standardId: string): Promise<void> {
  try {
    await requireSuperAdmin()
    await prisma.standard.delete({ where: { id: standardId } })
    revalidatePath("/super-admin/standards")
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error deleting Standard:", err)
  }
}

// ── User ─────────────────────────────────────────────────────────────────────

const CreateUserSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.nativeEnum(Role),
  cbOrgId: z.string().optional(),
  clientOrgId: z.string().optional(),
})

export async function createUser(_prev: FormState, formData: FormData): Promise<FormState> {
  try {
    await requireSuperAdmin()

    const parsed = CreateUserSchema.safeParse({
      name: formData.get("name"),
      email: formData.get("email"),
      password: formData.get("password"),
      role: formData.get("role"),
      cbOrgId: formData.get("cbOrgId") || undefined,
      clientOrgId: formData.get("clientOrgId") || undefined,
    })
    if (!parsed.success) return { error: parsed.error.issues[0].message }

    const passwordHash = await hash(parsed.data.password, 12)

    await prisma.user.create({
      data: {
        name: parsed.data.name,
        email: parsed.data.email,
        passwordHash,
        role: parsed.data.role,
        cbOrgId: parsed.data.role === "CLIENT_ADMIN" ? null : (parsed.data.cbOrgId ?? null),
        clientOrgId: parsed.data.role === "CLIENT_ADMIN" ? (parsed.data.clientOrgId ?? null) : null,
      },
    })

    revalidatePath("/super-admin/users")
    return { success: true }
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error creating user:", err)
    return { error: err instanceof Error ? err.message : "Failed to create user." }
  }
}

export async function toggleUserActive(userId: string, isActive: boolean): Promise<void> {
  try {
    await requireSuperAdmin()
    await prisma.user.update({ where: { id: userId }, data: { isActive } })
    revalidatePath("/super-admin/users")
  } catch (err) {
    if (isRedirectError(err)) throw err;
    console.error("Error toggling user active:", err)
  }
}