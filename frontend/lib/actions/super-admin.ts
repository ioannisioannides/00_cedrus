"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
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
  await requireSuperAdmin()

  const parsed = CbOrgSchema.safeParse({
    name: formData.get("name"),
    code: formData.get("code"),
  })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  try {
    await prisma.cbOrg.create({ data: { name: parsed.data.name, code: parsed.data.code } })
  } catch {
    return { error: "A CB org with that code already exists." }
  }

  revalidatePath("/super-admin/cb-orgs")
  return { success: true }
}

export async function toggleCbOrgActive(cbOrgId: string, isActive: boolean): Promise<void> {
  await requireSuperAdmin()
  await prisma.cbOrg.update({ where: { id: cbOrgId }, data: { isActive } })
  revalidatePath("/super-admin/cb-orgs")
}

// ── Standard ─────────────────────────────────────────────────────────────────

const StandardSchema = z.object({
  code: z.string().min(2, "Code is required"),
  title: z.string().min(3, "Title must be at least 3 characters"),
  naceCode: z.string().default(""),
  eaCode: z.string().default(""),
})

export async function createStandard(_prev: FormState, formData: FormData): Promise<FormState> {
  await requireSuperAdmin()

  const parsed = StandardSchema.safeParse({
    code: formData.get("code"),
    title: formData.get("title"),
    naceCode: formData.get("naceCode") || "",
    eaCode: formData.get("eaCode") || "",
  })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  try {
    await prisma.standard.create({ data: parsed.data })
  } catch {
    return { error: "A standard with that code already exists." }
  }

  revalidatePath("/super-admin/standards")
  return { success: true }
}

export async function deleteStandard(standardId: string): Promise<void> {
  await requireSuperAdmin()
  await prisma.standard.delete({ where: { id: standardId } })
  revalidatePath("/super-admin/standards")
}

// ── User ─────────────────────────────────────────────────────────────────────

const CreateUserSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.nativeEnum(Role),
  cbOrgId: z.string().optional(),
})

export async function createUser(_prev: FormState, formData: FormData): Promise<FormState> {
  await requireSuperAdmin()

  const parsed = CreateUserSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
    role: formData.get("role"),
    cbOrgId: formData.get("cbOrgId") || undefined,
  })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const passwordHash = await hash(parsed.data.password, 12)

  try {
    await prisma.user.create({
      data: {
        name: parsed.data.name,
        email: parsed.data.email,
        passwordHash,
        role: parsed.data.role,
        cbOrgId: parsed.data.cbOrgId ?? null,
      },
    })
  } catch {
    return { error: "A user with that email already exists." }
  }

  revalidatePath("/super-admin/users")
  return { success: true }
}

export async function toggleUserActive(userId: string, isActive: boolean): Promise<void> {
  await requireSuperAdmin()
  await prisma.user.update({ where: { id: userId }, data: { isActive } })
  revalidatePath("/super-admin/users")
}
