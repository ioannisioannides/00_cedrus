# Cedrus Quality & Reliability Checklist

This checklist outlines the concrete production readiness gaps identified in the audit. 

## Phase 1: Clean Baseline (TypeScript & Lint Fixes) — Immediate Priority

*   [x] **Fix CB-Admin Dashboard (Lints & Types)**
    *   Resolve nested server component declarations inside the main dashboard component ([frontend/app/(dashboard)/cb-admin/page.tsx](frontend/app/(dashboard)/cb-admin/page.tsx#L61-L76)) causing ESLint `react-hooks/static-components` failures.
    *   Await all Prisma `count()` calls ([frontend/app/(dashboard)/cb-admin/page.tsx](frontend/app/(dashboard)/cb-admin/page.tsx#L55-L73)) so they return `number` instead of unresolved `PrismaPromise<number>`.
*   [x] **Fix Client-Admin Dashboard (Types)**
    *   Await all Prisma `count()` calls ([frontend/app/(dashboard)/client-admin/page.tsx](frontend/app/(dashboard)/client-admin/page.tsx#L40-L58)) returning unresolved queries.
    *   Add null checks and scope safety on Prisma queries utilizing `clientOrgId`.
    *   Fix nested component declarations in render ([frontend/app/(dashboard)/client-admin/page.tsx](frontend/app/(dashboard)/client-admin/page.tsx#L38-L108)).
    *   Fix nested relation accessing error on finding items ([frontend/app/(dashboard)/client-admin/page.tsx](frontend/app/(dashboard)/client-admin/page.tsx#L94)).
*   [x] **Align FormAction / FormState Signatures**
    *   Align the action signature and state payload in [frontend/app/(dashboard)/cb-admin/audits/new/page.tsx](frontend/app/(dashboard)/cb-admin/audits/new/page.tsx#L73) and [frontend/app/(dashboard)/cb-admin/audits/[id]/edit/page.tsx](frontend/app/(dashboard)/cb-admin/audits/[id]/edit/page.tsx#L103) with the `FormState` expected by the [frontend/components/audit-form.tsx](frontend/components/audit-form.tsx#L33) component.
*   [x] **Fix Status Transition Button Event Handler**
    *   Ensure toast alerts pass a plain string message rather than a complex object structure ([frontend/components/status-transition-button.tsx](frontend/components/status-transition-button.tsx#L26)).

## Phase 2: Configuration & Governance Drift Alignment

*   [x] **Update Secret-Verification Workflows**
    *   Replace legacy Django-era secret references with Next/Prisma-relevant keys ([.github/workflows/verify-secrets.yml](.github/workflows/verify-secrets.yml#L11-L23)).
*   [x] **Align Dependabot Policy**
    *   Change targeted ecosystem from Python/uv to npm/Node packaging ([.github/dependabot.yml](.github/dependabot.yml#L5-L16)).
*   [x] **Upgrade Security & Documentation Policies**
    *   Publish active Next.js GRC platform vulnerability disclosure procedures ([SECURITY.md](SECURITY.md)).
    *   Document true database indexing schemes and architectural flow contracts inside [frontend/README.md](frontend/README.md).

## Phase 3: Dynamic Test Coverage Pipeline

*   [x] **Bootstrap Vitest Test Script**
    *   Add an executable `test` script block inside [frontend/package.json](frontend/package.json).
*   [x] **Introduce Baseline Tests**
    *   Develop test cases verifying authorization and role filters on server actions.
    *   Verify cross-tenant blockades of Prisma queries.
*   [x] **Integrate Test Step into CI**
    *   Include test execution step in CI pipeline workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Phase 4: Production SRE Posture & Observability

*   [x] **Add Web Container Healthcheck**
    *   Define a healthcheck block for the Next.js web service inside [docker-compose.production.yml](docker-compose.production.yml).
*   [x] **Enrich Health Endpoint**
    *   Update [frontend/app/api/health/route.ts](frontend/app/api/health/route.ts) to verify Prisma database connections as part of probe readiness.
