"use client"

import { useActionState } from "react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

type FormState = { error?: string; success?: boolean }

interface TechnicalReviewFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  existing?: {
    scopeVerified: boolean
    objectivesVerified: boolean
    findingsReviewed: boolean
    conclusionClear: boolean
    reviewerNotes: string
    clarificationRequested: string
    status: string
  } | null
}

const INITIAL_STATE: FormState = {}

export function TechnicalReviewForm({ action, existing }: TechnicalReviewFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE)

  useEffect(() => {
    if (state.success) {
      toast.success("Technical review submitted.")
      router.push("/technical-reviewer/reviews")
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router])

  return (
    <form action={formAction} className="space-y-6">
      <div className="space-y-4">
        <p className="text-sm font-medium">Review Checklist</p>

        {[
          { name: "scopeVerified", label: "Audit scope is correctly defined and documented" },
          { name: "objectivesVerified", label: "Audit objectives have been met" },
          { name: "findingsReviewed", label: "Findings are complete, evidence-based and correctly classified" },
          { name: "conclusionClear", label: "Audit conclusion and recommendation are clear and justified" },
        ].map((item) => (
          <div key={item.name} className="flex items-start gap-3">
            <input
              type="checkbox"
              id={item.name}
              name={item.name}
              defaultChecked={existing ? Boolean((existing as Record<string, unknown>)[item.name]) : false}
              className="mt-0.5 h-4 w-4 rounded border-input"
            />
            <Label htmlFor={item.name} className="cursor-pointer font-normal">
              {item.label}
            </Label>
          </div>
        ))}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="reviewerNotes">Review Notes *</Label>
        <textarea
          id="reviewerNotes"
          name="reviewerNotes"
          rows={5}
          defaultValue={existing?.reviewerNotes ?? ""}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
          placeholder="Summarise your technical review findings…"
          required
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="clarificationRequested">Clarification Required (if any)</Label>
        <textarea
          id="clarificationRequested"
          name="clarificationRequested"
          rows={3}
          defaultValue={existing?.clarificationRequested ?? ""}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
          placeholder="Describe any points requiring clarification from the lead auditor…"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="decision">Decision *</Label>
        <select
          id="decision"
          name="decision"
          defaultValue={existing?.status ?? ""}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          required
        >
          <option value="">Select outcome…</option>
          <option value="APPROVED">Approve — forward to Decision Maker</option>
          <option value="REQUIRES_CLARIFICATION">Request Clarification — return to Submitted</option>
          <option value="REJECTED">Reject — report has significant issues</option>
        </select>
      </div>

      {state.error && (
        <p className="text-sm text-destructive">{state.error}</p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Submitting…" : "Submit Review"}
        </Button>
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
