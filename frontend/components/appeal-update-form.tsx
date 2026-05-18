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
  { value: "PANEL_REVIEW", label: "Panel Review" },
  { value: "DECIDED", label: "Decided" },
  { value: "CLOSED", label: "Closed" },
]

const DECISION_OPTIONS = [
  { value: "", label: "— No decision yet —" },
  { value: "UPHELD", label: "Upheld" },
  { value: "REJECTED", label: "Rejected" },
  { value: "PARTIALLY_UPHELD", label: "Partially Upheld" },
]

export function AppealUpdateForm({
  currentStatus,
  currentDecision,
  panelJustification,
  action,
}: {
  currentStatus: string
  currentDecision: string | null
  panelJustification: string
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
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
          <Label htmlFor="panelDecision">Panel Decision</Label>
          <Select name="panelDecision" defaultValue={currentDecision ?? ""}>
            <SelectTrigger id="panelDecision" className="mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DECISION_OPTIONS.map((d) => (
                <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="panelJustification">Panel Justification</Label>
        <Textarea
          id="panelJustification"
          name="panelJustification"
          defaultValue={panelJustification}
          rows={4}
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
        {pending ? "Saving..." : "Update Appeal"}
      </Button>
    </form>
  )
}
