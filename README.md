# Cedrus — GRC Platform

A Next.js 15 platform for ISO 17021 external audit management by Certification Bodies.

## Features

- Full audit lifecycle management (Draft → Scheduled → In Progress → … → Closed)
- Findings & non-conformance tracking with client response workflow
- Technical review and certification decision tracking
- Role-based access (Super Admin, CB Admin, Lead Auditor, Technical Reviewer, Decision Maker, Client Admin)
- Client organisation portal

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router, Turbopack) |
| Auth | NextAuth v5 |
| ORM | Prisma 7 + PostgreSQL 16 |
| UI | Tailwind CSS + @base-ui/react |
| Validation | Zod |
| Container | Docker + docker-compose |

## Quick Start

### Prerequisites

- Node 22+
- PostgreSQL 16 (or Docker)
- npm 10+

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your values

docker-compose up --build
# App runs on http://localhost:3000
```

### Local Development

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL to point to your local postgres

cd frontend
npm install
npx prisma migrate dev
npx tsx prisma/seed.ts     # Load demo data
npm run dev                 # Start on http://localhost:3000
```

## Project Structure

```
frontend/               ← All application code
  app/                  ← Next.js App Router pages
  components/           ← Shared UI components
  lib/
    actions/            ← Server Actions (all mutations)
    auth.ts             ← NextAuth config
    prisma.ts           ← Prisma client singleton
  prisma/
    schema.prisma       ← Data model
    seed.ts             ← Demo data
docker/                 ← Nginx + Postgres production configs
docs/                   ← Architecture and product docs
```

## Demo Credentials

After running `npx tsx prisma/seed.ts`:

| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@cedrus.example | SuperAdmin123! |
| CB Admin | cbadmin@cedrus.example | CBAdmin123! |
| Lead Auditor | auditor1@cedrus.example | Auditor123! |
| Technical Reviewer | techreviewer@cedrus.example | TechReview123! |
| Decision Maker | decisionmaker@cedrus.example | Decision123! |
| Client Admin | clientadmin@cedrus.example | ClientAdmin123! |

## Key Commands

```bash
cd frontend
npm run dev              # Start dev server (port 3000)
npm run build            # Production build
npm run lint             # ESLint
npx tsc --noEmit         # Type check
npx prisma studio        # DB browser UI
```

## Documentation

See `docs/` for:
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Product Requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Security](SECURITY.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Proprietary. All rights reserved.
