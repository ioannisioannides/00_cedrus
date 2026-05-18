"use client"

import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

export function AddCompetenceWarningForm({
  action,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-3 max-w-xl">
      <div>
        <Label htmlFor="description">Description *</Label>
        <Textarea
          id="description"
          name="description"
          required
          minLength={10}
          rows={3}
          placeholder="Describe the competence concern..."
          className="mt-1"
        />
      </div>

      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> Warning recorded
        </div>
      )}
      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}

      <Button type="submit" disabled={pending} size="sm" variant="destructive">
        {pending ? "Adding..." : "Add Warning"}
      </Button>
    </form>
  )
}
