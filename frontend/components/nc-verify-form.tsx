"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

export function NCVerifyForm({
  action,
  auditId,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
  auditId: string
}) {
  const [state, formAction, pending] = useActionState(action, {})
  const router = useRouter()

  useEffect(() => {
    if (state.success) router.push(`/lead-auditor/audits/${auditId}`)
  }, [state.success, auditId, router])

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <Label htmlFor="status">Verification Decision *</Label>
        <Select name="status" required>
          <SelectTrigger id="status" className="mt-1">
            <SelectValue placeholder="Select decision..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ACCEPTED">
              Accepted — response is adequate, monitoring continues
            </SelectItem>
            <SelectItem value="CLOSED">
              Closed — corrective action verified as effective
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="verificationNotes">Verification Notes</Label>
        <Textarea
          id="verificationNotes"
          name="verificationNotes"
          placeholder="Notes on the verification decision..."
          rows={4}
          className="mt-1"
        />
      </div>

      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}
      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> Verified — redirecting…
        </div>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? "Saving..." : "Submit Verification"}
        </Button>
        <Button type="button" variant="outline" onClick={() => history.back()}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
