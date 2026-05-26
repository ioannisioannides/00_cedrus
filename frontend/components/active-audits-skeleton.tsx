import { Card, CardHeader, CardContent } from "@/components/ui/card"

export default function ActiveAuditsSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="h-5 w-32 bg-muted rounded animate-pulse" />
        <div className="h-8 w-16 bg-muted rounded animate-pulse" />
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between px-6 py-3">
              <div>
                <div className="h-4 w-24 bg-muted rounded mb-2 animate-pulse" />
                <div className="h-3 w-40 bg-muted rounded animate-pulse" />
              </div>
              <div className="flex items-center gap-2">
                <div className="h-5 w-12 bg-muted rounded animate-pulse" />
                <div className="h-5 w-16 bg-muted rounded animate-pulse" />
                <div className="h-8 w-16 bg-muted rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
