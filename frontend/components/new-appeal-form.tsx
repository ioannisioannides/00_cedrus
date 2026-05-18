"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { AlertCircle } from "lucide-react"
import { createAppeal } from "@/lib/actions/appeals"

type Complaint = { id: string; complaintNumber: string; complainantName: string }
type Decision = { id: string; auditId: string; audit: { clientOrg: { name: string } } }

export default function NewAppealForm({
  complaints,
  decisions,
}: {
  complaints: Complaint[]
  decisions: Decision[]
}) {
  const [state, formAction, pending] = useActionState(createAppeal, {})
  const router = useRouter()

  useEffect(() => {
    if (state.success) router.push("/cb-admin/appeals")
  }, [state.success, router])

  return (
    <form action={formAction} className="space-y-5 max-w-2xl">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="appellantName">Appellant Name *</Label>
          <Input id="appellantName" name="appellantName" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="appellantEmail">Email</Label>
          <Input id="appellantEmail" name="appellantEmail" type="email" className="mt-1" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="relatedComplaintId">Related Complaint (optional)</Label>
          <select
            id="relatedComplaintId"
            name="relatedComplaintId"
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">— None —</option>
            {complaints.map((c) => (
              <option key={c.id} value={c.id}>
                {c.complaintNumber} — {c.complainantName}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="relatedDecisionId">Related Decision (optional)</Label>
          <select
            id="relatedDecisionId"
            name="relatedDecisionId"
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">— None —</option>
            {decisions.map((d) => (
              <option key={d.id} value={d.id}>
                Decision — {d.audit.clientOrg.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <Label htmlFor="grounds">Grounds for Appeal *</Label>
        <Textarea
          id="grounds"
          name="grounds"
          required
          minLength={20}
          rows={5}
          placeholder="Describe the grounds for this appeal in detail..."
          className="mt-1"
        />
      </div>

      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}

      <Button type="submit" disabled={pending}>
        {pending ? "Submitting..." : "Submit Appeal"}
      </Button>
    </form>
  )
}
