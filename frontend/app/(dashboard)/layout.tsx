import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  if (!session?.user) redirect("/login")

  return (
    <SidebarProvider>
      <AppSidebar user={session.user} />
      <SidebarInset className="flex flex-col min-h-screen">
        <SiteHeader user={session.user} />
        <main className="flex-1 p-6 bg-muted/20">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  )
}
