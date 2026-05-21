"use client"

import React from "react"
import { useActionState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle, AlertCircle } from "lucide-react"
import { createUser } from "@/lib/actions/super-admin"

const ROLES = [
  { value: "CB_ADMIN", label: "CB Admin" },
  { value: "LEAD_AUDITOR", label: "Lead Auditor" },
  { value: "TECHNICAL_REVIEWER", label: "Technical Reviewer" },
  { value: "DECISION_MAKER", label: "Decision Maker" },
  { value: "CLIENT_ADMIN", label: "Client Admin" },
  { value: "SUPER_ADMIN", label: "Super Admin" },
]

type CbOrg = { id: string; name: string }
type ClientOrgItem = { id: string; name: string }

export function CreateUserForm({ cbOrgs, clientOrgs }: { cbOrgs: CbOrg[]; clientOrgs: ClientOrgItem[] }) {
  const [state, formAction, pending] = useActionState(createUser, {})
  const [selectedRole, setSelectedRole] = React.useState("")

  return (
    <form action={formAction} className="space-y-4 max-w-2xl">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="name">Full Name *</Label>
          <Input id="name" name="name" required minLength={2} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="email">Email *</Label>
          <Input id="email" name="email" type="email" required className="mt-1" />
        </div>
        <div>
          <Label htmlFor="password">Password *</Label>
          <Input id="password" name="password" type="password" required minLength={8} className="mt-1" />
        </div>
        <div>
          <Label htmlFor="role">Role *</Label>
          <Select name="role" required onValueChange={setSelectedRole}>
            <SelectTrigger id="role" className="mt-1">
              <SelectValue placeholder="Select role..." />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((r) => (
                <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {selectedRole === "CLIENT_ADMIN" ? (
          <div className="sm:col-span-2">
            <Label htmlFor="clientOrgId">Client Organisation *</Label>
            <select
              id="clientOrgId"
              name="clientOrgId"
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— None —</option>
              {clientOrgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        ) : (
          <div className="sm:col-span-2">
            <Label htmlFor="cbOrgId">CB Organisation (if applicable)</Label>
            <select
              id="cbOrgId"
              name="cbOrgId"
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— None —</option>
              {cbOrgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {state.success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          <CheckCircle className="h-4 w-4" /> User created successfully
        </div>
      )}
      {state.error && (
        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
          <AlertCircle className="h-4 w-4" /> {state.error}
        </div>
      )}

      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Creating..." : "Create User"}
      </Button>
    </form>
  )
}
