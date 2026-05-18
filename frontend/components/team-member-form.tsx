"use client"

import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, AlertCircle } from "lucide-react"

type FormState = { error?: string; success?: boolean }

const ROLES = [
  { value: "LEAD_AUDITOR", label: "Lead Auditor" },
  { value: "AUDITOR", label: "Auditor" },
  { value: "TECHNICAL_EXPERT", label: "Technical Expert" },
  { value: "TRAINEE", label: "Trainee" },
  { value: "OBSERVER", label: "Observer" },
]

function FormMessage({ state }: { state: FormState }) {
  if (state.success)
    return (
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
        <CheckCircle className="h-4 w-4" /> Team member added
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

export function AddTeamMemberForm({
  action,
}: {
  action: (prev: FormState, fd: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState(action, {})

  return (
    <form action={formAction} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="name">Full Name *</Label>
          <Input id="name" name="name" placeholder="John Smith" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="title">Title / Position</Label>
          <Input id="title" name="title" placeholder="e.g. Senior Auditor" className="mt-1" />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <Label htmlFor="role">Role *</Label>
          <Select name="role" required>
            <SelectTrigger className="mt-1" id="role">
              <SelectValue placeholder="Select role..." />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="dateFrom">From *</Label>
          <Input id="dateFrom" name="dateFrom" type="date" required className="mt-1" />
        </div>
        <div>
          <Label htmlFor="dateTo">To *</Label>
          <Input id="dateTo" name="dateTo" type="date" required className="mt-1" />
        </div>
      </div>
      <FormMessage state={state} />
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Adding..." : "Add Team Member"}
      </Button>
    </form>
  )
}
