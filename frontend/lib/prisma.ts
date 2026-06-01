import { PrismaPg } from "@prisma/adapter-pg"
import { PrismaClient } from "@prisma/client"
import { env } from "./env"

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

function createPrismaClient() {
  const adapter = new PrismaPg({ connectionString: env.DATABASE_URL })
  return new PrismaClient({ adapter })
}

export const prisma = globalForPrisma.prisma ?? createPrismaClient()


if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma
  // --- Prisma Client Staleness Check ---
  // If you add a new model to schema.prisma and forget to run `npx prisma generate`,
  // the corresponding delegate (e.g., prisma.audit) will be undefined.
  // This check warns you in development if a delegate is missing.
  if (typeof prisma.audit === "undefined") {
    console.warn(
      "\u26A0\uFE0F Prisma client is missing the 'audit' delegate.\n" +
      "This usually means you changed schema.prisma but did NOT run `npx prisma generate` or restart the dev server.\n" +
      "\nTo fix: Run `npx prisma generate` and restart the dev server.\n" +
      "If the problem persists, clear .next/cache and node_modules/.prisma.\n"
    )
  }
}
