import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { ClientOrgForm } from "@/components/client-org-form"
import { createClientOrg } from "@/lib/actions/client-orgs"

export const metadata = { title: "New Client — Cedrus" }

export default async function NewClientPage() {
  const session = await auth()
  if (!session?.user || !["CB_ADMIN", "SUPER_ADMIN"].includes(session.user.role)) {
    redirect("/")
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Client Organisation</h1>
        <p className="text-muted-foreground">
          Register a new client to be certified under ISO 17021.
        </p>
      </div>
      <ClientOrgForm action={createClientOrg} submitLabel="Create Client" />
    </div>
  )
}
