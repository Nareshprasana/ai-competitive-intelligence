"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Building2,
  Users2,
  CheckSquare,
  TrendingUp,
  FileText,
  Settings,
  UserCog,
  Compass,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";

const NAVIGATION_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/research", label: "Research Projects", icon: Search },
  { href: "/companies", label: "Companies", icon: Building2 },
  { href: "/competitors", label: "Competitors", icon: Users2 },
  { href: "/evidence", label: "Evidence Review", icon: CheckSquare },
  { href: "/strategy", label: "Strategic Analysis", icon: TrendingUp },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/users", label: "User Management", icon: UserCog, adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { currentOrg, role, canManageUsers, isAuthenticated } = useAuth();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 w-64 border-r border-input bg-card flex flex-col justify-between">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-input/60">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <span className="font-semibold text-base tracking-tight block leading-tight">
                ACIS
              </span>
              <span className="text-[11px] text-muted-foreground block leading-tight">
                Competitive Intelligence
              </span>
            </div>
          </Link>
        </div>

        {/* Organization / Role summary in Sidebar */}
        {isAuthenticated && currentOrg && (
          <div className="px-4 py-3 mx-3 my-3 rounded-lg bg-muted/40 border border-input/60">
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Workspace
            </div>
            <div className="text-sm font-semibold truncate mt-0.5 text-foreground">
              {currentOrg.name}
            </div>
            <div className="mt-1 flex items-center gap-1.5">
              <Badge variant="secondary" className="text-[10px] py-0 px-2 font-normal capitalize">
                {role ? role.replace("_", " ") : "Member"}
              </Badge>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="px-3 py-2 space-y-1">
          {NAVIGATION_ITEMS.map((item) => {
            if (item.adminOnly && !canManageUsers) return null;
            const Icon = item.icon;
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-colors
                  ${
                    active
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }
                `}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-input/60 text-[11px] text-muted-foreground bg-card">
        <div className="flex items-center justify-between">
          <span className="font-medium text-foreground">ACIS Enterprise</span>
          <span>v2.0-2H</span>
        </div>
        <p className="mt-0.5 opacity-75">Multi-Agent Intelligence System</p>
      </div>
    </aside>
  );
}

export default Sidebar;
