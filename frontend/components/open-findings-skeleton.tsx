import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function OpenFindingsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="h-5 w-40 bg-muted rounded animate-pulse" />
        <div className="h-4 w-56 bg-muted rounded mt-2 animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="divide-y">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between py-3">
              <div>
                <div className="h-4 w-48 bg-muted rounded mb-2 animate-pulse" />
                <div className="h-3 w-32 bg-muted rounded animate-pulse" />
              </div>
              <div className="h-5 w-20 bg-muted rounded animate-pulse" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
