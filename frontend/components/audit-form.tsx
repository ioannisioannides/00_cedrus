"use client"

import { useActionState } from "react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"

type FormState = { error?: string; success?: boolean; id?: string }

interface ClientOrg {
  id: string
  name: string
  customerId: string
}

interface Auditor {
  id: string
  name: string
}

interface AuditProgram {
  id: string
  title: string
  year: number
  clientOrgId: string
}

interface AuditFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  clientOrgs: ClientOrg[]
  auditors: Auditor[]
  programs: AuditProgram[]
  defaultClientOrgId?: string
  defaultValues?: {
    auditType?: string
    dateFrom?: string
    dateTo?: string
    leadAuditorId?: string
    programId?: string
    plannedDurationHours?: string
    durationJustification?: string
  }
}

const AUDIT_TYPES = [
  { value: "STAGE1", label: "Stage 1" },
  { value: "STAGE2", label: "Stage 2" },
  { value: "SURVEILLANCE", label: "Surveillance" },
  { value: "RECERTIFICATION", label: "Recertification" },
  { value: "TRANSFER", label: "Transfer" },
  { value: "SPECIAL", label: "Special" },
  { value: "INTERNAL", label: "Internal" },
]

const INITIAL_STATE: FormState = {}

export function AuditForm({
  action,
  clientOrgs,
  auditors,
  programs,
  defaultClientOrgId,
  defaultValues,
}: AuditFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE)

  useEffect(() => {
    if (state.success && state.id) {
      toast.success(state.id ? "Audit saved." : "Audit created.")
      router.push(`/cb-admin/audits/${state.id}`)
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router])

  return (
    <form action={formAction} className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Audit Details</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="clientOrgId">Client Organisation *</Label>
              <select
                id="clientOrgId"
                name="clientOrgId"
                defaultValue={defaultClientOrgId ?? ""}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                required
                disabled={isPending}
              >
                <option value="">Select client…</option>
                {clientOrgs.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.customerId})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="auditType">Audit Type *</Label>
              <select
                id="auditType"
                name="auditType"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                required
                defaultValue={defaultValues?.auditType ?? ""}
                disabled={isPending}
              >
                <option value="">Select type…</option>
                {AUDIT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="dateFrom">Start Date *</Label>
              <Input id="dateFrom" name="dateFrom" type="date" required defaultValue={defaultValues?.dateFrom ?? ""} disabled={isPending} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dateTo">End Date *</Label>
              <Input id="dateTo" name="dateTo" type="date" required defaultValue={defaultValues?.dateTo ?? ""} disabled={isPending} />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="leadAuditorId">Lead Auditor</Label>
              <select
                id="leadAuditorId"
                name="leadAuditorId"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                defaultValue={defaultValues?.leadAuditorId ?? ""}
                disabled={isPending}
              >
                <option value="">Assign later…</option>
                {auditors.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="programId">Audit Program</Label>
              <select
                id="programId"
                name="programId"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                defaultValue={defaultValues?.programId ?? ""}
                disabled={isPending}
              >
                <option value="">None</option>
                {programs.map((p) => (
                  <option key={p.id} value={p.id}>{p.title} ({p.year})</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="plannedDurationHours">Planned Duration (hours)</Label>
            <Input
              id="plannedDurationHours"
              name="plannedDurationHours"
              type="number"
              min="0.5"
              step="0.5"
              placeholder="e.g. 16"
              defaultValue={defaultValues?.plannedDurationHours ?? ""}
              disabled={isPending}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="durationJustification">Duration Justification</Label>
            <textarea
              id="durationJustification"
              name="durationJustification"
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
              placeholder="Basis for planned audit duration…"
              defaultValue={defaultValues?.durationJustification ?? ""}
              disabled={isPending}
            />
          </div>
        </CardContent>
      </Card>

      {state.error && (
        <p className="text-sm text-destructive">{state.error}</p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : defaultValues ? "Save Changes" : "Create Audit"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
          disabled={isPending}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
