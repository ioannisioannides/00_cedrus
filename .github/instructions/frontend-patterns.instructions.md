---
applyTo: "frontend/components/**,frontend/app/**"
---

# Frontend Component Patterns — Cedrus

## UI Components (`components/ui/`)

Built on `@base-ui/react` + Tailwind CSS. Use existing components — do not add new UI libraries.

```tsx
// Button (with router link)
import { Button } from "@/components/ui/button"
import Link from "next/link"
<Button render={<Link href="/cb-admin/audits/new" />}>New Audit</Button>

// Card layout
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
<Card>
  <CardHeader><CardTitle>Audits</CardTitle></CardHeader>
  <CardContent>...</CardContent>
</Card>

// Badge (enum status display)
import { Badge } from "@/components/ui/badge"
<Badge variant="outline">{formatEnum(audit.status)}</Badge>
```

## Form Rules

1. Forms always use `useActionState` — NOT `useState` + `fetch`
2. Server action is the `action` prop of `<form>`
3. Submit state managed via `pending` from `useActionState`
4. Show results via `toast.success()` / `toast.error()` from `sonner`

## Table Pattern (list pages)

```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Client</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {audits.map((a) => (
      <TableRow key={a.id}>
        <TableCell>{a.clientOrg.name}</TableCell>
        <TableCell><Badge variant="outline">{formatEnum(a.status)}</Badge></TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

## Stat Cards (dashboard pattern)

```tsx
import { StatCard } from "@/components/stat-card"
<StatCard title="Total Audits" value={count} icon={ClipboardList} href="/cb-admin/audits" />
```

## Icons

Use `lucide-react` exclusively. Import individually:
```tsx
import { ClipboardList, Users, AlertTriangle } from "lucide-react"
```
