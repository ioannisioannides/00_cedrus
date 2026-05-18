"use client"

import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { CheckCircle, AlertCircle } from "lucide-react"
import { createCbOrg, createStandard } from "@/lib/actions/super-admin"

type FormState = { error?: string; success?: boolean }

export function CreateCbOrgForm() {
  const [state, formAction, pending] = useActionState(createCbOrg, {})
  return (
    <form action={formAction} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="name">Organisation Name *</Label>
          <Input id="name" name="name" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="code">Code *</Label>
          <Input id="code" name="code" required minLength={2} className="mt-1" placeholder="e.g. ACME-CB" />
        </div>
      </div>
      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> CB org created
        </div>
      )}
      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}
      <Button type="submit" disabled={pending} size="sm">{pending ? "Creating..." : "Create Organisation"}</Button>
    </form>
  )
}

export function CreateStandardForm() {
  const [state, formAction, pending] = useActionState(createStandard, {} as FormState)
  return (
    <form action={formAction} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="std-code">Standard Code *</Label>
          <Input id="std-code" name="code" required placeholder="e.g. ISO 9001:2015" className="mt-1" />
        </div>
        <div>
          <Label htmlFor="std-title">Title *</Label>
          <Input id="std-title" name="title" required minLength={3} className="mt-1" placeholder="Quality management systems" />
        </div>
        <div>
          <Label htmlFor="naceCode">NACE Code</Label>
          <Input id="naceCode" name="naceCode" className="mt-1" />
        </div>
        <div>
          <Label htmlFor="eaCode">EA Code</Label>
          <Input id="eaCode" name="eaCode" className="mt-1" />
        </div>
      </div>
      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> Standard created
        </div>
      )}
      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}
      <Button type="submit" disabled={pending} size="sm">{pending ? "Creating..." : "Create Standard"}</Button>
    </form>
  )
}

