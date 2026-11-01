"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Shield, Activity, BarChart3 } from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: Compass },
  { href: "/research", label: "Research", icon: Activity },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Shield },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-20 w-64 border-r border-input bg-background">
      <div className="h-full flex flex-col">
        <div className="p-6">
          <Link href="/" className="flex items-center gap-2">
            <Compass className="h-6 w-6" />
            <span className="font-semibold tracking-tight">ACIS</span>
          </Link>
          <p className="text-xs text-muted-foreground mt-1">
            AI Competitive Intelligence
          </p>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {NAV.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 rounded-medium px-3 py-2 text-sm font-medium transition-colors
                  ${active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-accent hover:text-accent-foreground"
                }
                `}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-6 text-xs text-muted-foreground">
          Phase 0 + 1 • LangGraph • FastAPI
        </div>
      </div>
    </aside>
  );
}
