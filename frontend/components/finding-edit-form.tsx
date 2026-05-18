"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

type Finding = {
  findingType: string
  clause: string
  objectiveEvidence?: string | null
  statementOfNc?: string | null
  auditorExplanation?: string | null
  dueDate?: Date | null
  observationStatement?: string | null
  observationExplanation?: string | null
  ofiDescription?: string | null
}

export function FindingEditForm({
  finding,
  action,
  auditId,
}: {
  finding: Finding
  action: (prev: FormState, fd: FormData) => Promise<FormState>
  auditId: string
}) {
  const [state, formAction, pending] = useActionState(action, {})
  const router = useRouter()

  useEffect(() => {
    if (state.success) router.push(`/lead-auditor/audits/${auditId}`)
  }, [state.success, auditId, router])

  const isNC = finding.findingType === "NC_MAJOR" || finding.findingType === "NC_MINOR"
  const isObservation = finding.findingType === "OBSERVATION"
  const isOFI = finding.findingType === "OFI"

  const formatDate = (d: Date | null | undefined) =>
    d ? new Date(d).toISOString().split("T")[0] : ""

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <Label htmlFor="clause">Clause Reference *</Label>
        <Input
          id="clause"
          name="clause"
          defaultValue={finding.clause}
          placeholder="e.g. 9.2.1"
          required
          className="mt-1"
        />
      </div>

      {isNC && (
        <>
          <div>
            <Label htmlFor="objectiveEvidence">Objective Evidence *</Label>
            <Textarea
              id="objectiveEvidence"
              name="objectiveEvidence"
              defaultValue={finding.objectiveEvidence ?? ""}
              rows={4}
              required
              minLength={10}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="statementOfNc">Statement of Nonconformity *</Label>
            <Textarea
              id="statementOfNc"
              name="statementOfNc"
              defaultValue={finding.statementOfNc ?? ""}
              rows={4}
              required
              minLength={10}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="auditorExplanation">Auditor Explanation</Label>
            <Textarea
              id="auditorExplanation"
              name="auditorExplanation"
              defaultValue={finding.auditorExplanation ?? ""}
              rows={3}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="dueDate">Response Due Date</Label>
            <Input
              id="dueDate"
              name="dueDate"
              type="date"
              defaultValue={formatDate(finding.dueDate)}
              className="mt-1"
            />
          </div>
        </>
      )}

      {isObservation && (
        <>
          <div>
            <Label htmlFor="observationStatement">Observation Statement *</Label>
            <Textarea
              id="observationStatement"
              name="observationStatement"
              defaultValue={finding.observationStatement ?? ""}
              rows={4}
              required
              minLength={10}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="observationExplanation">Explanation</Label>
            <Textarea
              id="observationExplanation"
              name="observationExplanation"
              defaultValue={finding.observationExplanation ?? ""}
              rows={3}
              className="mt-1"
            />
          </div>
        </>
      )}

      {isOFI && (
        <div>
          <Label htmlFor="ofiDescription">Description *</Label>
          <Textarea
            id="ofiDescription"
            name="ofiDescription"
            defaultValue={finding.ofiDescription ?? ""}
            rows={4}
            required
            minLength={10}
            className="mt-1"
          />
        </div>
      )}

      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}
      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> Saved — redirecting…
        </div>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? "Saving..." : "Save Changes"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => history.back()}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
