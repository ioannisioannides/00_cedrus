# Pending TODO — Application Audit Opportunities

## Priority 0 — Security / Data Isolation (Do First)

- [x] Scope CB Admin audits list by organization in [frontend/app/(dashboard)/cb-admin/audits/page.tsx](frontend/app/(dashboard)/cb-admin/audits/page.tsx): add a where filter using the logged-in user's organization.
- [x] Scope CB Admin clients list by organization in [frontend/app/(dashboard)/cb-admin/clients/page.tsx](frontend/app/(dashboard)/cb-admin/clients/page.tsx): prevent cross-tenant client visibility.
- [x] Scope CB Admin programs list by organization in [frontend/app/(dashboard)/cb-admin/programs/page.tsx](frontend/app/(dashboard)/cb-admin/programs/page.tsx).
- [x] Scope CB Admin auditors list and counts by organization in [frontend/app/(dashboard)/cb-admin/auditors/page.tsx](frontend/app/(dashboard)/cb-admin/auditors/page.tsx).
- [x] Scope CB Admin complaints list by organization in [frontend/app/(dashboard)/cb-admin/complaints/page.tsx](frontend/app/(dashboard)/cb-admin/complaints/page.tsx).
- [x] Scope CB Admin dashboard counters and recent audits by organization in [frontend/app/(dashboard)/cb-admin/page.tsx](frontend/app/(dashboard)/cb-admin/page.tsx).
- [x] Scope client dropdown data in create/edit forms to organization context:
- [x] [frontend/app/(dashboard)/cb-admin/audits/new/page.tsx](frontend/app/(dashboard)/cb-admin/audits/new/page.tsx)
- [x] [frontend/app/(dashboard)/cb-admin/audits/[id]/edit/page.tsx](frontend/app/(dashboard)/cb-admin/audits/[id]/edit/page.tsx)
- [x] [frontend/app/(dashboard)/cb-admin/programs/new/page.tsx](frontend/app/(dashboard)/cb-admin/programs/new/page.tsx)
- [x] [frontend/app/(dashboard)/cb-admin/complaints/new/page.tsx](frontend/app/(dashboard)/cb-admin/complaints/new/page.tsx)
- [x] Decide and document whether Technical Reviewer and Decision Maker are global or org-scoped; enforce query scope accordingly:
- [x] Decision documented in code: both roles are org-scoped by `session.user.organizationId`.
- [x] [frontend/app/(dashboard)/technical-reviewer/page.tsx](frontend/app/(dashboard)/technical-reviewer/page.tsx)
- [x] [frontend/app/(dashboard)/decision-maker/page.tsx](frontend/app/(dashboard)/decision-maker/page.tsx)

## Priority 1 — Reliability / Correctness

- [x] Eliminate stale Prisma client confusion by adding a startup check or dev warning for missing delegates and documenting cache reset steps in [frontend/lib/prisma.ts](frontend/lib/prisma.ts).
- [x] Add a health endpoint for runtime checks and Docker health probe support (for example app route under api).
- [x] Normalize action error responses so UI can reliably map auth, validation, not-found, and conflict states (shared error constants in lib).
- [x] Review all server actions for strict object-level authorization with tenant filters (especially create/update/delete actions).

## Priority 2 — Performance

- [x] Move status count calculations from in-memory filtering to database aggregation in [frontend/app/(dashboard)/cb-admin/programs/page.tsx](frontend/app/(dashboard)/cb-admin/programs/page.tsx).
- [x] Move complaint status counts to database aggregation in [frontend/app/(dashboard)/cb-admin/complaints/page.tsx](frontend/app/(dashboard)/cb-admin/complaints/page.tsx).
- [x] Replace in-memory assigned-auditor count with database-side count in [frontend/app/(dashboard)/cb-admin/auditors/page.tsx](frontend/app/(dashboard)/cb-admin/auditors/page.tsx).
- [x] Reduce over-fetching by switching broad include usage to minimal select payloads in heavy dashboard/detail queries.
- [x] Add Suspense boundaries and independent loading skeletons for dashboards that currently block on multiple queries:
- [x] [frontend/app/(dashboard)/cb-admin/page.tsx](frontend/app/(dashboard)/cb-admin/page.tsx)
- [x] [frontend/app/(dashboard)/client-admin/page.tsx](frontend/app/(dashboard)/client-admin/page.tsx)
- [x] [frontend/app/(dashboard)/lead-auditor/page.tsx](frontend/app/(dashboard)/lead-auditor/page.tsx)
- [x] [frontend/app/(dashboard)/technical-reviewer/page.tsx](frontend/app/(dashboard)/technical-reviewer/page.tsx)
- [x] [frontend/app/(dashboard)/decision-maker/page.tsx](frontend/app/(dashboard)/decision-maker/page.tsx)

## Priority 3 — UX / Accessibility

- [x] Ensure all forms disable mutable controls during pending submission states, not only submit buttons (start with [frontend/components/audit-form.tsx](frontend/components/audit-form.tsx)).
- [x] Standardize form control primitives for consistency and accessibility (replace plain select where appropriate with shared UI primitives).
- [x] Run an accessibility pass for keyboard navigation, labels, and ARIA semantics across role dashboards and forms.

## Priority 4 — Testing / Quality Gates

- [x] Introduce a test stack (Vitest or Jest + Testing Library) and baseline tests for critical auth and tenant scoping behavior.
- [x] Add integration tests for server actions covering redirect behavior and role enforcement.
- [x] Add a regression test for the client-admin audit detail comments flow in [frontend/app/(dashboard)/client-admin/audits/[id]/page.tsx](frontend/app/(dashboard)/client-admin/audits/[id]/page.tsx).
- [x] Add CI jobs for typecheck and lint as explicit required checks if not already enforced.

## Priority 5 — Dependency / Security Hygiene

- [x] Resolve the moderate npm audit finding for qs (DoS advisory GHSA-q8mj-m7cp-5q26) in frontend dependencies.
- [x] Keep secret scanning strict and confirm only template/example values are allowlisted.
- [x] Periodically validate that local env files are not tracked and that production secrets rotate on schedule.

## Priority 6 — Maintainability

- [x] Extract duplicated status labels/badge mappings to shared constants.
- [x] Extract duplicated FormState definitions to a shared type module.
- [x] Introduce shared role guard/query helper utilities to reduce repeated auth logic and reduce drift.

## Suggested Execution Order

- [ ] Sprint A: Fix all tenant scoping issues and add tests for each fixed query path.
- [ ] Sprint B: Address performance (aggregation + Suspense) and reliability normalization.
- [ ] Sprint C: Accessibility + maintainability refactors and dependency hardening.
