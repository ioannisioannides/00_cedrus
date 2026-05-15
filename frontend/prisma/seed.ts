import "dotenv/config"
import { PrismaClient, Role } from "@prisma/client"
import { PrismaPg } from "@prisma/adapter-pg"
import bcrypt from "bcryptjs"

// Field renamed: Organization → CbOrg, organizationId → cbOrgId

const connectionString = process.env.DATABASE_URL
if (!connectionString) throw new Error("DATABASE_URL is not set")
const adapter = new PrismaPg({ connectionString })
const prisma = new PrismaClient({ adapter })

const DEMO_USERS: Array<{
  name: string
  email: string
  password: string
  role: Role
  orgCode: string | null
}> = [
  {
    name: "System Administrator",
    email: "superadmin@cedrus.example",
    password: "SuperAdmin123!",
    role: Role.SUPER_ADMIN,
    orgCode: null,
  },
  {
    name: "CB Administrator",
    email: "cbadmin@cedrus.example",
    password: "CBAdmin123!",
    role: Role.CB_ADMIN,
    orgCode: "CEDRUS-CB",
  },
  {
    name: "Lead Auditor",
    email: "auditor1@cedrus.example",
    password: "Auditor123!",
    role: Role.LEAD_AUDITOR,
    orgCode: "CEDRUS-CB",
  },
  {
    name: "Technical Reviewer",
    email: "techreviewer@cedrus.example",
    password: "TechReview123!",
    role: Role.TECHNICAL_REVIEWER,
    orgCode: "CEDRUS-CB",
  },
  {
    name: "Decision Maker",
    email: "decisionmaker@cedrus.example",
    password: "Decision123!",
    role: Role.DECISION_MAKER,
    orgCode: "CEDRUS-CB",
  },
  {
    name: "Client Administrator",
    email: "clientadmin@cedrus.example",
    password: "ClientAdmin123!",
    role: Role.CLIENT_ADMIN,
    orgCode: "ACME-001",
  },
]

async function main() {
  console.log("Seeding database…")

  const cb = await prisma.cbOrg.upsert({
    where: { code: "CEDRUS-CB" },
    update: {},
    create: { name: "Cedrus Certification Body", code: "CEDRUS-CB" },
  })

  const acme = await prisma.cbOrg.upsert({
    where: { code: "ACME-001" },
    update: {},
    create: { name: "Acme Corp", code: "ACME-001" },
  })

  const orgMap: Record<string, string> = {
    "CEDRUS-CB": cb.id,
    "ACME-001": acme.id,
  }

  for (const demo of DEMO_USERS) {
    const passwordHash = await bcrypt.hash(demo.password, 12)
    await prisma.user.upsert({
      where: { email: demo.email },
      update: {},
      create: {
        name: demo.name,
        email: demo.email,
        passwordHash,
        role: demo.role,
        cbOrgId: demo.orgCode ? orgMap[demo.orgCode] : null,
      },
    })
    console.log(`  ✓ ${demo.role.padEnd(20)} ${demo.email}  (${demo.password})`)
  }

  console.log("\nSeed complete.")
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(() => prisma.$disconnect())
