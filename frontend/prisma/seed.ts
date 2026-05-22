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
  clientOrgCode: string | null
}> = [
  {
    name: "System Administrator",
    email: "superadmin@cedrus.example",
    password: "SuperAdmin123!",
    role: Role.SUPER_ADMIN,
    orgCode: null,
    clientOrgCode: null,
  },
  {
    name: "CB Administrator",
    email: "cbadmin@cedrus.example",
    password: "CBAdmin123!",
    role: Role.CB_ADMIN,
    orgCode: "CEDRUS-CB",
    clientOrgCode: null,
  },
  {
    name: "Lead Auditor",
    email: "auditor1@cedrus.example",
    password: "Auditor123!",
    role: Role.LEAD_AUDITOR,
    orgCode: "CEDRUS-CB",
    clientOrgCode: null,
  },
  {
    name: "Technical Reviewer",
    email: "techreviewer@cedrus.example",
    password: "TechReview123!",
    role: Role.TECHNICAL_REVIEWER,
    orgCode: "CEDRUS-CB",
    clientOrgCode: null,
  },
  {
    name: "Decision Maker",
    email: "decisionmaker@cedrus.example",
    password: "Decision123!",
    role: Role.DECISION_MAKER,
    orgCode: "CEDRUS-CB",
    clientOrgCode: null,
  },
  {
    name: "Client Administrator",
    email: "clientadmin@cedrus.example",
    password: "ClientAdmin123!",
    role: Role.CLIENT_ADMIN,
    orgCode: null,
    clientOrgCode: "ACME-IND",
  },
]

async function main() {
  console.log("Seeding database…")

  const cb = await prisma.cbOrg.upsert({
    where: { code: "CEDRUS-CB" },
    update: {},
    create: { name: "Cedrus Certification Body", code: "CEDRUS-CB" },
  })

  const orgMap: Record<string, string> = {
    "CEDRUS-CB": cb.id,
  }

  const acmeClientOrg = await prisma.clientOrg.upsert({
    where: { customerId: "ACME-IND-001" },
    update: {},
    create: {
      name: "Acme Industries Ltd",
      customerId: "ACME-IND-001",
      registeredAddress: "123 Industrial Way, London, UK",
      totalEmployeeCount: 250,
    },
  })

  const clientOrgMap: Record<string, string> = {
    "ACME-IND": acmeClientOrg.id,
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
        clientOrgId: demo.clientOrgCode ? clientOrgMap[demo.clientOrgCode] : null,
      },
    })
    console.log(`  ✓ ${demo.role.padEnd(20)} ${demo.email} seeded.`)
  }

  console.log("\nSeed complete.")
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(() => prisma.$disconnect())
