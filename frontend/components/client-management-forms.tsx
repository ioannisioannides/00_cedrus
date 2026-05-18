"use client"

import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

function FormMessage({ state }: { state: FormState }) {
  if (state.success)
    return (
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
        <CheckCircle className="h-4 w-4" /> Saved
      </div>
    )
  if (state.error)
    return (
      <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
        <AlertCircle className="h-4 w-4" /> {state.error}
      </div>
    )
  return null
}

export function AddSiteForm({
  action,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="siteName">Site Name *</Label>
          <Input id="siteName" name="siteName" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="siteEmployeeCount">Employees</Label>
          <Input id="siteEmployeeCount" name="siteEmployeeCount" type="number" min={0} className="mt-1" />
        </div>
      </div>
      <div>
        <Label htmlFor="siteAddress">Address *</Label>
        <Input id="siteAddress" name="siteAddress" required minLength={5} className="mt-1" />
      </div>
      <div>
        <Label htmlFor="siteScope">Scope</Label>
        <Textarea id="siteScope" name="siteScope" rows={2} className="mt-1" />
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Adding..." : "Add Site"}
      </Button>
    </form>
  )
}

export function AddCertificationForm({
  action,
  standards,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
  standards: { id: string; code: string; title: string }[]
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="standardId">Standard *</Label>
          <Select name="standardId" required>
            <SelectTrigger id="standardId" className="mt-1">
              <SelectValue placeholder="Select standard..." />
            </SelectTrigger>
            <SelectContent>
              {standards.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.code} — {s.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="certificateStatus">Status</Label>
          <Select name="certificateStatus" defaultValue="DRAFT">
            <SelectTrigger id="certificateStatus" className="mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["DRAFT", "ACTIVE", "SUSPENDED", "WITHDRAWN", "EXPIRED"].map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div>
        <Label htmlFor="certificationScope">Certification Scope *</Label>
        <Textarea
          id="certificationScope"
          name="certificationScope"
          required
          minLength={5}
          rows={2}
          className="mt-1"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <Label htmlFor="certificateId">Certificate Number</Label>
          <Input id="certificateId" name="certificateId" className="mt-1" />
        </div>
        <div>
          <Label htmlFor="issueDate">Issue Date</Label>
          <Input id="issueDate" name="issueDate" type="date" className="mt-1" />
        </div>
        <div>
          <Label htmlFor="expiryDate">Expiry Date</Label>
          <Input id="expiryDate" name="expiryDate" type="date" className="mt-1" />
        </div>
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Adding..." : "Add Certification"}
      </Button>
    </form>
  )
}
