/* eslint-disable @typescript-eslint/no-explicit-any */
import { vi, expect, describe, it, beforeEach } from "vitest"
import { createAudit } from "./audits"
import { auth } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import { redirect } from "next/navigation"

// Mock dependencies
vi.mock("@/lib/auth", () => ({
  auth: vi.fn(),
}))

vi.mock("@/lib/prisma", () => ({
  prisma: {
    user: {
      findUnique: vi.fn(),
    },
    audit: {
      create: vi.fn(),
    },
    auditStatusLog: {
      create: vi.fn(),
    },
  },
}))

vi.mock("next/dist/client/components/redirect-error", () => ({
  isRedirectError: vi.fn((err: any) => {
    return (
      err &&
      typeof err === "object" &&
      (err.message === "NEXT_REDIRECT" ||
        (typeof err.digest === "string" && err.digest.startsWith("NEXT_REDIRECT")))
    )
  }),
}))

vi.mock("next/navigation", () => ({
  redirect: vi.fn((url) => {
    const err = new Error("NEXT_REDIRECT")
    ;(err as any).digest = `NEXT_REDIRECT;${url};307;`
    throw err
  }),
}))

vi.mock("next/cache", () => ({
  revalidatePath: vi.fn(),
}))

describe("createAudit Server Action", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should return public schema validation error when fields are invalid", async () => {
    // Authenticated user mock
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", role: "CB_ADMIN", organizationId: "cb-1" },
    } as any)

    vi.mocked(prisma.user.findUnique).mockResolvedValue({
      id: "user-1",
      role: "CB_ADMIN",
      cbOrgId: "cb-1",
    } as any)

    const formData = new FormData()
    formData.set("clientOrgId", "") // empty string triggering min(1) constraint
    
    const state = await createAudit({}, formData)
    expect(state.error).toBeDefined()
    expect(state.error).toContain("Client organisation is required")
  })

  it("should redirect to root / when unauthenticated", async () => {
    vi.mocked(auth).mockResolvedValue(null as any)

    const formData = new FormData()
    formData.set("clientOrgId", "client-1")
    formData.set("auditType", "STAGE1")
    formData.set("dateFrom", "2025-12-01")
    formData.set("dateTo", "2025-12-05")

    await expect(createAudit({}, formData)).rejects.toThrow("NEXT_REDIRECT")
    expect(redirect).toHaveBeenCalledWith("/")
  })

  it("should redirect to root / when user role is unauthorized", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", role: "CLIENT_ADMIN" },
    } as any)

    const formData = new FormData()
    formData.set("clientOrgId", "client-1")

    await expect(createAudit({}, formData)).rejects.toThrow("NEXT_REDIRECT")
    expect(redirect).toHaveBeenCalledWith("/")
  })

  it("should redirect to /login when authenticated user is not in database", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", role: "CB_ADMIN" },
    } as any)
    vi.mocked(prisma.user.findUnique).mockResolvedValue(null) // Not in DB

    const formData = new FormData()
    formData.set("clientOrgId", "client-1")

    await expect(createAudit({}, formData)).rejects.toThrow("NEXT_REDIRECT")
    expect(redirect).toHaveBeenCalledWith("/login")
  })

  it("should create audit cleanly on valid data input and return success", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", role: "CB_ADMIN", organizationId: "cb-1" },
    } as any)

    vi.mocked(prisma.user.findUnique).mockResolvedValue({
      id: "user-1",
      role: "CB_ADMIN",
      cbOrgId: "cb-1",
    } as any)

    vi.mocked(prisma.audit.create).mockResolvedValue({
      id: "audit-1234",
    } as any)

    vi.mocked(prisma.auditStatusLog.create).mockResolvedValue({
      id: "log-1",
    } as any)

    const formData = new FormData()
    formData.set("clientOrgId", "client-1")
    formData.set("auditType", "STAGE1")
    formData.set("dateFrom", "2025-12-01")
    formData.set("dateTo", "2025-12-05")
    formData.set("plannedDurationHours", "40")
    formData.set("leadAuditorId", "auditor-1")
    formData.set("durationJustification", "Large complex site structures")

    const state = await createAudit({}, formData)
    expect(state.success).toBe(true)
    expect(state.id).toBe("audit-1234")
    expect(prisma.audit.create).toHaveBeenCalled()
    expect(prisma.auditStatusLog.create).toHaveBeenCalled()
  })
})