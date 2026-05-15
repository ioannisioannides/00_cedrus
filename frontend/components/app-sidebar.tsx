"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Badge } from "@/components/ui/badge"
import {
  LayoutDashboard,
  Building2,
  Users,
  ClipboardList,
  UserCheck,
  Building,
  FileText,
  Eye,
  CheckSquare,
  ShieldCheck,
} from "lucide-react"
import type { Role } from "@prisma/client"

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
}

const NAV_ITEMS: Record<Role, NavItem[]> = {
  SUPER_ADMIN: [
    { title: "Dashboard", href: "/super-admin", icon: LayoutDashboard },
    { title: "CB Organisations", href: "/super-admin/cb-orgs", icon: Building2 },
    { title: "Users", href: "/super-admin/users", icon: Users },
    { title: "Standards", href: "/super-admin/standards", icon: FileText },
  ],
  CB_ADMIN: [
    { title: "Dashboard", href: "/cb-admin", icon: LayoutDashboard },
    { title: "Clients", href: "/cb-admin/clients", icon: Building },
    { title: "Audits", href: "/cb-admin/audits", icon: ClipboardList },
    { title: "Audit Programs", href: "/cb-admin/programs", icon: FileText },
    { title: "Auditors", href: "/cb-admin/auditors", icon: UserCheck },
  ],
  LEAD_AUDITOR: [
    { title: "Dashboard", href: "/lead-auditor", icon: LayoutDashboard },
    { title: "My Audits", href: "/lead-auditor/audits", icon: ClipboardList },
  ],
  TECHNICAL_REVIEWER: [
    { title: "Dashboard", href: "/technical-reviewer", icon: LayoutDashboard },
    { title: "Pending Reviews", href: "/technical-reviewer/reviews", icon: Eye },
  ],
  DECISION_MAKER: [
    { title: "Dashboard", href: "/decision-maker", icon: LayoutDashboard },
    { title: "Pending Decisions", href: "/decision-maker/decisions", icon: CheckSquare },
  ],
  CLIENT_ADMIN: [
    { title: "Dashboard", href: "/client-admin", icon: LayoutDashboard },
    { title: "My Audits", href: "/client-admin/audits", icon: ClipboardList },
  ],
}

const ROLE_LABELS: Record<Role, string> = {
  SUPER_ADMIN: "Super Admin",
  CB_ADMIN: "CB Administrator",
  LEAD_AUDITOR: "Lead Auditor",
  TECHNICAL_REVIEWER: "Technical Reviewer",
  DECISION_MAKER: "Decision Maker",
  CLIENT_ADMIN: "Client Admin",
}

interface AppSidebarProps {
  user: {
    name: string
    email: string
    role: Role
    organizationId: string | null
  }
}

export function AppSidebar({ user }: AppSidebarProps) {
  const pathname = usePathname()
  const navItems = NAV_ITEMS[user.role]

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-3 px-3 py-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
            C
          </div>
          <div className="flex flex-col gap-0.5 min-w-0">
            <span className="text-sm font-semibold truncate">Cedrus</span>
            <span className="text-xs text-muted-foreground truncate">GRC Platform</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    render={<Link href={item.href} />}
                    isActive={pathname === item.href || pathname.startsWith(item.href + "/")}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="px-3 py-3 border-t">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-muted-foreground shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">{user.name}</p>
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 mt-0.5">
                {ROLE_LABELS[user.role]}
              </Badge>
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
