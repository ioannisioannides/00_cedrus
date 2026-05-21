"use client"

import { useActionState } from "react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { createCbUser } from "@/lib/actions/users"

const ROLES = [
  { value: "LEAD_AUDITOR", label: "Lead Auditor" },
  { value: "TECHNICAL_REVIEWER", label: "Technical Reviewer" },
  { value: "DECISION_MAKER", label: "Decision Maker" },
  { value: "CB_ADMIN", label: "CB Admin" },
]

export default function NewCbUserPage() {
  const router = useRouter()
  const [state, formAction, pending] = useActionState(createCbUser, {})

  useEffect(() => {
    if (state.success) {
      toast.success("User created.")
      router.push("/cb-admin/users")
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, router])

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New User</h1>
        <p className="text-muted-foreground">Add a new auditor or administrator to your CB.</p>
      </div>

      <Card>
        <CardHeader><CardTitle>User Details</CardTitle></CardHeader>
        <CardContent>
          <form action={formAction} className="space-y-4">
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
                <Select name="role" required>
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
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={pending} size="sm">
                {pending ? "Creating..." : "Create User"}
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
