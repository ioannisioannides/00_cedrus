"use client"

import { useActionState, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

// ─── Toggle field component ────────────────────────────────────────────────────

function YesNoField({
  name,
  label,
  defaultValue,
}: {
  name: string
  label: string
  defaultValue: boolean
}) {
  const [value, setValue] = useState(defaultValue)
  return (
    <div className="flex items-center gap-3">
      <input type="hidden" name={name} value={value ? "true" : "false"} />
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => setValue(!value)}
        className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${
          value ? "bg-primary" : "bg-input"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
            value ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </button>
      <Label className="text-sm">{label}</Label>
    </div>
  )
}

function FormMessage({ state }: { state: FormState }) {
  if (state.success)
    return (
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
        <CheckCircle className="h-4 w-4" /> Saved successfully
      </div>
    )
  if (state.error)
    return (
      <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
        <AlertCircle className="h-4 w-4" /> {state.error}
      </div>
    )
  return null
}

// ─── Audit Changes Form ────────────────────────────────────────────────────────

type AuditChangesData = {
  changeOfName: boolean
  changeOfScope: boolean
  changeOfSites: boolean
  changeOfMsRep: boolean
  changeOfSignatory: boolean
  changeOfEmployeeCount: boolean
  changeOfContactInfo: boolean
  otherHasChange: boolean
  otherDescription: string
} | null

export function AuditChangesForm({
  auditId,
  data,
  action,
}: {
  auditId: string
  data: AuditChangesData
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  const CHANGE_FIELDS: [string, string][] = [
    ["changeOfName", "Change of organisation name"],
    ["changeOfScope", "Change of scope"],
    ["changeOfSites", "Change of sites"],
    ["changeOfMsRep", "Change of management system representative"],
    ["changeOfSignatory", "Change of authorised signatory"],
    ["changeOfEmployeeCount", "Change of employee count"],
    ["changeOfContactInfo", "Change of contact information"],
    ["otherHasChange", "Other changes"],
  ]

  return (
    <form action={formAction} className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {CHANGE_FIELDS.map(([name, label]) => (
          <YesNoField
            key={name}
            name={name}
            label={label}
            defaultValue={data ? (data as Record<string, unknown>)[name] === true : false}
          />
        ))}
      </div>
      <div>
        <Label htmlFor="otherDescription">Other changes description</Label>
        <Textarea
          id="otherDescription"
          name="otherDescription"
          placeholder="Describe any other changes..."
          defaultValue={data?.otherDescription ?? ""}
          rows={3}
          className="mt-1"
        />
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Saving..." : "Save Changes"}
      </Button>
    </form>
  )
}

// ─── Plan Review Form ──────────────────────────────────────────────────────────

type PlanReviewData = {
  deviationsYesNo: boolean
  deviationsDetails: string
  issuesAffectingYesNo: boolean
  issuesAffectingDetails: string
  nextAuditDateFrom: Date | null
  nextAuditDateTo: Date | null
} | null

export function AuditPlanReviewForm({
  data,
  action,
}: {
  data: PlanReviewData
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  const formatDate = (d: Date | null) =>
    d ? new Date(d).toISOString().split("T")[0] : ""

  return (
    <form action={formAction} className="space-y-4">
      <YesNoField
        name="deviationsYesNo"
        label="Were there deviations from the audit plan?"
        defaultValue={data?.deviationsYesNo ?? false}
      />
      <div>
        <Label htmlFor="deviationsDetails">Deviation details</Label>
        <Textarea
          id="deviationsDetails"
          name="deviationsDetails"
          placeholder="Describe deviations..."
          defaultValue={data?.deviationsDetails ?? ""}
          rows={3}
          className="mt-1"
        />
      </div>
      <YesNoField
        name="issuesAffectingYesNo"
        label="Were there issues affecting the audit?"
        defaultValue={data?.issuesAffectingYesNo ?? false}
      />
      <div>
        <Label htmlFor="issuesAffectingDetails">Issues details</Label>
        <Textarea
          id="issuesAffectingDetails"
          name="issuesAffectingDetails"
          placeholder="Describe issues..."
          defaultValue={data?.issuesAffectingDetails ?? ""}
          rows={3}
          className="mt-1"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="nextAuditDateFrom">Next audit — from</Label>
          <Input
            id="nextAuditDateFrom"
            name="nextAuditDateFrom"
            type="date"
            defaultValue={formatDate(data?.nextAuditDateFrom ?? null)}
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="nextAuditDateTo">Next audit — to</Label>
          <Input
            id="nextAuditDateTo"
            name="nextAuditDateTo"
            type="date"
            defaultValue={formatDate(data?.nextAuditDateTo ?? null)}
            className="mt-1"
          />
        </div>
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Saving..." : "Save Plan Review"}
      </Button>
    </form>
  )
}

// ─── Audit Summary Form ────────────────────────────────────────────────────────

type AuditSummaryData = {
  objectivesMet: boolean
  objectivesComments: string
  scopeAppropriate: boolean
  scopeComments: string
  msMeetsRequirements: boolean
  msComments: string
  managementReviewEffective: boolean
  managementReviewComments: string
  internalAuditEffective: boolean
  internalAuditComments: string
  msEffective: boolean
  msEffectiveComments: string
  correctUseOfLogos: boolean
  logosComments: string
  promotedToCommittee: boolean
  committeeComments: string
  generalCommentary: string
} | null

const SUMMARY_ROWS: [string, string, string][] = [
  ["objectivesMet", "objectivesComments", "Audit objectives met"],
  ["scopeAppropriate", "scopeComments", "Scope is appropriate"],
  ["msMeetsRequirements", "msComments", "Management system meets requirements"],
  ["managementReviewEffective", "managementReviewComments", "Management review is effective"],
  ["internalAuditEffective", "internalAuditComments", "Internal audit is effective"],
  ["msEffective", "msEffectiveComments", "Management system is effective"],
  ["correctUseOfLogos", "logosComments", "Correct use of logos / certificates"],
  ["promotedToCommittee", "committeeComments", "Promoted to committee"],
]

export function AuditSummaryForm({
  data,
  action,
}: {
  data: AuditSummaryData
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})
  const d = data as Record<string, unknown> | null

  return (
    <form action={formAction} className="space-y-4">
      {SUMMARY_ROWS.map(([boolField, commentField, label]) => (
        <div key={boolField} className="space-y-2 border rounded p-3">
          <YesNoField
            name={boolField}
            label={label}
            defaultValue={d ? d[boolField] === true : false}
          />
          <Textarea
            name={commentField}
            placeholder="Comments..."
            defaultValue={(d?.[commentField] as string) ?? ""}
            rows={2}
            className="text-sm"
          />
        </div>
      ))}
      <div>
        <Label htmlFor="generalCommentary">General commentary</Label>
        <Textarea
          id="generalCommentary"
          name="generalCommentary"
          placeholder="General comments on the audit..."
          defaultValue={data?.generalCommentary ?? ""}
          rows={4}
          className="mt-1"
        />
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Saving..." : "Save Summary"}
      </Button>
    </form>
  )
}

// ─── Add Recommendation Form ───────────────────────────────────────────────────

export function AddRecommendationForm({
  action,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-2">
      <Textarea
        name="recommendation"
        placeholder="Enter recommendation..."
        rows={2}
        required
        minLength={5}
      />
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Adding..." : "Add Recommendation"}
      </Button>
    </form>
  )
}
