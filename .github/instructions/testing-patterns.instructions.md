---
applyTo: "frontend/**/*.test.ts,frontend/**/*.test.tsx,frontend/**/*.spec.ts,frontend/**/*.spec.tsx"
---

# Testing Patterns — Cedrus (Next.js)

## Test Stack

- **Unit/integration**: Vitest + React Testing Library (add when needed)
- **E2E**: Playwright (add when needed)
- **Type checking**: `npx tsc --noEmit` (required before every commit)
- **Lint**: `npm run lint` (required before every commit)

## Server Action Testing Pattern

Server actions are plain async functions — test them by mocking Prisma:

```ts
import { vi, expect, describe, it } from "vitest"
import { createAudit } from "@/lib/actions/audits"

vi.mock("@/lib/prisma", () => ({
  prisma: {
    audit: {
      create: vi.fn().mockResolvedValue({ id: "test-id" }),
    },
  },
}))

vi.mock("@/lib/auth", () => ({
  auth: vi.fn().mockResolvedValue({
    user: { id: "u1", role: "CB_ADMIN", organizationId: "org1" },
  }),
}))

describe("createAudit", () => {
  it("returns error when schema validation fails", async () => {
    const formData = new FormData()
    formData.set("auditType", "") // missing required field
    const result = await createAudit({}, formData)
    expect(result.error).toBeDefined()
  })
})
```

## What to Test

1. **Server action validation** — invalid input returns `{ error: "..." }`
2. **Auth checks** — unauthenticated calls redirect to `/login`
3. **Object-level access** — user cannot access another org's resources
4. **Status transitions** — valid/invalid state machine transitions
5. **Enum display** — `formatEnum` converts correctly

## Type Check Command

```bash
cd frontend && npx tsc --noEmit
```

This must pass before any PR. It catches type errors across the entire codebase including Prisma generated types.
