import { auth } from "@/lib/auth"
import { redirect, notFound } from "next/navigation"
import { prisma } from "@/lib/prisma"
import { ClientOrgForm } from "@/components/client-org-form"
import { updateClientOrg } from "@/lib/actions/client-orgs"

interface Props {
  params: Promise<{ id: string }>
}

export default async function EditClientPage({ params }: Props) {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  const { id } = await params
  const client = await prisma.clientOrg.findUnique({ where: { id } })
  if (!client) notFound()

  const action = updateClientOrg.bind(null, id)

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Edit Client</h1>
        <p className="text-muted-foreground">{client.name} · {client.customerId}</p>
      </div>
      <ClientOrgForm
        action={action}
        defaultValues={{
          name: client.name,
          customerId: client.customerId,
          registeredAddress: client.registeredAddress,
          registeredId: client.registeredId,
          totalEmployeeCount: client.totalEmployeeCount,
          contactEmail: client.contactEmail,
          contactTelephone: client.contactTelephone,
          contactWebsite: client.contactWebsite,
          signatoryName: client.signatoryName,
          signatoryTitle: client.signatoryTitle,
          msRepresentativeName: client.msRepresentativeName,
          msRepresentativeTitle: client.msRepresentativeTitle,
        }}
        submitLabel="Update Client"
      />
    </div>
  )
}
