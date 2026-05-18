"use server"

import { z } from "zod"
import { revalidatePath } from "next/cache"
import { prisma } from "@/lib/prisma"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

const ClientOrgSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  customerId: z.string().min(2, "Customer ID is required"),
  registeredAddress: z.string().min(5, "Registered address is required"),
  registeredId: z.string().optional().default(""),
  totalEmployeeCount: z.coerce.number().int().min(0, "Employee count must be 0 or more"),
  contactEmail: z.string().email("Invalid email").optional().or(z.literal("")).default(""),
  contactTelephone: z.string().optional().default(""),
  contactFax: z.string().optional().default(""),
  contactWebsite: z.string().optional().default(""),
  signatoryName: z.string().optional().default(""),
  signatoryTitle: z.string().optional().default(""),
  msRepresentativeName: z.string().optional().default(""),
  msRepresentativeTitle: z.string().optional().default(""),
})

type FormState = { error?: string; success?: boolean }

async function requireCbAdmin() {
  const session = await auth()
  if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }
  return session.user
}

export async function createClientOrg(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireCbAdmin()

  const parsed = ClientOrgSchema.safeParse({
    name: formData.get("name"),
    customerId: formData.get("customerId"),
    registeredAddress: formData.get("registeredAddress"),
    registeredId: formData.get("registeredId") || "",
    totalEmployeeCount: formData.get("totalEmployeeCount") || 0,
    contactEmail: formData.get("contactEmail") || "",
    contactTelephone: formData.get("contactTelephone") || "",
    contactFax: formData.get("contactFax") || "",
    contactWebsite: formData.get("contactWebsite") || "",
    signatoryName: formData.get("signatoryName") || "",
    signatoryTitle: formData.get("signatoryTitle") || "",
    msRepresentativeName: formData.get("msRepresentativeName") || "",
    msRepresentativeTitle: formData.get("msRepresentativeTitle") || "",
  })

  if (!parsed.success) {
    return { error: parsed.error.issues[0].message }
  }

  const existing = await prisma.clientOrg.findUnique({ where: { customerId: parsed.data.customerId } })
  if (existing) return { error: "A client organisation with this Customer ID already exists." }

  await prisma.clientOrg.create({ data: parsed.data })
  revalidatePath("/cb-admin/clients")
  revalidatePath("/super-admin")
  return { success: true }
}

export async function updateClientOrg(
  id: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  await requireCbAdmin()

  const parsed = ClientOrgSchema.safeParse({
    name: formData.get("name"),
    customerId: formData.get("customerId"),
    registeredAddress: formData.get("registeredAddress"),
    registeredId: formData.get("registeredId") || "",
    totalEmployeeCount: formData.get("totalEmployeeCount") || 0,
    contactEmail: formData.get("contactEmail") || "",
    contactTelephone: formData.get("contactTelephone") || "",
    contactFax: formData.get("contactFax") || "",
    contactWebsite: formData.get("contactWebsite") || "",
    signatoryName: formData.get("signatoryName") || "",
    signatoryTitle: formData.get("signatoryTitle") || "",
    msRepresentativeName: formData.get("msRepresentativeName") || "",
    msRepresentativeTitle: formData.get("msRepresentativeTitle") || "",
  })

  if (!parsed.success) return { error: parsed.error.issues[0].message }

  const conflict = await prisma.clientOrg.findFirst({
    where: { customerId: parsed.data.customerId, NOT: { id } },
  })
  if (conflict) return { error: "Another client organisation already uses this Customer ID." }

  await prisma.clientOrg.update({ where: { id }, data: parsed.data })
  revalidatePath("/cb-admin/clients")
  revalidatePath(`/cb-admin/clients/${id}`)
  return { success: true }
}

export async function deleteClientOrg(id: string): Promise<FormState> {
  await requireCbAdmin()

  const hasAudits = await prisma.audit.findFirst({ where: { clientOrgId: id } })
  if (hasAudits) {
    return { error: "Cannot delete a client organisation that has associated audits." }
  }

  await prisma.clientOrg.delete({ where: { id } })
  revalidatePath("/cb-admin/clients")
  return { success: true }
}
