# CLAUDE.md — Cedrus

> Quick-start guide for AI coding agents (Claude, Copilot, etc.)

---

## What Is This?

**Cedrus** is a Next.js 15 GRC platform for ISO 17021 external audit management.
It serves Certification Bodies (CBs) managing the full audit lifecycle: planning,
execution, findings, NC responses, technical review, and certification decisions.

**All application code lives in `frontend/`.**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router, Turbopack) |
| Auth | NextAuth v5 (JWT, `auth.config.ts` + `lib/auth.ts`) |
| ORM | Prisma 7 + `@prisma/adapter-pg` + PostgreSQL |
| UI | Tailwind CSS + `@base-ui/react` |
| Validation | Zod |
| Toasts | sonner |
| Icons | lucide-react |
| Dates | date-fns |
| Passwords | bcryptjs |

---

## Key Commands

```bash
cd frontend

npm run dev                          # Start dev server on :3000 (Turbopack)
npm run build                        # Production build
npm run lint                         # ESLint
npx tsc --noEmit                     # Type-check entire codebase
npx prisma studio                    # Open DB browser
npx prisma migrate dev --name <n>    # Create + apply migration
npx tsx prisma/seed.ts               # Seed demo data
```

---

## File Layout

```
frontend/
  app/
    (auth)/login/             → Login page
    (dashboard)/
      layout.tsx              → Sidebar + header shell
      cb-admin/               → CB Admin pages
      lead-auditor/           → Lead Auditor pages
      technical-reviewer/     → Technical Reviewer pages
      decision-maker/         → Decision Maker pages
      client-admin/           → Client Admin pages
      super-admin/            → Super Admin pages
      profile/                → Password change page (all roles)
  components/
    ui/                       → Primitive components (button, card, table…)
    app-sidebar.tsx           → Navigation sidebar
    site-header.tsx           → Top header with user dropdown
    status-transition-button.tsx → Audit status transitions
    audit-form.tsx            → Create/edit audit form
    [feature]-form.tsx        → Feature-specific forms
  lib/
    auth.ts                   → NextAuth config (authorize, JWT, session)
    prisma.ts                 → Prisma client singleton
    utils.ts                  → cn(), formatEnum()
    actions/
      audits.ts               → createAudit, updateAudit, transitionAudit
      findings.ts             → createFinding, updateFinding, deleteFinding
      nc-responses.ts         → submitNCResponse
      decisions.ts            → makeDecision
      complaints.ts           → createComplaint, updateComplaint
      appeals.ts              → createAppeal, updateAppeal
      profile.ts              → changePassword
      users.ts                → createCbUser, toggleCbUserActive
      super-admin.ts          → createUser (super admin)
      [feature].ts            → Other actions
  prisma/
    schema.prisma             → Canonical data model
    seed.ts                   → Demo data seeder
    migrations/               → Migration history
```

---

## User Roles

| Role | Enum | Access |
|------|------|--------|
| Super Admin | `SUPER_ADMIN` | All organisations, user management |
| CB Admin | `CB_ADMIN` | Own CB org — audits, clients, users |
| Lead Auditor | `LEAD_AUDITOR` | Assigned audits — findings, team, docs |
| Technical Reviewer | `TECHNICAL_REVIEWER` | Technical review step |
| Decision Maker | `DECISION_MAKER` | Certification decisions |
| Client Admin | `CLIENT_ADMIN` | Own client org — audits view, NC responses |

Session fields:
- `session.user.organizationId` → `cbOrgId` (all CB roles)
- `session.user.clientOrgId` → clientOrgId (CLIENT_ADMIN only)

---

## Audit Lifecycle (ISO 17021)

```
DRAFT → SCHEDULED → IN_PROGRESS → CLIENT_RESPONSE → CB_REVIEW → DECISION_PENDING → CLOSED
                                                                              ↘ CANCELLED
```

---

## Coding Rules

1. **Read before write** — read existing file before editing
2. **Auth first** — every server action calls `auth()` at the top
3. **Scope queries** — always filter by `cbOrgId` or `clientOrgId`
4. **Zod at boundaries** — validate all `formData` before touching the DB
5. **Return errors** — actions return `{ error: "..." }` — never throw
6. **`npx tsc --noEmit`** — must pass before committing
7. **No raw SQL** — use the Prisma ORM only

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@cedrus.example | SuperAdmin123! |
| CB Admin | cbadmin@cedrus.example | CBAdmin123! |
| Lead Auditor | auditor1@cedrus.example | Auditor123! |
| Technical Reviewer | techreviewer@cedrus.example | TechReview123! |
| Decision Maker | decisionmaker@cedrus.example | Decision123! |
| Client Admin | clientadmin@cedrus.example | ClientAdmin123! |

---

## Common Pitfalls

- **Prisma client stale after schema change**: run `npx prisma generate`
- **Migration drift**: run `npx prisma migrate reset --force` then `npx prisma migrate dev`
- **`output: 'standalone'`**: required in `next.config.ts` for Docker to work
- **Turbopack + Prisma**: `serverExternalPackages` must include `@prisma/client`, `@prisma/adapter-pg`, `pg`
- **`session.user.clientOrgId`** is `null` for CB roles — check before using
