"use client";

import { useState } from "react";
import Link from "next/link";
import { UserCog, UserPlus, Mail, Shield, CheckCircle2, ShieldAlert } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { inviteUser } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Modal } from "@/components/ui/modal";

export default function UserManagementPage() {
  const { canManageUsers, currentOrg, role } = useAuth();

  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("analyst");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!canManageUsers) {
    return (
      <div className="max-w-xl mx-auto py-12 space-y-4 text-center">
        <Alert variant="destructive" title="Access Denied">
          User management is restricted to Organization Administrators and Owners. Your current role is &ldquo;{role || "viewer"}&rdquo;.
        </Alert>
        <Link href="/">
          <Button variant="outline" className="text-xs">
            Return to Dashboard
          </Button>
        </Link>
      </div>
    );
  }

  const handleInviteSubmit = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await inviteUser({ email: inviteEmail.trim(), role: inviteRole });
      setSuccessMsg(`Invitation sent to ${inviteEmail} with role ${inviteRole}.`);
      setInviteEmail("");
      setTimeout(() => {
        setSuccessMsg(null);
        setInviteModalOpen(false);
      }, 1500);
    } catch (err) {
      setErrorMsg(err.message || "Failed to issue invitation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <UserCog className="h-6 w-6 text-primary" />
            User Management
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage organization members, invite analysts, and enforce Role-Based Access Controls
          </p>
        </div>

        <Button
          className="h-9 text-xs gap-1.5"
          onClick={() => {
            setErrorMsg(null);
            setSuccessMsg(null);
            setInviteModalOpen(true);
          }}
        >
          <UserPlus className="h-4 w-4" />
          Invite Team Member
        </Button>
      </div>

      {/* Role Breakdown Reference Card */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs uppercase tracking-wide text-foreground">
              Organization Admin
            </span>
            <Badge variant="default" className="text-[10px]">Admin</Badge>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Full management of users, research pipelines, evidence overrides, and strategic reports within the organization.
          </p>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs uppercase tracking-wide text-foreground">
              Intelligence Analyst
            </span>
            <Badge variant="secondary" className="text-[10px]">Analyst</Badge>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Create research runs, discover competitors, evaluate evidence credibility, and record human review decisions.
          </p>
        </Card>

        <Card className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs uppercase tracking-wide text-foreground">
              Executive Viewer
            </span>
            <Badge variant="outline" className="text-[10px]">Viewer</Badge>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Read-only access to view research progress, competitor profiles, SWOT matrices, and download intelligence reports.
          </p>
        </Card>
      </div>

      {/* Members Table */}
      <Card>
        <CardHeader className="border-b pb-3">
          <CardTitle className="text-sm font-semibold">Active Organization Members</CardTitle>
          <p className="text-xs text-muted-foreground">
            Members registered in workspace <strong>{currentOrg?.name}</strong>
          </p>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
              <tr>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Access Level</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-input/50">
              <tr className="hover:bg-muted/30">
                <td className="py-3 px-4">
                  <div className="font-semibold text-foreground">Lead Analyst</div>
                  <span className="text-[11px] text-muted-foreground">admin@enterprise.com</span>
                </td>
                <td className="py-3 px-4">
                  <Badge variant="default" className="text-[10px]">organization_admin</Badge>
                </td>
                <td className="py-3 px-4 text-muted-foreground">Full Read / Write / User Management</td>
                <td className="py-3 px-4">
                  <Badge variant="success" className="text-[10px] gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Active
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Invite Member Modal */}
      <Modal
        isOpen={inviteModalOpen}
        onClose={() => setInviteModalOpen(false)}
        title="Invite New Organization Member"
        description={`Send an invitation to join workspace "${currentOrg?.name}" with specified permissions.`}
      >
        <form onSubmit={handleInviteSubmit} className="space-y-4 pt-2">
          {errorMsg && (
            <Alert variant="destructive" title="Invitation Failed">
              {errorMsg}
            </Alert>
          )}
          {successMsg && (
            <Alert variant="success" title="Invitation Sent">
              {successMsg}
            </Alert>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="inviteEmail" className="text-xs font-medium">
              Email Address <span className="text-destructive">*</span>
            </Label>
            <div className="relative">
              <Input
                id="inviteEmail"
                type="email"
                placeholder="colleague@enterprise.com"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="pl-9 text-xs"
              />
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="inviteRole" className="text-xs font-medium">
              Assigned Role
            </Label>
            <select
              id="inviteRole"
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
            >
              <option value="analyst">Intelligence Analyst (Create Research, Review Evidence)</option>
              <option value="viewer">Viewer (Read-only reports and dashboards)</option>
              <option value="organization_admin">Organization Administrator (Full Admin)</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t">
            <Button
              variant="outline"
              type="button"
              className="text-xs"
              onClick={() => setInviteModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="text-xs gap-1.5">
              {loading ? "Sending Invitation…" : "Send Invitation"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
