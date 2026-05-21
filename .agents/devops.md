# Cedrus DevOps Agent

## Purpose

Manage infrastructure, CI/CD, Docker, and deployments.

## Stack

Next.js 15 · Node 22 (Alpine) · PostgreSQL 16 · Redis 7 · Docker · GitHub Actions

## Key Files

- `frontend/Dockerfile` — multi-stage node:22-alpine build (requires `output: 'standalone'` in next.config.ts)
- `docker-compose.yml` — dev: postgres + redis + Next.js web on :3000
- `docker-compose.staging.yml` — staging environment
- `docker-compose.production.yml` — production (pull image from GHCR)
- `.github/workflows/ci.yml` — npm ci → prisma generate → tsc → lint → build → npm audit
- `docker/nginx/` — reverse proxy config
- `docker/postgres/` — postgres backup + prod config

## Docker Workflow

```bash
# Dev (builds from source)
docker-compose up --build

# Production (pull pre-built image)
IMAGE_TAG=latest docker-compose -f docker-compose.production.yml up -d
```

## Required ENV (docker-compose)

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `DATABASE_URL` | Full Prisma connection string (postgres host = service name) |
| `AUTH_SECRET` | NextAuth secret (min 32 chars, `openssl rand -base64 32`) |
| `NEXTAUTH_URL` | Public URL of the app |
| `REDIS_PASSWORD` | Redis auth (production only) |

## Post-Deploy Steps

```bash
# Run migrations (inside web container)
docker exec cedrus-web-prod npx prisma migrate deploy

# Seed (first deploy only)
docker exec cedrus-web-prod npx tsx prisma/seed.ts
```

## Mandate

- Zero-downtime deployments
- Keep secrets in environment variables — never in images
- Security headers enforced by `next.config.ts` (CSP, HSTS, X-Frame-Options)
- Run `npm audit --audit-level=high` in CI — fail on high/critical vulns
