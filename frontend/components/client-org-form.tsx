"use client"

import { useActionState } from "react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"

type FormState = { error?: string; success?: boolean }

interface ClientOrgFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  defaultValues?: {
    name?: string
    customerId?: string
    registeredAddress?: string
    registeredId?: string
    totalEmployeeCount?: number
    contactEmail?: string
    contactTelephone?: string
    contactWebsite?: string
    signatoryName?: string
    signatoryTitle?: string
    msRepresentativeName?: string
    msRepresentativeTitle?: string
  }
  submitLabel?: string
}

const INITIAL_STATE: FormState = {}

export function ClientOrgForm({ action, defaultValues, submitLabel = "Save Client" }: ClientOrgFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE)

  useEffect(() => {
    if (state.success) {
      toast.success("Client organisation saved.")
      router.push("/cb-admin/clients")
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router])

  return (
    <form action={formAction} className="space-y-6">
      {/* Identity */}
      <Card>
        <CardHeader>
          <CardTitle>Organisation Identity</CardTitle>
          <CardDescription>Legal registration details</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="name">Organisation Name *</Label>
            <Input id="name" name="name" required defaultValue={defaultValues?.name} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="customerId">Customer ID *</Label>
            <Input id="customerId" name="customerId" required placeholder="e.g. ACME-001" defaultValue={defaultValues?.customerId} className="font-mono" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="registeredId">Registered Company Number</Label>
            <Input id="registeredId" name="registeredId" defaultValue={defaultValues?.registeredId} />
          </div>
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="registeredAddress">Registered Address *</Label>
            <Input id="registeredAddress" name="registeredAddress" required defaultValue={defaultValues?.registeredAddress} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="totalEmployeeCount">Total Employee Count *</Label>
            <Input id="totalEmployeeCount" name="totalEmployeeCount" type="number" min={0} required defaultValue={defaultValues?.totalEmployeeCount ?? 0} />
          </div>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Contact Details</CardTitle>
          <CardDescription>Primary contact for correspondence</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="contactEmail">Contact Email</Label>
            <Input id="contactEmail" name="contactEmail" type="email" defaultValue={defaultValues?.contactEmail} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="contactTelephone">Telephone</Label>
            <Input id="contactTelephone" name="contactTelephone" defaultValue={defaultValues?.contactTelephone} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="contactWebsite">Website</Label>
            <Input id="contactWebsite" name="contactWebsite" placeholder="https://" defaultValue={defaultValues?.contactWebsite} />
          </div>
        </CardContent>
      </Card>

      {/* Signatories */}
      <Card>
        <CardHeader>
          <CardTitle>Signatories</CardTitle>
          <CardDescription>ISO 17021 signatory and management representative</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="signatoryName">Signatory Name</Label>
            <Input id="signatoryName" name="signatoryName" defaultValue={defaultValues?.signatoryName} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="signatoryTitle">Signatory Title</Label>
            <Input id="signatoryTitle" name="signatoryTitle" defaultValue={defaultValues?.signatoryTitle} />
          </div>
          <Separator className="sm:col-span-2" />
          <div className="space-y-1">
            <Label htmlFor="msRepresentativeName">MS Representative Name</Label>
            <Input id="msRepresentativeName" name="msRepresentativeName" defaultValue={defaultValues?.msRepresentativeName} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="msRepresentativeTitle">MS Representative Title</Label>
            <Input id="msRepresentativeTitle" name="msRepresentativeTitle" defaultValue={defaultValues?.msRepresentativeTitle} />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : submitLabel}
        </Button>
      </div>
    </form>
  )
}
