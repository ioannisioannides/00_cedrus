"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle } from "lucide-react"
import { createComplaint } from "@/lib/actions/complaints"

const COMPLAINT_TYPES = [
  { value: "AUDIT_CONDUCT", label: "Audit Conduct" },
  { value: "AUDITOR_BEHAVIOR", label: "Auditor Behaviour" },
  { value: "CERTIFICATION_DECISION", label: "Certification Decision" },
  { value: "CERTIFICATE_MISUSE", label: "Certificate Misuse" },
  { value: "OTHER", label: "Other" },
]

type Props = { clientOrgs: { id: string; name: string }[] }

export default function NewComplaintForm({ clientOrgs }: Props) {
  const [state, formAction, pending] = useActionState(createComplaint, {})
  const router = useRouter()

  useEffect(() => {
    if (state.success) router.push("/cb-admin/complaints")
  }, [state.success, router])

  return (
    <form action={formAction} className="space-y-5 max-w-2xl">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="complainantName">Complainant Name *</Label>
          <Input id="complainantName" name="complainantName" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="complainantEmail">Email</Label>
          <Input id="complainantEmail" name="complainantEmail" type="email" className="mt-1" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="complaintType">Complaint Type *</Label>
          <Select name="complaintType" required>
            <SelectTrigger id="complaintType" className="mt-1">
              <SelectValue placeholder="Select type..." />
            </SelectTrigger>
            <SelectContent>
              {COMPLAINT_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="clientOrgId">Related Client (optional)</Label>
          <select
            id="clientOrgId"
            name="clientOrgId"
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">— None —</option>
            {clientOrgs.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <Label htmlFor="description">Description *</Label>
        <Textarea
          id="description"
          name="description"
          required
          minLength={20}
          rows={5}
          placeholder="Describe the complaint in detail..."
          className="mt-1"
        />
      </div>

      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}

      <Button type="submit" disabled={pending}>
        {pending ? "Submitting..." : "Submit Complaint"}
      </Button>
    </form>
  )
}
