"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createFinding } from "@/lib/actions/findings"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"

type FormState = { error?: string; success?: boolean; id?: string }

interface Props {
  auditId: string
  sites: { id: string; name: string }[]
  standards: { id: string; code: string; title: string }[]
}

const FINDING_TYPES = [
  { value: "NC_MAJOR", label: "Major Nonconformity" },
  { value: "NC_MINOR", label: "Minor Nonconformity" },
  { value: "OBSERVATION", label: "Observation" },
  { value: "OFI", label: "Opportunity for Improvement (OFI)" },
]

const INITIAL_STATE: FormState = {}

export function NewFindingForm({ auditId, sites, standards }: Props) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(createFinding, INITIAL_STATE)

  useEffect(() => {
    if (state.success) {
      toast.success("Finding recorded.")
      router.push(`/lead-auditor/audits/${auditId}`)
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router, auditId])

  return (
    <form action={formAction} className="space-y-6">
      <input type="hidden" name="auditId" value={auditId} />

      <Card>
        <CardHeader><CardTitle>Finding Details</CardTitle></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {/* Type */}
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="findingType">Finding Type *</Label>
            <select
              id="findingType"
              name="findingType"
              required
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Select type…</option>
              {FINDING_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* Clause */}
          <div className="space-y-1">
            <Label htmlFor="clause">Clause Reference *</Label>
            <Input id="clause" name="clause" required placeholder="e.g. 6.1.2" className="font-mono" />
          </div>

          {/* Standard */}
          {standards.length > 0 && (
            <div className="space-y-1">
              <Label htmlFor="standardId">Standard</Label>
              <select
                id="standardId"
                name="standardId"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">— Not specified —</option>
                {standards.map((s) => (
                  <option key={s.id} value={s.id}>{s.code} — {s.title}</option>
                ))}
              </select>
            </div>
          )}

          {/* Site */}
          {sites.length > 0 && (
            <div className="space-y-1">
              <Label htmlFor="siteId">Site</Label>
              <select
                id="siteId"
                name="siteId"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">— All sites —</option>
                {sites.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* NC fields */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Nonconformity Details</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <div className="space-y-1">
            <Label htmlFor="objectiveEvidence">Objective Evidence</Label>
            <textarea
              id="objectiveEvidence"
              name="objectiveEvidence"
              rows={3}
              placeholder="Evidence observed during the audit…"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="statementOfNc">Statement of Nonconformity</Label>
            <textarea
              id="statementOfNc"
              name="statementOfNc"
              rows={3}
              placeholder="The organisation has failed to…"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="auditorExplanation">Auditor Explanation (optional)</Label>
            <textarea
              id="auditorExplanation"
              name="auditorExplanation"
              rows={2}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="dueDate">Response Due Date</Label>
            <Input id="dueDate" name="dueDate" type="date" />
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Observation / OFI fields */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Observation / OFI Details</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <div className="space-y-1">
            <Label htmlFor="observationStatement">Observation Statement</Label>
            <textarea
              id="observationStatement"
              name="observationStatement"
              rows={3}
              placeholder="The auditor observed that…"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="ofiDescription">OFI Description</Label>
            <textarea
              id="ofiDescription"
              name="ofiDescription"
              rows={3}
              placeholder="An opportunity exists to improve…"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : "Record Finding"}
        </Button>
      </div>
    </form>
  )
}
