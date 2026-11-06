"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Building2,
  Users2,
  CheckSquare,
  TrendingUp,
  FileText,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { getResearch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";

const NODE_ORDER = [
  { key: "initialize_research", label: "Initialize" },
  { key: "research_planner", label: "Research Planner" },
  { key: "company_researcher", label: "Company Researcher" },
  { key: "competitor_discovery", label: "Competitor Discovery" },
  { key: "evidence_validator", label: "Evidence Validator" },
  { key: "strategic_analyst", label: "Strategic Analyst" },
  { key: "report_generator", label: "Report Generator" },
  { key: "finalize_research", label: "Finalize" },
];

export default function ResearchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const researchId = params?.id;
  const { isAuthenticated } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pollTimerRef = useRef(null);

  const fetchDetail = useCallback(async () => {
    if (!researchId) return;
    try {
      const res = await getResearch(researchId);
      setData(res?.results || null);

      // Stop polling once terminal state is reached
      if (res?.status === "completed" || res?.status === "failed") {
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      }
    } catch (err) {
      setError(err.message || "Failed to load research execution details.");
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    } finally {
      setLoading(false);
    }
  }, [researchId]);

  useEffect(() => {
    fetchDetail();

    // Conservative polling (3 seconds) while active
    pollTimerRef.current = setInterval(fetchDetail, 3000);
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [fetchDetail]);

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin text-primary" />
          Loading pipeline execution telemetry…
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4 max-w-xl mx-auto py-12">
        <Alert variant="destructive" title="Research Not Found">
          {error || `Research run ${researchId} does not exist or belongs to another organization.`}
        </Alert>
        <Link href="/research">
          <Button variant="outline" className="text-xs">
            Return to Research Listing
          </Button>
        </Link>
      </div>
    );
  }

  const isSuccess = data.status === "completed";
  const isFailed = data.status === "failed";
  const metadata = data.execution_metadata || [];
  const errors = data.errors || [];
  const competitorsCount = (data.competitors || []).length;
  const evidenceCount = (data.evidence || []).length;
  const hasReport = Boolean(data.final_report);

  // Map executed nodes
  const executedNodesMap = new Map();
  metadata.forEach((m) => {
    executedNodesMap.set(m.node_name, m);
  });

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link href="/research">
              <Button variant="ghost" className="h-7 px-1.5 text-xs text-muted-foreground gap-1">
                <ArrowLeft className="h-3 w-3" />
                Projects
              </Button>
            </Link>
            <span className="text-muted-foreground">/</span>
            <span className="font-mono text-xs text-muted-foreground">{data.research_id}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
            {data.company_name}
            <Badge
              variant={isSuccess ? "success" : isFailed ? "danger" : "warning"}
              className="text-xs"
            >
              {isSuccess ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : isFailed ? (
                <XCircle className="h-3.5 w-3.5" />
              ) : (
                <Clock className="h-3.5 w-3.5 animate-spin" />
              )}
              {data.status}
            </Badge>
          </h1>
          <p className="text-xs text-muted-foreground max-w-2xl">{data.research_question}</p>
        </div>

        <div className="flex items-center gap-2">
          {hasReport && (
            <Link href={`/reports?research_id=${encodeURIComponent(data.research_id)}`}>
              <Button className="h-9 text-xs gap-1.5">
                <FileText className="h-4 w-4" />
                View 14-Section Report
              </Button>
            </Link>
          )}
          <Button variant="outline" className="h-9 text-xs gap-1.5" onClick={fetchDetail}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Errors Alert if any */}
      {errors.length > 0 && (
        <Alert variant="destructive" title="Pipeline Errors Encountered">
          <ul className="list-disc pl-4 space-y-1 mt-1">
            {errors.map((err, i) => (
              <li key={i}>
                <strong>{err.node_name || "Error"}:</strong> {err.error || JSON.stringify(err)}
              </li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Execution Stages Flow */}
      <Card>
        <CardHeader className="border-b pb-3">
          <CardTitle className="text-sm font-semibold">LangGraph Pipeline Execution</CardTitle>
          <p className="text-xs text-muted-foreground">
            Deterministic sequence across all 8 multi-agent orchestration nodes
          </p>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {NODE_ORDER.map((node, index) => {
              const exec = executedNodesMap.get(node.key);
              const nodeCompleted = exec?.status === "completed";
              const nodeFailed = exec?.status === "failed";
              const nodePending = !exec;

              return (
                <div
                  key={node.key}
                  className={`p-3 rounded-lg border text-xs flex flex-col justify-between transition-colors ${
                    nodeCompleted
                      ? "bg-emerald-50/60 border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-800"
                      : nodeFailed
                      ? "bg-rose-50/60 border-rose-200 dark:bg-rose-950/20 dark:border-rose-800"
                      : "bg-muted/30 border-input text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono text-muted-foreground">0{index + 1}</span>
                    {nodeCompleted ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    ) : nodeFailed ? (
                      <XCircle className="h-3.5 w-3.5 text-rose-600" />
                    ) : (
                      <Clock className="h-3.5 w-3.5 text-muted-foreground/60" />
                    )}
                  </div>
                  <div className="font-semibold text-foreground text-[11px] leading-tight">
                    {node.label}
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-2">
                    {exec ? `${exec.duration_ms?.toFixed(1) || 0} ms` : "Pending"}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Workspace Quick Links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href={`/companies?research_id=${encodeURIComponent(data.research_id)}`}>
          <Card className="hover:border-primary/50 transition-all p-4 h-full flex flex-col justify-between cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Building2 className="h-4 w-4 text-primary" />
                Company Profile
              </span>
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Inspect verified business model, customer segments, and technology positioning.
            </p>
            <div className="text-[11px] font-medium text-primary mt-3">Open Workspace &rarr;</div>
          </Card>
        </Link>

        <Link href={`/competitors?research_id=${encodeURIComponent(data.research_id)}`}>
          <Card className="hover:border-primary/50 transition-all p-4 h-full flex flex-col justify-between cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Users2 className="h-4 w-4 text-emerald-600" />
                Competitors ({competitorsCount})
              </span>
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Browse qualified direct, indirect, substitute, and emerging competitor profiles.
            </p>
            <div className="text-[11px] font-medium text-emerald-600 mt-3">Open Workspace &rarr;</div>
          </Card>
        </Link>

        <Link href={`/evidence?research_id=${encodeURIComponent(data.research_id)}`}>
          <Card className="hover:border-primary/50 transition-all p-4 h-full flex flex-col justify-between cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <CheckSquare className="h-4 w-4 text-amber-600" />
                Evidence Review ({evidenceCount})
              </span>
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Verify source credibility tiers, check freshness, and resolve contradictions.
            </p>
            <div className="text-[11px] font-medium text-amber-600 mt-3">Open Workspace &rarr;</div>
          </Card>
        </Link>

        <Link href={`/strategy?research_id=${encodeURIComponent(data.research_id)}`}>
          <Card className="hover:border-primary/50 transition-all p-4 h-full flex flex-col justify-between cursor-pointer">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-violet-600" />
                Strategic Analysis
              </span>
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              SWOT matrix, competitive threats, opportunities, and prioritized recommendations.
            </p>
            <div className="text-[11px] font-medium text-violet-600 mt-3">Open Workspace &rarr;</div>
          </Card>
        </Link>
      </div>

      {/* Execution Details Card */}
      <Card>
        <CardHeader className="border-b pb-3">
          <CardTitle className="text-sm font-semibold">Execution Telemetry & Provenance</CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-muted-foreground block text-[11px]">Research ID</span>
              <span className="font-mono font-medium">{data.research_id}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Organization ID</span>
              <span className="font-mono font-medium">{data.organization_id || "default"}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Created At</span>
              <span>{data.created_at ? new Date(data.created_at).toLocaleString() : "—"}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Review Status</span>
              <Badge variant="outline" className="text-[10px] mt-0.5">
                {data.review_status || "standard"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
