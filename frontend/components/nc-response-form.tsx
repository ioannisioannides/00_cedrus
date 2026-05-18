"use client"

import { useActionState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

type FormState = { error?: string; success?: boolean }

interface NCResponseFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  defaultValues?: {
    clientRootCause?: string
    clientCorrection?: string
    clientCorrectiveAction?: string
  }
}

export function NCResponseForm({ action, defaultValues }: NCResponseFormProps) {
  const [state, formAction, isPending] = useActionState(action, {})

  useEffect(() => {
    if (state.success) {
      // Refresh the page to show updated status
      window.location.reload()
    }
  }, [state.success])

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {state.error}
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="clientRootCause">Root Cause Analysis</Label>
        <textarea
          id="clientRootCause"
          name="clientRootCause"
          required
          minLength={10}
          rows={3}
          defaultValue={defaultValues?.clientRootCause ?? ""}
          placeholder="Describe the root cause of this non-conformity…"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="clientCorrection">Immediate Correction</Label>
        <textarea
          id="clientCorrection"
          name="clientCorrection"
          required
          minLength={5}
          rows={2}
          defaultValue={defaultValues?.clientCorrection ?? ""}
          placeholder="What immediate action was taken to correct the finding…"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="clientCorrectiveAction">Corrective Action Plan</Label>
        <textarea
          id="clientCorrectiveAction"
          name="clientCorrectiveAction"
          required
          minLength={20}
          rows={3}
          defaultValue={defaultValues?.clientCorrectiveAction ?? ""}
          placeholder="Describe the corrective action plan to prevent recurrence…"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <Button type="submit" disabled={isPending}>
        {isPending ? "Submitting…" : "Submit Response"}
      </Button>
    </form>
  )
}
