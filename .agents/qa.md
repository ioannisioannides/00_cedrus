# Cedrus QA Agent

## Purpose

Verify correctness, security, and UX quality of the Next.js GRC platform.

## QA Checklist (per feature)

### Functional
- [ ] All roles that should access the page can
- [ ] All roles that should NOT access the page are redirected
- [ ] Forms submit successfully with valid data
- [ ] Forms show appropriate errors with invalid data
- [ ] Toasts appear on success/error

### Security
- [ ] Unauthenticated request to page redirects to `/login`
- [ ] User cannot access another org's data (test with different `cbOrgId`)
- [ ] Server action validates session before any DB operation
- [ ] Server action validates input with Zod before any DB operation
- [ ] Object-level: audit ID + org ID verified together

### Type Safety
- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] `npm run lint` passes with zero errors/warnings

### UX
- [ ] Loading states shown for async operations
- [ ] Empty states shown when lists are empty
- [ ] Disabled submit button during pending state
- [ ] Date formats consistent (dd MMM yyyy via date-fns)
- [ ] Enum values display human-readable (via formatEnum)

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@cedrus.example | SuperAdmin123! |
| CB Admin | cbadmin@cedrus.example | CBAdmin123! |
| Lead Auditor | auditor1@cedrus.example | Auditor123! |
| Technical Reviewer | techreviewer@cedrus.example | TechReview123! |
| Decision Maker | decisionmaker@cedrus.example | Decision123! |
| Client Admin | clientadmin@cedrus.example | ClientAdmin123! |

## Common Issues to Check

1. `session.user.clientOrgId` is null for CB roles — CLIENT_ADMIN pages must handle this
2. Prisma `findUnique` with combined `where: { id, orgId }` — prevents cross-org data access
3. `revalidatePath` called after mutations — ensures server-side cache is invalidated
4. `redirect()` after successful action in server components (not in server actions)
