"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Users2,
  Globe,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Filter,
  RefreshCw,
  Search,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch, getResearch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Modal } from "@/components/ui/modal";

const TYPE_BADGES = {
  direct: { variant: "danger", label: "Direct Competitor" },
  indirect: { variant: "warning", label: "Indirect Competitor" },
  substitute: { variant: "info", label: "Substitute Solution" },
  emerging: { variant: "success", label: "Emerging Entrant" },
};

function CompetitorsContent() {
  const searchParams = useSearchParams();
  const initialResearchId = searchParams?.get("research_id") || "";
  const { isAuthenticated } = useAuth();

  const [researchList, setResearchList] = useState([]);
  const [selectedId, setSelectedId] = useState(initialResearchId);
  const [currentResearch, setCurrentResearch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState("all");
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);

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
  const loadCompetitors = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getResearch(selectedId);
      setCurrentResearch(res?.results || null);
    } catch (err) {
      setError(err.message || "Failed to load competitor data.");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadCompetitors();
  }, [loadCompetitors]);

  const rawCompetitors = currentResearch?.competitors || [];

  const filteredCompetitors = useMemo(() => {
    if (typeFilter === "all") return rawCompetitors;
    return rawCompetitors.filter((c) => c.competitor_type?.toLowerCase() === typeFilter.toLowerCase());
  }, [rawCompetitors, typeFilter]);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Users2 className="h-6 w-6 text-emerald-600" />
            Competitor Intelligence Workspace
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Evidence-qualified competitor landscape, overlap analysis, and classification benchmarks
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
          <Button variant="outline" className="h-9 text-xs" onClick={loadCompetitors} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" title="Error">
          {error}
        </Alert>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b pb-3">
        {[
          { key: "all", label: `All Competitors (${rawCompetitors.length})` },
          { key: "direct", label: "Direct" },
          { key: "indirect", label: "Indirect" },
          { key: "substitute", label: "Substitute" },
          { key: "emerging", label: "Emerging" },
        ].map((tab) => (
          <Button
            key={tab.key}
            variant={typeFilter === tab.key ? "default" : "outline"}
            className="h-8 px-3 text-xs capitalize"
            onClick={() => setTypeFilter(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
          Loading competitor profiles…
        </div>
      ) : filteredCompetitors.length === 0 ? (
        <div className="p-12 text-center text-xs text-muted-foreground border rounded-lg bg-card">
          No competitors found matching category filter "{typeFilter}".
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCompetitors.map((comp, idx) => {
            const typeInfo = TYPE_BADGES[comp.competitor_type?.toLowerCase()] || {
              variant: "outline",
              label: comp.competitor_type || "Competitor",
            };
            const scorePercent = Math.round((comp.qualification_score || 0) * 100);

            return (
              <Card
                key={comp.competitor_id || idx}
                className="flex flex-col justify-between hover:border-primary/50 transition-all shadow-xs"
              >
                <CardHeader className="pb-3 border-b">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CardTitle className="text-base font-bold text-foreground">
                        {comp.company_name}
                      </CardTitle>
                      {comp.website && (
                        <a
                          href={comp.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-primary hover:underline flex items-center gap-1 mt-0.5"
                        >
                          <Globe className="h-3 w-3" />
                          <span className="truncate max-w-[180px]">{comp.website}</span>
                        </a>
                      )}
                    </div>
                    <Badge variant={typeInfo.variant} className="text-[10px] shrink-0">
                      {typeInfo.label}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="pt-3 flex-1 flex flex-col justify-between space-y-3 text-xs">
                  <p className="text-muted-foreground line-clamp-3 leading-relaxed">
                    {comp.company_description || comp.overlap_explanation || "No description available."}
                  </p>

                  <div className="space-y-2 pt-2 border-t">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-muted-foreground">Qualification Score:</span>
                      <span className="font-semibold text-foreground">{scorePercent}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-primary h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, Math.max(5, scorePercent))}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-[11px] text-muted-foreground">
                      {(comp.evidence || []).length} supporting citations
                    </span>
                    <Button
                      variant="outline"
                      className="h-7 px-2.5 text-[11px]"
                      onClick={() => setSelectedCompetitor(comp)}
                    >
                      Inspect Evidence &rarr;
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Competitor Evidence Modal */}
      {selectedCompetitor && (
        <Modal
          isOpen={Boolean(selectedCompetitor)}
          onClose={() => setSelectedCompetitor(null)}
          title={selectedCompetitor.company_name}
          description={`Competitor Classification: ${selectedCompetitor.competitor_type} • Score: ${Math.round(
            (selectedCompetitor.qualification_score || 0) * 100
          )}%`}
        >
          <div className="space-y-4 text-xs">
            <div>
              <h4 className="font-semibold text-foreground mb-1">Market Overlap Rationale</h4>
              <p className="text-muted-foreground bg-muted/40 p-3 rounded-md leading-relaxed">
                {selectedCompetitor.overlap_explanation || "Overlap deduced from search results and industry alignment."}
              </p>
            </div>

            {selectedCompetitor.products_and_services?.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground mb-1">Key Products & Services</h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCompetitor.products_and_services.map((p, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {p}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h4 className="font-semibold text-foreground mb-2">Supporting Evidence Claims</h4>
              {(selectedCompetitor.evidence || []).length === 0 ? (
                <p className="text-muted-foreground">No explicit citations recorded.</p>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {selectedCompetitor.evidence.map((ev, i) => (
                    <div key={i} className="p-3 rounded border bg-card space-y-1">
                      <div className="font-medium text-foreground">&ldquo;{ev.claim}&rdquo;</div>
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                        <span className="truncate max-w-sm">{ev.source_domain || ev.source_title}</span>
                        {ev.source_url && (
                          <a
                            href={ev.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            Source link <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default function CompetitorsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-muted-foreground">
          Loading competitor workspace…
        </div>
      }
    >
      <CompetitorsContent />
    </Suspense>
  );
}
