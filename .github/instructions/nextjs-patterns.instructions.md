---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx"
---

# Next.js 15 Patterns — Cedrus

## Architecture

```
app/(dashboard)/[role]/     → Server component pages (auth-gated)
components/                 → Shared client/server UI components
lib/actions/               → Server Actions (ALL mutations)
lib/auth.ts                → NextAuth config
lib/prisma.ts              → Prisma singleton
lib/utils.ts               → cn(), formatEnum()
prisma/schema.prisma       → Source of truth for data model
```

## Server Component Page

```tsx
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"

export default async function Page() {
  const session = await auth()
  if (!session?.user || session.user.role !== "CB_ADMIN") redirect("/")

  const data = await prisma.audit.findMany({
    where: { cbOrg: { id: session.user.organizationId } },
    select: { id: true, auditType: true, status: true },
  })
  return <AuditList audits={data} />
}
```

## Server Action

```ts
"use server"
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { z } from "zod"
import { revalidatePath } from "next/cache"

type FormState = { error?: string; success?: boolean }

const Schema = z.object({ name: z.string().min(1) })

export async function doSomething(
  _prev: FormState,
  formData: FormData
): Promise<FormState> {
  const session = await auth()
  if (!session?.user) redirect("/login")

  const parsed = Schema.safeParse({ name: formData.get("name") })
  if (!parsed.success) return { error: parsed.error.issues[0].message }

  await prisma.someModel.create({ data: parsed.data })
  revalidatePath("/path")
  return { success: true }
}
```

## Client Form Component

```tsx
"use client"
import { useActionState } from "react"
import { useEffect } from "react"
import { toast } from "sonner"

export function SomeForm({ action }) {
  const [state, formAction, pending] = useActionState(action, {})

  useEffect(() => {
    if (state.success) toast.success("Done.")
    else if (state.error) toast.error(state.error)
  }, [state])

  return (
    <form action={formAction}>
      <Button type="submit" disabled={pending}>
        {pending ? "Saving..." : "Save"}
      </Button>
    </form>
  )
}
```

## Key Conventions

- `session.user.organizationId` = cbOrgId (CB roles)
- `session.user.clientOrgId` = clientOrgId (CLIENT_ADMIN)
- `@base-ui/react` Button with link: `<Button render={<Link href="/foo" />}>Label</Button>`
- Enum display: `formatEnum("SOME_VALUE")` → `"Some Value"` (import from `@/lib/utils`)
- Date display: `format(date, "dd MMM yyyy")` (import from `date-fns`)
- Toasts: `toast.success()` / `toast.error()` (import from `sonner`)

## Security Checklist (every page/action)

- [ ] Check `session.user.role` and redirect if unauthorised
- [ ] Scope Prisma queries to the user's org (`cbOrgId` or `clientOrgId`)
- [ ] Validate all formData with Zod before touching the DB
- [ ] Use `prisma.model.findUnique({ where: { id, orgId } })` — never trust id alone
