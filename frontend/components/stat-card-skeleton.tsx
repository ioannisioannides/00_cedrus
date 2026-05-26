import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function StatCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="h-4 w-24 bg-muted rounded animate-pulse" />
        <div className="h-4 w-4 bg-muted rounded-full animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="h-8 w-16 bg-muted rounded mb-2 animate-pulse" />
        <div className="h-3 w-28 bg-muted rounded animate-pulse" />
      </CardContent>
    </Card>
  )
}
