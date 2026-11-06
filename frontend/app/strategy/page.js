"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  TrendingUp,
  Shield,
  Target,
  Zap,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Clock,
  Layers,
  RefreshCw,
  Search,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch, getResearch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";

const TIME_HORIZON_LABELS = {
  immediate: "Immediate (0–30 days)",
  near_term: "Short term (1–3 months)",
  short_term: "Short term (1–3 months)",
  medium_term: "Medium term (3–6 months)",
  long_term: "Long term (6–12 months)",
};

function StrategyContent() {
  const searchParams = useSearchParams();
  const initialResearchId = searchParams?.get("research_id") || "";
  const { isAuthenticated } = useAuth();

  const [researchList, setResearchList] = useState([]);
  const [selectedId, setSelectedId] = useState(initialResearchId);
  const [currentResearch, setCurrentResearch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load available research runs
  useEffect(() => {
    if (!isAuthenticated) return;
    listResearch({ limit: 50 }).then((items) => {
      setResearchList(items || []);
      if (!selectedId && items && items.length > 0) {
        setSelectedId(items[0].research_id);
      }
    });
  }, [isAuthenticated, selectedId]);

  // Load research detail
  const loadStrategy = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getResearch(selectedId);
      setCurrentResearch(res?.results || null);
    } catch (err) {
      setError(err.message || "Failed to load strategic analysis data.");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadStrategy();
  }, [loadStrategy]);

  const strat = currentResearch?.strategic_analysis || {};
  const swot = strat.swot_analysis || {};
  const strengths = swot.strengths || [];
  const weaknesses = swot.weaknesses || [];
  const swotOpportunities = swot.opportunities || [];
  const swotThreats = swot.threats || [];

  const marketOpportunities = strat.market_opportunities || [];
  const competitiveThreats = strat.competitive_threats || [];
  const recommendations = strat.strategic_recommendations || [];
  const competitors = currentResearch?.competitors || [];

  // Group recommendations by canonical time horizon
  const groupedRecs = useMemo(() => {
    const groups = {
      immediate: [],
      short_term: [],
      medium_term: [],
      long_term: [],
    };
    recommendations.forEach((rec) => {
      let h = (rec.time_horizon || "medium_term").toLowerCase();
      if (h === "near_term") h = "short_term";
      if (!groups[h]) groups[h] = [];
      groups[h].push(rec);
    });
    return groups;
  }, [recommendations]);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-violet-600" />
            Strategic Analysis Workspace
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            SWOT synthesis, market opportunities, competitive threats, and prioritized action plan
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground whitespace-nowrap">Project:</span>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-xs font-medium"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {researchList.map((r) => (
              <option key={r.research_id} value={r.research_id}>
                {r.company_name} ({r.industry || "General"})
              </option>
            ))}
          </select>
          <Button variant="outline" className="h-9 text-xs" onClick={loadStrategy} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" title="Error">
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
          Synthesizing strategic analysis models…
        </div>
      ) : !currentResearch ? (
        <div className="p-12 text-center text-xs text-muted-foreground border rounded-lg bg-card">
          Select or launch a research project to inspect strategic analysis.
        </div>
      ) : (
        <div className="space-y-6">
          {/* SWOT Grid */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* Strengths */}
            <Card className="border-emerald-200 dark:border-emerald-900/40">
              <CardHeader className="bg-emerald-50/50 dark:bg-emerald-950/20 border-b pb-3">
                <CardTitle className="text-sm font-bold text-emerald-800 dark:text-emerald-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle className="h-4 w-4" />
                    Strengths ({strengths.length})
                  </span>
                  <Badge variant="success" className="text-[10px]">Internal Advantage</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                {strengths.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No explicit strengths recorded.</p>
                ) : (
                  strengths.map((item, i) => (
                    <div key={i} className="p-3 rounded-lg border bg-card text-xs space-y-1">
                      <div className="font-semibold text-foreground">{item.point || item}</div>
                      {item.evidence_references?.length > 0 && (
                        <div className="text-[10px] text-muted-foreground">
                          Evidence: {item.evidence_references.join(", ")}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Weaknesses */}
            <Card className="border-amber-200 dark:border-amber-900/40">
              <CardHeader className="bg-amber-50/50 dark:bg-amber-950/20 border-b pb-3">
                <CardTitle className="text-sm font-bold text-amber-800 dark:text-amber-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <AlertTriangle className="h-4 w-4" />
                    Weaknesses ({weaknesses.length})
                  </span>
                  <Badge variant="warning" className="text-[10px]">Internal Constraint</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                {weaknesses.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No weaknesses recorded.</p>
                ) : (
                  weaknesses.map((item, i) => (
                    <div key={i} className="p-3 rounded-lg border bg-card text-xs space-y-1">
                      <div className="font-semibold text-foreground">{item.point || item}</div>
                      {item.evidence_references?.length > 0 && (
                        <div className="text-[10px] text-muted-foreground">
                          Evidence: {item.evidence_references.join(", ")}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Opportunities */}
            <Card className="border-sky-200 dark:border-sky-900/40">
              <CardHeader className="bg-sky-50/50 dark:bg-sky-950/20 border-b pb-3">
                <CardTitle className="text-sm font-bold text-sky-800 dark:text-sky-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Target className="h-4 w-4" />
                    Opportunities ({swotOpportunities.length})
                  </span>
                  <Badge variant="info" className="text-[10px]">Market Potential</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                {swotOpportunities.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No market opportunities recorded.</p>
                ) : (
                  swotOpportunities.map((item, i) => (
                    <div key={i} className="p-3 rounded-lg border bg-card text-xs space-y-1">
                      <div className="font-semibold text-foreground">{item.point || item}</div>
                      {item.evidence_references?.length > 0 && (
                        <div className="text-[10px] text-muted-foreground">
                          Evidence: {item.evidence_references.join(", ")}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Threats */}
            <Card className="border-rose-200 dark:border-rose-900/40">
              <CardHeader className="bg-rose-50/50 dark:bg-rose-950/20 border-b pb-3">
                <CardTitle className="text-sm font-bold text-rose-800 dark:text-rose-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Shield className="h-4 w-4" />
                    Threats ({swotThreats.length})
                  </span>
                  <Badge variant="danger" className="text-[10px]">Competitive Risk</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                {swotThreats.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No competitive threats recorded.</p>
                ) : (
                  swotThreats.map((item, i) => (
                    <div key={i} className="p-3 rounded-lg border bg-card text-xs space-y-1">
                      <div className="font-semibold text-foreground">{item.point || item}</div>
                      {item.evidence_references?.length > 0 && (
                        <div className="text-[10px] text-muted-foreground">
                          Evidence: {item.evidence_references.join(", ")}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Strategic Recommendations by Normalized Time Horizon */}
          <Card>
            <CardHeader className="border-b pb-4">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                Strategic Recommendations & Action Plan
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Actionable recommendations categorized across standardized 0–30 days, 1–3 months, 3–6 months, and 6–12 months timelines
              </p>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {[
                { key: "immediate", title: "Immediate (0–30 days)", color: "text-rose-600" },
                { key: "short_term", title: "Short term (1–3 months)", color: "text-amber-600" },
                { key: "medium_term", title: "Medium term (3–6 months)", color: "text-sky-600" },
                { key: "long_term", title: "Long term (6–12 months)", color: "text-emerald-600" },
              ].map(({ key, title, color }) => {
                const recs = groupedRecs[key] || [];
                return (
                  <div key={key} className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Clock className={`h-4 w-4 ${color}`} />
                      <h4 className="font-bold text-xs uppercase tracking-wider text-foreground">
                        {title}
                      </h4>
                      <span className="text-[11px] text-muted-foreground">({recs.length})</span>
                    </div>

                    {recs.length === 0 ? (
                      <p className="text-xs text-muted-foreground italic pl-6">
                        No recommendations formulated for this horizon.
                      </p>
                    ) : (
                      <div className="grid gap-3 sm:grid-cols-2 pl-2">
                        {recs.map((rec, idx) => (
                          <div
                            key={idx}
                            className="p-4 rounded-lg border bg-card space-y-2 text-xs shadow-xs"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <h5 className="font-bold text-foreground text-sm leading-tight">
                                {rec.recommendation || rec.title}
                              </h5>
                              <Badge variant="outline" className="text-[10px] uppercase">
                                {rec.priority || "Medium"} Priority
                              </Badge>
                            </div>
                            <p className="text-muted-foreground leading-relaxed">
                              {rec.description || rec.objective || rec.rationale}
                            </p>
                            {rec.expected_impact && (
                              <div className="text-[11px] text-primary font-medium pt-1">
                                Expected Impact: {rec.expected_impact}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default function StrategyPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-muted-foreground">
          Loading strategic workspace…
        </div>
      }
    >
      <StrategyContent />
    </Suspense>
  );
}
