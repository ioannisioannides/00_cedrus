# Cedrus Next.js Frontend — ISO 17021 GRC Platform

This is the main web application and server container workspace for **Cedrus**, a modern Governance, Risk, and Compliance (GRC) platform. It provides Certification Bodies (CBs) and Auditees with a robust, type-safe, multi-tenant workspace to manage the full ISO 17021 external audit management lifecycle.

## Technical Stack

- **Framework:** Next.js 15 (App Router, Turbopack enabled)
- **Runtime:** React 19 / Node.js
- **Database ORM:** Prisma 7 + PostgreSQL (`@prisma/adapter-pg`)
- **Authentication:** NextAuth v5 (Supporting multi-role token/session pipelines)
- **UI & Layout:** Tailwind CSS & Lucide Icons
- **Component Primitives:** `@base-ui/react` (Zero-styled, accessible React components)
- **State Validation:** Zod
- **Date Management:** date-fns

---

## Architectural Flow Contracts

To safeguard multi-tenant operations, the application operates under a strict, non-negotiable layered security and validation pattern.

### 1. Multi-Tenant Query Scoping
The database is shared across multiple external Certification Body (CB) organizations and audited Client organizations. To prevent any cross-tenant data leakage, every page and transaction query **MUST** be explicitly scoped to the active tenant in the database query.
- When an action or page is requested by a User of a Certification Body (role `CB_ADMIN`, `LEAD_AUDITOR`, etc.), all query parameters are scoped using `session.user.organizationId` (mapped to `cbOrgId`).
- When an action or page is requested by an Auditee (role `CLIENT_ADMIN`), all query parameters are scoped using `session.user.clientOrgId` (mapped to `clientOrgId`).

### 2. Validation & Flow Boundaries
- **Server Actions:** All server actions defined inside [lib/actions/](lib/actions/) call the NextAuth `auth()` session validation first. If no session exists, they redirect to the login page immediately.
- **Client Forms:** Forms execute using React 19's `useActionState` and `useTransition` hooks, collecting errors and displaying them using plain-text `FormState` return strings and the `sonner` toast system.

---

## Database Indexing Scheme

To maintain fast transaction and lookup response times in multi-tenant production deployments, the PostgreSQL database is indexed for critical query joins. The primary indices defined in [prisma/schema.prisma](prisma/schema.prisma) include:

### 1. Audit Table Indices
- **Multi-Tenant Status Join Index:** Crucial for rendering dashboard statistics filter queries.
  ```prisma
  @@index([clientOrgId, status])
  ```
- **Filter Status Lookup Index:** Speeds up table pagination filters.
  ```prisma
  @@index([status])
  ```
- **Auditor Assignment Index:** Optimizes performance when loading assigned audits for individual lead auditors.
  ```prisma
  @@index([leadAuditorId])
  ```

### 2. Certification History Table Indices
- **History Action Index:** Speeds up audit trail reports and compliance timeline checks.
  ```prisma
  @@index([action])
  ```
- **Action Date Index:** Optimizes sorting of chronological change logs.
  ```prisma
  @@index([actionDate])
  ```

---

## Workspace Structure

The application layout is highly modularized around architectural layups:

```
app/                        - Pages, route layouts, and Next.js router files
  (auth)/                   - Authentication route pipeline (e.g., login, register)
  (dashboard)/              - Dashboard shells grouped by user role directories
    cb-admin/               - Certification Body administration pages
    client-admin/           - Client Auditee pages
    lead-auditor/           - Assigned lead auditor workflow pages
components/                 - Shared UI components (audit forms, sidebar drawers)
lib/                        - Core helper libraries and system initialization
  actions/                  - Standard next-js Server Actions mutating state safely
  auth.ts                   - NextAuth authorization rules and session payload hooks
  prisma.ts                 - Primary singleton instance of the database adapter
  utils.ts                  - Common presentation utilities (such as formatEnum)
prisma/                     - Prisma schema definitions and initialization seeds
```

---

## Developer Workflows

### Setup and Running Locally

1. Install package dependencies:
   ```bash
   npm install
   ```

2. Generate Prisma Client database schemas:
   ```bash
   npx prisma generate
   ```

3. Spin up the development server:
   ```bash
   npm run dev
   ```

4. Perform static verification checks before committing any changes:
   ```bash
   # Typecheck entire workspace
   npx tsc --noEmit

   # Lint checking (ESlint)
   npm run lint
   ```
