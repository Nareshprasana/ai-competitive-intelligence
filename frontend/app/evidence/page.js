"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  CheckSquare,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ExternalLink,
  Filter,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch, getResearch, reviewEvidence, getOrganizationId, safeUrl } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Modal } from "@/components/ui/modal";

const STATUS_BADGES = {
  approved: { variant: "success", label: "Approved" },
  verified: { variant: "success", label: "Verified" },
  partially_verified: { variant: "info", label: "Partially Verified" },
  unverified: { variant: "outline", label: "Unverified" },
  flagged: { variant: "warning", label: "Flagged" },
  contradicted: { variant: "danger", label: "Contradicted" },
  stale: { variant: "warning", label: "Stale Data" },
  rejected: { variant: "danger", label: "Rejected" },
};

function EvidenceContent() {
  const searchParams = useSearchParams();
  const initialResearchId = searchParams?.get("research_id") || "";
  const { isAuthenticated, canManageEvidence, currentOrg, currentOrgId } = useAuth();

  const [researchList, setResearchList] = useState([]);
  const [selectedId, setSelectedId] = useState(initialResearchId);
  const [currentResearch, setCurrentResearch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeEvidence, setActiveEvidence] = useState(null);

  // Review action form state
  const [reviewDecision, setReviewDecision] = useState("approved");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewConfidence, setReviewConfidence] = useState(0.85);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState(null);

  // Load available research runs
  useEffect(() => {
    if (!isAuthenticated) return;
    const activeAtStart = currentOrgId || currentOrg?.organization_id;
    listResearch({ limit: 50 }).then((items) => {
      if (getOrganizationId() === activeAtStart) {
        setResearchList(items || []);
        if (!selectedId && items && items.length > 0) {
          setSelectedId(items[0].research_id);
        }
      }
    });
  }, [isAuthenticated, selectedId, currentOrgId, currentOrg]);

  // Load research detail
  const loadResearchDetail = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    const activeAtStart = currentOrgId || currentOrg?.organization_id;
    try {
      const res = await getResearch(selectedId);
      if (getOrganizationId() === activeAtStart) {
        setCurrentResearch(res?.results || null);
      }
    } catch (err) {
      if (getOrganizationId() === activeAtStart) {
        setError(err.message || "Failed to load evidence records.");
      }
    } finally {
      if (getOrganizationId() === activeAtStart) {
        setLoading(false);
      }
    }
  }, [selectedId, currentOrgId, currentOrg]);

  useEffect(() => {
    loadResearchDetail();
  }, [loadResearchDetail]);

  const rawEvidence = currentResearch?.evidence || [];
  const validationResults = currentResearch?.validation_results || {};
  const contradictions = validationResults.contradictions || [];

  // Filter evidence
  const filteredEvidence = useMemo(() => {
    return rawEvidence.filter((item) => {
      if (statusFilter !== "all" && item.verification_status !== statusFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          item.claim?.toLowerCase().includes(q) ||
          item.source_domain?.toLowerCase().includes(q) ||
          item.source_title?.toLowerCase().includes(q) ||
          item.evidence_id?.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [rawEvidence, statusFilter, searchQuery]);

  // Open modal for review
  const handleOpenReview = (ev) => {
    setActiveEvidence(ev);
    setReviewDecision(ev.verification_status || "verified");
    setReviewNotes(ev.human_review?.analyst_notes || "");
    setReviewConfidence(ev.confidence || 0.85);
    setReviewSuccess(null);
  };

  // Submit human review decision
  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!activeEvidence || !selectedId) return;
    setReviewLoading(true);
    try {
      const res = await reviewEvidence(selectedId, activeEvidence.evidence_id, {
        decision: reviewDecision,
        analyst_notes: reviewNotes,
        override_confidence: parseFloat(reviewConfidence),
      });

      // Update local state
      setActiveEvidence((prev) => ({
        ...prev,
        verification_status: res.verification_status,
        confidence: res.confidence,
        human_review: res.human_review,
      }));

      // Refresh parent dataset
      await loadResearchDetail();
      setReviewSuccess("Review decision recorded successfully.");
      setTimeout(() => {
        setReviewSuccess(null);
        setActiveEvidence(null);
      }, 1200);
    } catch (err) {
      setError(err.message || "Failed to submit review decision.");
    } finally {
      setReviewLoading(false);
    }
  };

  // Metric counts
  const countVerified = rawEvidence.filter((e) => e.verification_status === "verified").length;
  const countPartially = rawEvidence.filter((e) => e.verification_status === "partially_verified").length;
  const countContradicted = rawEvidence.filter((e) => e.verification_status === "contradicted").length;
  const countStale = rawEvidence.filter((e) => e.verification_status === "stale").length;

  return (
    <div className="space-y-6">
      {/* Header & Project Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <CheckSquare className="h-6 w-6 text-amber-600" />
            Evidence Review Workspace
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Audit evidence claims, inspect contradictions, evaluate credibility tiers, and record human review decisions
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
          <Button variant="outline" className="h-9 text-xs" onClick={loadResearchDetail} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" title="Error">
          {error}
        </Alert>
      )}

      {/* Prominent Contradiction Warning Banner */}
      {contradictions.length > 0 && (
        <Alert variant="warning" title="Cross-Source Contradictions Detected">
          <p className="mb-2">
            Automated mathematical validation discovered <strong>{contradictions.length}</strong> contradicting factual claims across independent sources:
          </p>
          <div className="space-y-2 mt-2">
            {contradictions.map((c, i) => (
              <div key={i} className="p-3 rounded bg-amber-100/50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs space-y-1">
                <div className="font-semibold text-foreground">
                  Conflict Topic: {c.topic || "Factual Claim Conflict"}
                </div>
                <div className="grid sm:grid-cols-2 gap-2 text-muted-foreground pt-1">
                  <div className="p-2 rounded bg-background/80 border">
                    <span className="font-medium text-foreground block">Source Claim A:</span>
                    &ldquo;{c.claim_a}&rdquo;
                  </div>
                  <div className="p-2 rounded bg-background/80 border">
                    <span className="font-medium text-foreground block">Conflicting Claim B:</span>
                    &ldquo;{c.claim_b}&rdquo;
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Alert>
      )}

      {/* Metrics Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-3 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Total Claims</div>
            <div className="text-xl font-bold mt-0.5 text-foreground">{rawEvidence.length}</div>
          </div>
          <Badge variant="outline" className="text-xs">All</Badge>
        </Card>
        <Card className="p-3 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-emerald-600 font-semibold">Verified</div>
            <div className="text-xl font-bold mt-0.5 text-emerald-600">{countVerified}</div>
          </div>
          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
        </Card>
        <Card className="p-3 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-rose-600 font-semibold">Contradicted</div>
            <div className="text-xl font-bold mt-0.5 text-rose-600">{countContradicted}</div>
          </div>
          <AlertTriangle className="h-5 w-5 text-rose-500" />
        </Card>
        <Card className="p-3 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-amber-600 font-semibold">Stale Claims</div>
            <div className="text-xl font-bold mt-0.5 text-amber-600">{countStale}</div>
          </div>
          <Clock className="h-5 w-5 text-amber-500" />
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search claims, domains, or evidence IDs…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-xs text-muted-foreground whitespace-nowrap">Status:</span>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-xs"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Verification Statuses</option>
              <option value="verified">Verified</option>
              <option value="partially_verified">Partially Verified</option>
              <option value="unverified">Unverified</option>
              <option value="contradicted">Contradicted</option>
              <option value="stale">Stale</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Evidence Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-16 text-center text-xs text-muted-foreground">
              <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
              Loading evidence claims…
            </div>
          ) : filteredEvidence.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground border rounded-lg bg-card">
              No evidence claims found matching filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                  <tr>
                    <th className="py-3 px-4">Claim</th>
                    <th className="py-3 px-4">Source / Domain</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4">Dates</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-input/50">
                  {filteredEvidence.map((ev, i) => {
                    const statusInfo = STATUS_BADGES[ev.verification_status?.toLowerCase()] || {
                      variant: "outline",
                      label: ev.verification_status || "Unknown",
                    };
                    const confPercent = Math.round((ev.confidence || 0) * 100);

                    return (
                      <tr key={ev.evidence_id || i} className="hover:bg-muted/30 transition-colors">
                        <td className="py-3 px-4 max-w-md">
                          <div className="font-medium text-foreground line-clamp-2 leading-relaxed">
                            &ldquo;{ev.claim}&rdquo;
                          </div>
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {ev.evidence_id}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <div className="font-medium text-foreground">{ev.source_domain || "Web Source"}</div>
                          {ev.source_url && (
                            <a
                              href={safeUrl(ev.source_url)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[11px] text-primary hover:underline flex items-center gap-1"
                            >
                              <ExternalLink className="h-3 w-3" />
                              <span className="truncate max-w-[140px]">{ev.source_url}</span>
                            </a>
                          )}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <Badge variant={statusInfo.variant} className="text-[10px]">
                            {statusInfo.label}
                          </Badge>
                          {ev.human_review && (
                            <span className="block text-[9px] text-primary font-medium mt-0.5">
                              Human Reviewed
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-muted rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-1.5 rounded-full ${
                                  confPercent >= 70 ? "bg-emerald-500" : confPercent >= 40 ? "bg-amber-500" : "bg-rose-500"
                                }`}
                                style={{ width: `${confPercent}%` }}
                              />
                            </div>
                            <span className="font-semibold text-foreground text-[11px]">{confPercent}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-muted-foreground whitespace-nowrap text-[11px]">
                          <div>Pub: {ev.published_at ? new Date(ev.published_at).toLocaleDateString() : "—"}</div>
                          <div>Ret: {ev.retrieved_at ? new Date(ev.retrieved_at).toLocaleDateString() : "Recent"}</div>
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          <Button
                            variant="outline"
                            className="h-7 px-2.5 text-[11px]"
                            onClick={() => handleOpenReview(ev)}
                          >
                            Review &rarr;
                          </Button>
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

      {/* Human Review Modal / Drawer */}
      {activeEvidence && (
        <Modal
          isOpen={Boolean(activeEvidence)}
          onClose={() => setActiveEvidence(null)}
          title="Evidence Claim Review"
          description={`Evidence ID: ${activeEvidence.evidence_id} • Target: ${currentResearch?.company_name}`}
        >
          <div className="space-y-4 text-xs">
            {reviewSuccess && (
              <Alert variant="success" title="Success">
                {reviewSuccess}
              </Alert>
            )}

            <div className="p-3 rounded-lg border bg-muted/30 space-y-2">
              <div className="font-semibold text-foreground text-sm">
                &ldquo;{activeEvidence.claim}&rdquo;
              </div>
              <div className="flex flex-wrap items-center gap-3 text-muted-foreground text-[11px]">
                <span>
                  Source: <strong>{activeEvidence.source_domain || activeEvidence.source_title}</strong>
                </span>
                {activeEvidence.source_url && (
                  <a
                    href={safeUrl(activeEvidence.source_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline flex items-center gap-1"
                  >
                    Open Source Link <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Machine Validation Status Preservation */}
            <div className="grid sm:grid-cols-2 gap-3 p-3 rounded-md border text-[11px] bg-muted/20">
              <div>
                <span className="text-muted-foreground block font-medium">Machine Validation Status:</span>
                <span className="font-semibold text-foreground">
                  {activeEvidence.machine_verification_status || activeEvidence.verification_status}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground block font-medium">Machine Confidence Score:</span>
                <span className="font-semibold text-foreground">
                  {Math.round((activeEvidence.machine_confidence ?? activeEvidence.confidence ?? 0) * 100)}%
                </span>
              </div>
              {(activeEvidence.machine_explanation || activeEvidence.explanation) && (
                <div className="sm:col-span-2 pt-1 border-t text-muted-foreground">
                  <span className="font-medium text-foreground block">Machine Explanation:</span>
                  {activeEvidence.machine_explanation || activeEvidence.explanation}
                </div>
              )}
            </div>

            {/* Human Review Audit History (if already reviewed) */}
            {activeEvidence.human_review && (
              <div className="p-3 rounded-md border text-[11px] bg-amber-500/5 border-amber-500/20 space-y-1">
                <span className="font-semibold text-foreground block">Recorded Human Review:</span>
                <div className="grid sm:grid-cols-2 gap-2 text-muted-foreground">
                  <div>
                    <span className="font-medium text-foreground">Decision: </span>
                    <Badge variant={STATUS_BADGES[activeEvidence.human_review.decision]?.variant || "secondary"} className="text-[10px]">
                      {STATUS_BADGES[activeEvidence.human_review.decision]?.label || activeEvidence.human_review.decision}
                    </Badge>
                  </div>
                  <div>
                    <span className="font-medium text-foreground">Reviewer: </span>
                    {activeEvidence.human_review.reviewed_by}
                  </div>
                  <div className="sm:col-span-2">
                    <span className="font-medium text-foreground">Timestamp: </span>
                    {new Date(activeEvidence.human_review.reviewed_at).toLocaleString()}
                  </div>
                  {activeEvidence.human_review.analyst_notes && (
                    <div className="sm:col-span-2">
                      <span className="font-medium text-foreground">Notes: </span>
                      &ldquo;{activeEvidence.human_review.analyst_notes}&rdquo;
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analyst Decision Form */}
            {canManageEvidence ? (
              <form onSubmit={handleSubmitReview} className="space-y-3 pt-2 border-t">
                <div className="space-y-1.5">
                  <label className="font-semibold text-foreground block">Human Review Decision</label>
                  <select
                    className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs"
                    value={reviewDecision}
                    onChange={(e) => setReviewDecision(e.target.value)}
                  >
                    <option value="approved">Approved (Verified by Analyst)</option>
                    <option value="rejected">Rejected (Invalid / False Claim)</option>
                    <option value="flagged">Flagged (Contradicted / Requires Further Review)</option>
                    <option value="partially_verified">Partially Verified (Single Source)</option>
                    <option value="unverified">Unverified (Insufficient Evidence)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-foreground block">Analyst Rationale / Notes</label>
                  <Textarea
                    rows={3}
                    placeholder="Provide evidence confirmation or reasoning for the decision…"
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="font-semibold text-foreground">Confidence Score Override</label>
                    <span className="font-mono text-primary font-bold">
                      {Math.round(reviewConfidence * 100)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={reviewConfidence}
                    onChange={(e) => setReviewConfidence(parseFloat(e.target.value))}
                    className="w-full accent-primary"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t">
                  <Button
                    variant="outline"
                    type="button"
                    className="text-xs"
                    onClick={() => setActiveEvidence(null)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={reviewLoading} className="text-xs gap-1.5">
                    {reviewLoading ? "Saving…" : "Save Review Decision"}
                  </Button>
                </div>
              </form>
            ) : (
              <p className="text-muted-foreground text-center py-2">
                Analyst or Admin permissions required to submit human review decisions.
              </p>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-muted-foreground">
          Loading evidence workspace…
        </div>
      }
    >
      <EvidenceContent />
    </Suspense>
  );
}
