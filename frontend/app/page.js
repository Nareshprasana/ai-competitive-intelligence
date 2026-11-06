"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Compass,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Building2,
  Users2,
  AlertTriangle,
  FileText,
  ArrowRight,
  Plus,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch, getOrganizationId } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";

export default function OverviewPage() {
  const { isAuthenticated, isLoading: authLoading, currentOrg, currentOrgId, canCreateResearch } = useAuth();
  const [researchList, setResearchList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    const activeAtStart = currentOrgId || currentOrg?.organization_id;
    try {
      const items = await listResearch({ limit: 50 });
      if (getOrganizationId() === activeAtStart) {
        setResearchList(items || []);
      }
    } catch (err) {
      if (getOrganizationId() === activeAtStart) {
        setError(err.message || "Failed to load dashboard metrics.");
      }
    } finally {
      if (getOrganizationId() === activeAtStart) {
        setLoading(false);
      }
    }
  }, [isAuthenticated, currentOrgId, currentOrg]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (authLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Restoring organization workspace…
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="py-12 space-y-8">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
            <Compass className="h-4 w-4" />
            ACIS Intelligence Platform
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-foreground">
            Evidence-Backed Competitive Intelligence
          </h1>
          <p className="text-base text-muted-foreground leading-relaxed">
            Multi-agent research orchestration, automated evidence validation, cross-source contradiction detection, and 14-section strategic analysis for enterprise decision-makers.
          </p>
          <div className="pt-2 flex items-center gap-3">
            <Link href="/login">
              <Button className="gap-2">
                Sign In to Workspace
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3 pt-6 border-t">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Search className="h-4 w-4 text-primary" />
                Multi-Agent Workflow
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground leading-relaxed">
              Planner, Company Researcher, and Competitor Discovery agents discover market landscape with SSRF protection and deterministic fallbacks.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Evidence Validation
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground leading-relaxed">
              Mathematical source-credibility tiering, category-specific freshness decay, and automated cross-source contradiction detection.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Strategic Reporting
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground leading-relaxed">
              14-section strategic reports delivered synchronously in JSON, structured Markdown, and professional ReportLab PDF formats.
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Calculate actual counts from backend data
  const totalRuns = researchList.length;
  const completedRuns = researchList.filter((r) => r.status === "completed").length;
  const failedRuns = researchList.filter((r) => r.status === "failed").length;
  const runningRuns = researchList.filter((r) => r.status === "running" || r.status === "pending").length;

  const uniqueCompanies = new Set(researchList.map((r) => r.company_name).filter(Boolean)).size;
  const totalCompetitors = researchList.reduce((acc, r) => acc + (r.competitors_count || 0), 0);
  const totalReports = researchList.filter((r) => r.has_report).length;
  const pendingReviews = researchList.filter((r) => r.review_status === "requires_review" || r.review_status === "pending").length;

  return (
    <div className="space-y-6">
      {/* Workspace Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Intelligence Overview
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Active Workspace: <strong className="text-foreground">{currentOrg?.name}</strong> • Real-time telemetry & execution status
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="h-9 text-xs gap-1.5"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          {canCreateResearch && (
            <Link href="/research/new">
              <Button className="h-9 text-xs gap-1.5">
                <Plus className="h-4 w-4" />
                New Research
              </Button>
            </Link>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive" title="Workspace Error">
          {error}
        </Alert>
      )}

      {/* Actual Metrics Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Total Executions
            </div>
            <div className="text-2xl font-bold mt-1 text-foreground">{totalRuns}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              {completedRuns} completed • {failedRuns} failed
            </div>
          </div>
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Search className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Companies Researched
            </div>
            <div className="text-2xl font-bold mt-1 text-foreground">{uniqueCompanies}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              Across target industries
            </div>
          </div>
          <div className="p-2 rounded-lg bg-sky-500/10 text-sky-600">
            <Building2 className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Discovered Competitors
            </div>
            <div className="text-2xl font-bold mt-1 text-foreground">{totalCompetitors}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              Qualified & categorized
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600">
            <Users2 className="h-5 w-5" />
          </div>
        </Card>

        <Card className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Generated Reports
            </div>
            <div className="text-2xl font-bold mt-1 text-foreground">{totalReports}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              JSON • Markdown • PDF
            </div>
          </div>
          <div className="p-2 rounded-lg bg-violet-500/10 text-violet-600">
            <FileText className="h-5 w-5" />
          </div>
        </Card>
      </div>

      {/* Pending Reviews Notice */}
      {pendingReviews > 0 && (
        <Alert variant="warning" title="Analyst Review Attention Required">
          There are <strong>{pendingReviews}</strong> research runs with unverified claims, cross-source contradictions, or pending human review.
          <Link href="/evidence" className="ml-2 font-semibold underline hover:opacity-80">
            Open Evidence Review &rarr;
          </Link>
        </Alert>
      )}

      {/* Recent Research Runs Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between border-b pb-4">
          <div>
            <CardTitle className="text-base font-semibold">Recent Research Activity</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Latest competitive intelligence research runs for {currentOrg?.name}
            </p>
          </div>
          <Link href="/research" className="text-xs font-medium text-primary hover:underline">
            View all projects &rarr;
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          {researchList.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <div className="p-3 rounded-full bg-muted w-fit mx-auto text-muted-foreground">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">No research runs found</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Begin competitive intelligence analysis by initiating a research execution for a target company.
              </p>
              {canCreateResearch && (
                <div className="pt-2">
                  <Link href="/research/new">
                    <Button className="text-xs gap-1.5">
                      <Plus className="h-3.5 w-3.5" />
                      Start First Research
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                  <tr>
                    <th className="py-3 px-4">Target Company</th>
                    <th className="py-3 px-4">Research Question</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Competitors</th>
                    <th className="py-3 px-4">Evidence</th>
                    <th className="py-3 px-4">Created</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-input/50">
                  {researchList.slice(0, 10).map((r) => {
                    const isSuccess = r.status === "completed";
                    const isFail = r.status === "failed";
                    return (
                      <tr key={r.research_id} className="hover:bg-muted/30 transition-colors">
                        <td className="py-3 px-4 font-semibold text-foreground">
                          <Link
                            href={`/research/${encodeURIComponent(r.research_id)}`}
                            className="hover:underline text-primary"
                          >
                            {r.company_name}
                          </Link>
                          <span className="block text-[10px] font-normal text-muted-foreground">
                            {r.industry || "General"}
                          </span>
                        </td>
                        <td className="py-3 px-4 max-w-xs truncate text-muted-foreground">
                          {r.research_question}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            variant={isSuccess ? "success" : isFail ? "danger" : "warning"}
                            className="text-[10px]"
                          >
                            {isSuccess ? (
                              <CheckCircle2 className="h-3 w-3" />
                            ) : isFail ? (
                              <XCircle className="h-3 w-3" />
                            ) : (
                              <Clock className="h-3 w-3" />
                            )}
                            {r.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-muted-foreground">
                          {r.competitors_count || 0}
                        </td>
                        <td className="py-3 px-4 text-muted-foreground">
                          {r.evidence_count || 0}
                        </td>
                        <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : "Recent"}
                        </td>
                        <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                          <Link href={`/research/${encodeURIComponent(r.research_id)}`}>
                            <Button variant="outline" className="h-7 px-2.5 text-[11px]">
                              Details
                            </Button>
                          </Link>
                          {r.has_report && (
                            <Link href={`/reports?research_id=${encodeURIComponent(r.research_id)}`}>
                              <Button variant="secondary" className="h-7 px-2.5 text-[11px]">
                                Report
                              </Button>
                            </Link>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
