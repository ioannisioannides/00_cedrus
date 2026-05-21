# Contributing to Cedrus

## Prerequisites

- Node 22+
- npm 10+
- PostgreSQL 16 (or Docker)
- Git

## Local Setup

```bash
git clone <repo>
cd cedrus

# Set up environment
cp frontend/.env.example frontend/.env
# Edit frontend/.env with your local DATABASE_URL and AUTH_SECRET

# Install dependencies
cd frontend
npm install

# Set up database
npx prisma migrate dev
npx tsx prisma/seed.ts    # Load demo data

# Start dev server
npm run dev               # http://localhost:3000
```

## Development Workflow

1. Create a branch: `git checkout -b feat/your-feature`
2. Make your changes in `frontend/`
3. **Before committing**, run:
   ```bash
   cd frontend
   npx tsc --noEmit      # Must pass
   npm run lint           # Must pass
   npm run build          # Recommended
   ```
4. Push and open a PR

## Code Standards

All application code is in `frontend/`. See [CLAUDE.md](CLAUDE.md) for the full AI agent guide and conventions.

### Key Rules

- **Server actions** for all mutations — in `frontend/lib/actions/`
- **Server components** for pages — auth check at top
- **Zod validation** for all form inputs at action boundaries
- **Auth scope** — every Prisma query scoped to user's org
- **No raw SQL** — Prisma ORM only
- **No `console.log`** — use `console.error` for caught errors only

### Tech Stack

- Next.js 15 (App Router, Turbopack)
- NextAuth v5
- Prisma 7 + PostgreSQL 16
- Tailwind CSS + @base-ui/react
- Zod + sonner + lucide-react

## Schema Changes

```bash
cd frontend

# After editing prisma/schema.prisma
npx prisma migrate dev --name describe-your-change
npx prisma generate
```

## Testing

Currently: type checking + linting as quality gates.

```bash
npx tsc --noEmit
npm run lint
```

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add evidence file upload
fix: scope audit queries to cbOrgId
chore: update dependencies
docs: update CLAUDE.md
```
