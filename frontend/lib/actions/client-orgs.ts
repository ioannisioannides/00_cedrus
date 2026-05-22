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
  try {
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
  } catch (err) {
    console.error("Error creating client organisation:", err)
    return { error: err instanceof Error ? err.message : "Failed to create client organisation due to an unexpected error." }
  }
}

export async function updateClientOrg(
  id: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
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
    revalidatePath("/super-admin")
    return { success: true }
  } catch (err) {
    console.error("Error updating client organisation:", err)
    return { error: err instanceof Error ? err.message : "Failed to update client organisation." }
  }
}

export async function deleteClientOrg(id: string): Promise<FormState> {
  try {
    await requireCbAdmin()

    const hasAudits = await prisma.audit.findFirst({ where: { clientOrgId: id } })
    if (hasAudits) {
      return { error: "Cannot delete a client organisation that has associated audits." }
    }

    await prisma.clientOrg.delete({ where: { id } })
    revalidatePath("/cb-admin/clients")
    return { success: true }
  } catch (err) {
    console.error("Error deleting client organisation:", err)
    return { error: err instanceof Error ? err.message : "Failed to delete client organisation due to an unexpected error." }
  }
}

// ─── Sites ────────────────────────────────────────────────────────────────────

const SiteSchema = z.object({
  siteName: z.string().min(2, "Site name is required"),
  siteAddress: z.string().min(5, "Site address is required"),
  siteEmployeeCount: z.coerce.number().int().min(0).optional(),
  siteScope: z.string().default(""),
})

export async function addSite(
  clientOrgId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const parsed = SiteSchema.safeParse({
      siteName: formData.get("siteName"),
      siteAddress: formData.get("siteAddress"),
      siteEmployeeCount: formData.get("siteEmployeeCount") || undefined,
      siteScope: formData.get("siteScope") || "",
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    await prisma.site.create({ data: { clientOrgId, ...parsed.data } })
    revalidatePath(`/cb-admin/clients/${clientOrgId}`)
    return { success: true }
  } catch (err) {
    console.error("Error adding site:", err)
    return { error: err instanceof Error ? err.message : "Failed to add site due to an unexpected error." }
  }
}

export async function deleteSite(siteId: string): Promise<void> {
  try {
    const session = await auth()
    if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) return

    const site = await prisma.site.findUnique({ where: { id: siteId } })
    if (!site) return

    await prisma.site.delete({ where: { id: siteId } })
    revalidatePath(`/cb-admin/clients/${site.clientOrgId}`)
  } catch (err) {
    console.error("Error deleting site:", err)
  }
}

// ─── Certifications ───────────────────────────────────────────────────────────

const CertificationSchema = z.object({
  standardId: z.string().min(1, "Standard is required"),
  certificationScope: z.string().min(5, "Certification scope is required"),
  certificateId: z.string().default(""),
  certificateStatus: z.enum(["DRAFT", "ACTIVE", "SUSPENDED", "WITHDRAWN", "EXPIRED"]).default("DRAFT"),
  issueDate: z.string().optional(),
  expiryDate: z.string().optional(),
})

export async function addCertification(
  clientOrgId: string,
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    await requireCbAdmin()

    const parsed = CertificationSchema.safeParse({
      standardId: formData.get("standardId"),
      certificationScope: formData.get("certificationScope"),
      certificateId: formData.get("certificateId") || "",
      certificateStatus: formData.get("certificateStatus") || "DRAFT",
      issueDate: formData.get("issueDate") || undefined,
      expiryDate: formData.get("expiryDate") || undefined,
    })

    if (!parsed.success) return { error: parsed.error.issues[0].message }

    await prisma.certification.create({
      data: {
        clientOrgId,
        standardId: parsed.data.standardId,
        certificationScope: parsed.data.certificationScope,
        certificateId: parsed.data.certificateId,
        certificateStatus: parsed.data.certificateStatus,
        issueDate: parsed.data.issueDate ? new Date(parsed.data.issueDate) : null,
        expiryDate: parsed.data.expiryDate ? new Date(parsed.data.expiryDate) : null,
      },
    })

    revalidatePath(`/cb-admin/clients/${clientOrgId}`)
    return { success: true }
  } catch (err) {
    console.error("Error adding certification:", err)
    return { error: "A certification for this standard already exists or could not be created." }
  }
}

export async function updateCertificationStatus(
  certId: string,
  status: string
): Promise<void> {
  try {
    const session = await auth()
    if (!session?.user || !["SUPER_ADMIN", "CB_ADMIN"].includes(session.user.role)) return

    const cert = await prisma.certification.findUnique({ where: { id: certId } })
    if (!cert) return

    await prisma.certification.update({
      where: { id: certId },
      data: { certificateStatus: status as "DRAFT" | "ACTIVE" | "SUSPENDED" | "WITHDRAWN" | "EXPIRED" },
    })
    revalidatePath(`/cb-admin/clients/${cert.clientOrgId}`)
  } catch (err) {
    console.error("Error updating certification status:", err)
  }
}

