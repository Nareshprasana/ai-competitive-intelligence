"use client";

import { useState, useEffect, useCallback } from "react";
import ResearchForm from "@/components/ResearchForm";
import ReportDisplay from "@/components/ReportDisplay";
import {
  getOrganizations,
  getResearch,
  health,
  login,
  logout,
  refreshAccessToken,
  setOrganizationId,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Home() {
  const [healthOk, setHealthOk] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrganization, setSelectedOrganization] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [researchId, setResearchId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    health()
      .then(() => setHealthOk(true))
      .catch(() => setHealthOk(false));

    async function restoreSession() {
      let token;
      try {
        token = await refreshAccessToken();
      } catch {
        return;
      }
      if (!token) return;
      try {
        const availableOrganizations = await getOrganizations();
        const savedOrganization =
          window.localStorage.getItem("acis-organization-id");
        const selected = availableOrganizations.some(
          (organization) => organization.organization_id === savedOrganization,
        )
          ? savedOrganization
          : availableOrganizations[0]?.organization_id || "";
        setOrganizations(availableOrganizations);
        setSelectedOrganization(selected);
        setOrganizationId(selected);
        setAuthenticated(true);
      } catch {
        setAuthenticated(false);
      }
    }

    restoreSession();
  }, []);

  async function handleLogin(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      const availableOrganizations = await getOrganizations();
      const selected = availableOrganizations[0]?.organization_id || "";
      setOrganizations(availableOrganizations);
      setSelectedOrganization(selected);
      setOrganizationId(selected);
      if (selected) {
        window.localStorage.setItem("acis-organization-id", selected);
      }
      setAuthenticated(true);
      setPassword("");
    } catch (loginError) {
      setError(loginError.message || "Sign-in failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await logout();
    setAuthenticated(false);
    setOrganizations([]);
    setSelectedOrganization("");
    setResearchId(null);
    setResult(null);
  }

  function handleOrganizationChange(event) {
    const value = event.target.value;
    setSelectedOrganization(value);
    setOrganizationId(value);
    window.localStorage.setItem("acis-organization-id", value);
    setResearchId(null);
    setResult(null);
  }

  const handleSubmit = useCallback((data) => {
    setResearchId(data.research_id);
    setResult(null);
    setError(null);
  }, []);

  const poll = useCallback(async () => {
    if (!researchId) return;
    setLoading(true);
    try {
      const fetched = await getResearch(researchId);
      if (fetched) setResult(fetched.results);
    } catch (err) {
      setError(err.message || "Failed to load research");
    } finally {
      setLoading(false);
    }
  }, [researchId]);

  useEffect(() => {
    if (!researchId) return;
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, [researchId, poll]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        {!authenticated ? (
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>Sign in</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? "Signing in…" : "Sign in"}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card className="max-w-2xl">
              <CardContent className="flex flex-wrap items-end gap-4 pt-6">
                <div className="grid min-w-64 flex-1 gap-2">
                  <Label htmlFor="organization">Organization</Label>
                  <select
                    id="organization"
                    className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                    value={selectedOrganization}
                    onChange={handleOrganizationChange}
                    disabled={organizations.length === 0}
                  >
                    {organizations.length === 0 ? (
                      <option value="">No organization membership</option>
                    ) : (
                      organizations.map((organization) => (
                        <option
                          key={organization.organization_id}
                          value={organization.organization_id}
                        >
                          {organization.name} ({organization.role})
                        </option>
                      ))
                    )}
                  </select>
                </div>
                <Button type="button" variant="outline" onClick={handleLogout}>
                  Sign out
                </Button>
              </CardContent>
            </Card>
            {selectedOrganization ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>New Research</CardTitle>
                  </CardHeader>
                </Card>
                <ResearchForm onSubmit={handleSubmit} />
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                An organization invitation is required before you can access research.
              </p>
            )}
          </>
        )}
        {healthOk === false && (
          <div className="text-xs text-amber-600">
            Backend not reachable at {process.env.NEXT_PUBLIC_API_URL ||
            "http://localhost:8000"}. Start the FastAPI server first.
          </div>
        )}
      </div>

      {(result || error) && (
        <Card className="max-w-5xl">
          {error && (
            <div className="p-4 text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
              {error}
            </div>
          )}
          {result && <ReportDisplay result={result} />}
          {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
        </Card>
      )}
    </div>
  );
}
