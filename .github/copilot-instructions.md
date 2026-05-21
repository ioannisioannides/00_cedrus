# GitHub Copilot Instructions for Cedrus

> Karpathy-Inspired AI Coding Guidelines — Next.js GRC Platform

---

## Project

**Cedrus** is a Next.js 15 GRC (Governance, Risk, Compliance) platform for ISO 17021 external audit management by Certification Bodies.

**Stack:** TypeScript · Next.js 15 (App Router, Turbopack) · NextAuth v5 · Prisma 7 + PostgreSQL · Tailwind CSS · @base-ui/react · sonner · bcryptjs · zod · date-fns · lucide-react

---

## Core Principles (Karpathy-Inspired)

1. **Read before write** — understand existing code before changing it
2. **Small changes** — make the minimum change that solves the problem
3. **No clever code** — boring, obvious code beats clever code
4. **Verify everything** — run `npx tsc --noEmit` and `npm run lint` after every change
5. **Fail loudly** — validate at boundaries, never silently ignore errors
6. **One thing per function** — if you need "and" in a description, split the function
7. **Make impossible states impossible** — use Zod schemas, TypeScript types, Prisma constraints

---

## Architecture Layers

```
app/(dashboard)/[role]/     → Page components (server components by default)
components/                 → Shared UI components
lib/actions/               → Server Actions (all mutation logic lives here)
lib/auth.ts                → NextAuth config (JWT, session, authorize)
lib/prisma.ts              → Prisma client singleton
lib/utils.ts               → Shared utilities (cn, formatEnum)
prisma/schema.prisma       → Single source of truth for data model
```

### Page Pattern (Server Component)
```tsx
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"

export default async function SomePage() {
  const session = await auth()
  if (!session?.user || session.user.role !== "CB_ADMIN") redirect("/")

  const data = await prisma.someModel.findMany({ where: { ... } })
  return <SomeClientComponent data={data} />
}
```

### Server Action Pattern
```ts
"use server"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { z } from "zod"
import { revalidatePath } from "next/cache"

const Schema = z.object({ name: z.string().min(1) })

export async function doSomething(_prev: FormState, formData: FormData) {
  const session = await auth()
  if (!session?.user) redirect("/login")

  const parsed = Schema.safeParse({ name: formData.get("name") })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  await prisma.someModel.create({ data: parsed.data })
  revalidatePath("/some-path")
  return { success: true }
}
```

### Client Component Pattern
```tsx
"use client"
import { useActionState } from "react"
import { useEffect } from "react"
import { toast } from "sonner"

export function SomeForm({ action }: { action: (prev: FormState, fd: FormData) => Promise<FormState> }) {
  const [state, formAction, pending] = useActionState(action, {})

  useEffect(() => {
    if (state.success) toast.success("Done.")
    else if (state.error) toast.error(state.error)
  }, [state])

  return <form action={formAction}>...</form>
}
```

---

## Security Rules (Non-Negotiable)

- Every page: check `session.user.role` and `redirect("/")` if unauthorized
- Every action: call `auth()` first — `redirect("/login")` if no session
- Object-level: scope Prisma queries to the user's org (`cbOrgId` or `clientOrgId`)
- No secrets in code — environment variables only
- Never `JSON.parse` user input without validation
- Use Zod for all form input validation at action boundaries

---

## Key Conventions

- **`session.user.organizationId`** = cbOrgId (for CB roles)
- **`session.user.clientOrgId`** = clientOrgId (for CLIENT_ADMIN)
- **`@base-ui/react` Button with link**: `<Button render={<Link href="/foo" />}>Label</Button>`
- **Toast**: `import { toast } from "sonner"` — `toast.success()` / `toast.error()`
- **Enum display**: `import { formatEnum } from "@/lib/utils"` — converts `SOME_ENUM` → `"Some Enum"`
- **Date display**: `import { format } from "date-fns"` — `format(date, "dd MMM yyyy")`

---

## What NOT To Do

- Don't add features not in scope
- Don't refactor working code unless asked
- Don't add docstrings/comments to unchanged code
- Don't use `console.log` — use `console.error` only for caught errors in actions
- Don't write raw SQL — use the Prisma ORM
- Don't store secrets in code
- Don't catch and silently ignore errors — return `{ error: "..." }` from actions
- Don't ship code without running `npx tsc --noEmit`

---

## Key Commands

```bash
cd frontend

npm run dev                          # Dev server (Turbopack, port 3000)
npm run build                        # Production build
npm run lint                         # ESLint
npx tsc --noEmit                     # Type check
npx prisma studio                    # DB browser UI
npx prisma migrate dev --name <name> # Create + apply migration
npx tsx prisma/seed.ts               # Seed demo data
```

## Demo Credentials (after seed)

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@cedrus.example | SuperAdmin123! |
| CB Admin | cbadmin@cedrus.example | CBAdmin123! |
| Lead Auditor | auditor1@cedrus.example | Auditor123! |
| Technical Reviewer | techreviewer@cedrus.example | TechReview123! |
| Decision Maker | decisionmaker@cedrus.example | Decision123! |
| Client Admin | clientadmin@cedrus.example | ClientAdmin123! |
