"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Settings, ShieldCheck, Building, Key, Database } from "lucide-react";

export default function SettingsPage() {
  const { currentOrg, role, user, isAuthenticated } = useAuth();

  return (
    <div className="max-w-4xl space-y-6">
      <div className="border-b pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Settings className="h-6 w-6 text-primary" />
          Organization Settings
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Workspace configurations, security policies, and tenant isolation parameters
        </p>
      </div>

      <div className="grid gap-6">
        {/* Workspace Details */}
        <Card>
          <CardHeader className="border-b pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Building className="h-4 w-4 text-primary" />
              Organization Identity
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-4 text-xs">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <span className="text-muted-foreground block text-[11px]">Organization Name</span>
                <span className="font-semibold text-foreground text-sm">
                  {currentOrg?.name || "Default Organization"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block text-[11px]">Organization ID</span>
                <span className="font-mono text-muted-foreground">
                  {currentOrg?.organization_id || "org-default"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block text-[11px]">Your Assigned Role</span>
                <Badge variant="secondary" className="capitalize text-xs mt-1">
                  {role ? role.replace("_", " ") : "Viewer"}
                </Badge>
              </div>
              <div>
                <span className="text-muted-foreground block text-[11px]">Active User Email</span>
                <span className="text-foreground">{user?.email || "Authenticated Session"}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security & Isolation Policies */}
        <Card>
          <CardHeader className="border-b pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Security Architecture & Multi-Tenant Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-3 text-xs leading-relaxed text-muted-foreground">
            <div className="flex items-start gap-3 p-3 rounded-lg border bg-muted/30">
              <Key className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div>
                <strong className="text-foreground block">Session Security & Token Storage:</strong>
                Refresh tokens reside strictly in HttpOnly, SameSite=Strict cookies. Access tokens reside solely in memory and are reissued via CSRF-protected refresh headers. No credentials are kept in localStorage.
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg border bg-muted/30">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-foreground block">Server-Side Multi-Tenant Isolation:</strong>
                All queries filter by <code>organization_id</code> at the SQLAlchemy repository tier. Cross-tenant access attempts return 404 Not Found to prevent resource enumeration.
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg border bg-muted/30">
              <Database className="h-4 w-4 text-sky-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-foreground block">Durable Persistence & Audit Trail:</strong>
                Research executions, evidence claims, strategic analyses, and report artifacts are versioned and stored with cryptographic hashes and execution metadata.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
