"use client"

import { useTransition } from "react"
import { updateAuditStatus } from "@/lib/actions/audits"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import type { AuditStatus } from "@prisma/client"

interface Props {
  auditId: string
  targetStatus: AuditStatus
  label: string
  variant?: "default" | "outline" | "secondary" | "destructive"
  notes?: string
}

export function StatusTransitionButton({ auditId, targetStatus, label, variant = "default", notes }: Props) {
  const [isPending, startTransition] = useTransition()
  const router = useRouter()

  function handleClick() {
    startTransition(async () => {
      const result = await updateAuditStatus(auditId, targetStatus, notes)
      if (result.error) {
        toast.error(result.error)
      } else {
        toast.success(`Status updated to ${targetStatus.replace("_", " ")}.`)
        router.refresh()
      }
    })
  }

  return (
    <Button onClick={handleClick} disabled={isPending} variant={variant} size="sm">
      {isPending ? "Updating…" : label}
    </Button>
  )
}
