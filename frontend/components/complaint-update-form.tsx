"use client"

import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

const STATUS_OPTIONS = [
  { value: "RECEIVED", label: "Received" },
  { value: "UNDER_INVESTIGATION", label: "Under Investigation" },
  { value: "ESCALATED", label: "Escalated" },
  { value: "RESOLVED", label: "Resolved" },
  { value: "CLOSED", label: "Closed" },
]

export function ComplaintUpdateForm({
  currentStatus,
  investigationNotes,
  resolutionDetails,
  correctiveActions,
  action,
}: {
  currentStatus: string
  investigationNotes: string
  resolutionDetails: string
  correctiveActions: string
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <Label htmlFor="status">Status *</Label>
        <Select name="status" defaultValue={currentStatus}>
          <SelectTrigger id="status" className="mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((s) => (
              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor="investigationNotes">Investigation Notes</Label>
        <Textarea
          id="investigationNotes"
          name="investigationNotes"
          defaultValue={investigationNotes}
          rows={3}
          className="mt-1"
        />
      </div>
      <div>
        <Label htmlFor="resolutionDetails">Resolution Details</Label>
        <Textarea
          id="resolutionDetails"
          name="resolutionDetails"
          defaultValue={resolutionDetails}
          rows={3}
          className="mt-1"
        />
      </div>
      <div>
        <Label htmlFor="correctiveActions">Corrective Actions</Label>
        <Textarea
          id="correctiveActions"
          name="correctiveActions"
          defaultValue={correctiveActions}
          rows={3}
          className="mt-1"
        />
      </div>

      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> Status updated
        </div>
      )}
      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}

      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Saving..." : "Update Status"}
      </Button>
    </form>
  )
}
