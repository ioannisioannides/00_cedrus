"use client"

import { useActionState } from "react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

type FormState = { error?: string; success?: boolean }

interface DecisionFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  clientName: string
}

const DECISION_OPTIONS = [
  { value: "GRANT", label: "Grant — issue certification" },
  { value: "REFUSE", label: "Refuse — do not issue certification" },
  { value: "SUSPEND", label: "Suspend — temporarily halt certification" },
  { value: "WITHDRAW", label: "Withdraw — revoke existing certification" },
  { value: "SPECIAL_AUDIT", label: "Special Audit — require additional audit" },
]

const INITIAL_STATE: FormState = {}

export function DecisionForm({ action, clientName }: DecisionFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE)

  useEffect(() => {
    if (state.success) {
      toast.success("Certification decision recorded.")
      router.push("/decision-maker/decisions")
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router])

  return (
    <form action={formAction} className="space-y-5">
      <div className="space-y-1.5">
        <Label htmlFor="decision">Decision for {clientName} *</Label>
        <select
          id="decision"
          name="decision"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          required
        >
          <option value="">Select decision…</option>
          {DECISION_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="decisionNotes">Decision Notes * <span className="text-muted-foreground font-normal">(min 20 chars)</span></Label>
        <textarea
          id="decisionNotes"
          name="decisionNotes"
          rows={6}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
          placeholder="Provide justification for the certification decision…"
          required
        />
      </div>

      {state.error && (
        <p className="text-sm text-destructive">{state.error}</p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Recording…" : "Record Decision"}
        </Button>
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
