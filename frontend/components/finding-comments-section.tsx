"use client"

import { useActionState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { addFindingComment } from "@/lib/actions/finding-comments"
import { format } from "date-fns"
import { MessageSquare } from "lucide-react"

interface FindingCommentData {
  id: string
  comment: string
  createdAt: Date
  user: {
    name: string
    role: string
  }
}

interface FindingCommentsSectionProps {
  findingId: string
  comments: FindingCommentData[]
}

export function FindingCommentsSection({ findingId, comments }: FindingCommentsSectionProps) {
  const formRef = useRef<HTMLFormElement>(null)
  const boundAction = addFindingComment.bind(null, findingId)
  const [state, formAction, isPending] = useActionState(boundAction, {})

  useEffect(() => {
    if (state.success) {
      if (formRef.current) {
        formRef.current.reset()
      }
      // Reload or trigger dynamic cache refresh is handled by server action revalidatePath
      // But re-rendering the local component or triggering reload helps UX
      window.location.reload()
    }
  }, [state.success])

  return (
    <div className="mt-6 border-t pt-4 space-y-4">
      <div className="flex items-center gap-2 font-medium text-sm text-foreground">
        <MessageSquare className="h-4 w-4" />
        <span>Discussion ({comments.length})</span>
      </div>

      {comments.length > 0 && (
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
          {comments.map((c) => (
            <div key={c.id} className="text-sm bg-muted/30 p-3 rounded-lg border">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-semibold text-primary">{c.user.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono uppercase tracking-wider bg-primary/10 text-primary-foreground font-semibold px-1.5 py-0.2 rounded">
                    {c.user.role.replace("_", " ")}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(c.createdAt), "dd MMM yyyy HH:mm")}
                  </span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{c.comment}</p>
            </div>
          ))}
        </div>
      )}

      <form ref={formRef} action={formAction} className="space-y-2">
        {state.error && (
          <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {state.error}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor={`comment-${findingId}`} className="sr-only">Add a comment</Label>
          <textarea
            id={`comment-${findingId}`}
            name="comment"
            placeholder="Add to the conversation or request clarification..."
            required
            rows={2}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
        </div>

        <div className="flex justify-end">
          <Button type="submit" size="sm" disabled={isPending}>
            {isPending ? "Posting..." : "Comment"}
          </Button>
        </div>
      </form>
    </div>
  )
}
