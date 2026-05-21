"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <AlertTriangle className="h-10 w-10 text-destructive" />
      <h2 className="text-xl font-bold">Something went wrong</h2>
      <p className="text-muted-foreground max-w-sm text-sm">
        An error occurred while loading this page. Please try again.
      </p>
      <Button onClick={reset} variant="outline" size="sm">Try again</Button>
    </div>
  )
}
