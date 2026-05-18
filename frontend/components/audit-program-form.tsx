"use client"

import { useActionState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type FormState = { error?: string; success?: boolean }

interface ClientOrgOption {
  id: string
  name: string
}

interface AuditProgramFormProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  clientOrgs: ClientOrgOption[]
  redirectTo?: string
  defaultValues?: {
    title?: string
    clientOrgId?: string
    year?: number
    objectives?: string
    risksOpportunities?: string
    status?: string
  }
}

const STATUS_OPTIONS = ["DRAFT", "ACTIVE", "COMPLETED", "CANCELLED"]

export function AuditProgramForm({ action, clientOrgs, redirectTo = "/cb-admin/programs", defaultValues }: AuditProgramFormProps) {
  const router = useRouter()
  const [state, formAction, isPending] = useActionState(action, {})

  useEffect(() => {
    if (state.success) router.push(redirectTo)
  }, [state.success, router, redirectTo])

  return (
    <form action={formAction} className="space-y-5">
      {state.error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {state.error}
        </div>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="clientOrgId">Client Organisation</Label>
        <select
          id="clientOrgId"
          name="clientOrgId"
          required
          defaultValue={defaultValues?.clientOrgId ?? ""}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="" disabled>Select client…</option>
          {clientOrgs.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="title">Program Title</Label>
          <Input
            id="title"
            name="title"
            required
            minLength={3}
            defaultValue={defaultValues?.title ?? ""}
            placeholder="Annual Audit Program 2026"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="year">Year</Label>
          <Input
            id="year"
            name="year"
            type="number"
            required
            min={2000}
            max={2100}
            defaultValue={defaultValues?.year ?? new Date().getFullYear()}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          name="status"
          defaultValue={defaultValues?.status ?? "DRAFT"}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="objectives">Audit Objectives</Label>
        <textarea
          id="objectives"
          name="objectives"
          required
          minLength={10}
          rows={4}
          defaultValue={defaultValues?.objectives ?? ""}
          placeholder="Describe the objectives of this audit program…"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="risksOpportunities">Risks &amp; Opportunities</Label>
        <textarea
          id="risksOpportunities"
          name="risksOpportunities"
          rows={3}
          defaultValue={defaultValues?.risksOpportunities ?? ""}
          placeholder="Identify key risks and opportunities for this program…"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <Button type="submit" disabled={isPending}>
        {isPending ? "Saving…" : "Save Program"}
      </Button>
    </form>
  )
}

// ─── Edit form (no clientOrg selector — org is fixed) ─────────────────────────

interface AuditProgramEditProps {
  action: (prev: FormState, formData: FormData) => Promise<FormState>
  program: {
    clientOrgId: string
    title: string
    year: number
    status: string
    objectives: string
    risksOpportunities: string
  }
}

export function AuditProgramEditForm({ action, program }: AuditProgramEditProps) {
  const [state, formAction, isPending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-5">
      <input type="hidden" name="clientOrgId" value={program.clientOrgId} />
      {state.error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {state.error}
        </div>
      )}
      {state.success && (
        <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
          Program saved successfully.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="title">Program Title</Label>
          <Input
            id="title"
            name="title"
            required
            minLength={3}
            defaultValue={program.title}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="year">Year</Label>
          <Input
            id="year"
            name="year"
            type="number"
            required
            min={2000}
            max={2100}
            defaultValue={program.year}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          name="status"
          defaultValue={program.status}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="objectives">Audit Objectives</Label>
        <textarea
          id="objectives"
          name="objectives"
          required
          minLength={10}
          rows={4}
          defaultValue={program.objectives}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="risksOpportunities">Risks &amp; Opportunities</Label>
        <textarea
          id="risksOpportunities"
          name="risksOpportunities"
          rows={3}
          defaultValue={program.risksOpportunities}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y"
        />
      </div>

      <Button type="submit" disabled={isPending}>
        {isPending ? "Saving…" : "Save Changes"}
      </Button>
    </form>
  )
}
