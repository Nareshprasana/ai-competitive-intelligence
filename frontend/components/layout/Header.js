"use client";

import Link from "next/link";
import { LogOut, Building, ShieldCheck, Wifi, WifiOff } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function Header() {
  const {
    currentOrg,
    organizations,
    switchOrganization,
    role,
    user,
    isAuthenticated,
    logout,
    isBackendHealthy,
  } = useAuth();

  return (
    <header className="sticky top-0 z-20 h-16 border-b border-input bg-card/90 backdrop-blur-md px-6 flex items-center justify-between">
      {/* Workspace / Org Switcher */}
      <div className="flex items-center gap-4">
        {isAuthenticated && organizations.length > 0 ? (
          <div className="flex items-center gap-2">
            <Building className="h-4 w-4 text-muted-foreground" />
            <select
              className="h-8 rounded-md border border-input bg-background px-2.5 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              value={currentOrg?.organization_id || ""}
              onChange={(e) => switchOrganization(e.target.value)}
              aria-label="Active Organization"
            >
              {organizations.map((org) => (
                <option key={org.organization_id} value={org.organization_id}>
                  {org.name} ({org.role})
                </option>
              ))}
            </select>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">ACIS Intelligence Platform</span>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Backend health pill */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-2">
          {isBackendHealthy === true ? (
            <span className="flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              API Connected
            </span>
          ) : isBackendHealthy === false ? (
            <span className="flex items-center gap-1 text-[11px] text-amber-600 font-medium">
              <WifiOff className="h-3.5 w-3.5" />
              API Offline
            </span>
          ) : null}
        </div>

        {isAuthenticated ? (
          <>
            <div className="text-right hidden sm:block">
              <div className="text-xs font-medium text-foreground">
                {user?.email || "Authenticated User"}
              </div>
              <div className="text-[10px] text-muted-foreground capitalize">
                {role ? role.replace("_", " ") : "Viewer"}
              </div>
            </div>
            <Button
              variant="outline"
              className="h-8 px-2.5 text-xs gap-1.5"
              onClick={logout}
              title="Sign Out"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </>
        ) : (
          <Link href="/login">
            <Button className="h-8 px-3 text-xs">Sign In</Button>
          </Link>
        )}
      </div>
    </header>
  );
}

export default Header;
