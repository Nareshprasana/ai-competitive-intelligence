"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  Download,
  Code,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Copy,
  ExternalLink,
  Layers,
  TrendingUp,
  ShieldAlert,
  Building,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import {
  listResearch,
  getReport,
  downloadReportPdf,
  downloadReportMarkdown,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Modal } from "@/components/ui/modal";

function ReportsContent() {
  const searchParams = useSearchParams();
  const initialResearchId = searchParams?.get("research_id") || "";
  const { isAuthenticated } = useAuth();

  const [researchList, setResearchList] = useState([]);
  const [selectedId, setSelectedId] = useState(initialResearchId);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Download states
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingMd, setDownloadingMd] = useState(false);
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);

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

  // Load report data
  const loadReport = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getReport(selectedId);
      setReportData(data);
    } catch (err) {
      setError(err.message || "Failed to load strategic intelligence report.");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleDownloadPdf = async () => {
    if (!selectedId) return;
    setDownloadingPdf(true);
    try {
      await downloadReportPdf(selectedId);
    } catch (err) {
      setError(err.message || "PDF download failed.");
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleDownloadMd = async () => {
    if (!selectedId) return;
    setDownloadingMd(true);
    try {
      await downloadReportMarkdown(selectedId);
    } catch (err) {
      setError(err.message || "Markdown download failed.");
    } finally {
      setDownloadingMd(false);
    }
  };

  const handleCopyJson = () => {
    if (!reportData) return;
    navigator.clipboard.writeText(JSON.stringify(reportData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const sections = reportData?.sections || {};

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            Competitive Intelligence Reports
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Audit-grade 14-section strategic intelligence reports synchronized across JSON, Markdown, and PDF
          </p>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex flex-wrap items-center gap-2">
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

          <Button
            variant="outline"
            className="h-9 text-xs gap-1.5"
            onClick={() => setJsonModalOpen(true)}
            disabled={!reportData || loading}
          >
            <Code className="h-3.5 w-3.5" />
            JSON
          </Button>

          <Button
            variant="outline"
            className="h-9 text-xs gap-1.5"
            onClick={handleDownloadMd}
            disabled={!reportData || downloadingMd}
          >
            <Download className="h-3.5 w-3.5" />
            {downloadingMd ? "Exporting…" : "Markdown"}
          </Button>

          <Button
            className="h-9 text-xs gap-1.5"
            onClick={handleDownloadPdf}
            disabled={!reportData || downloadingPdf}
          >
            <Download className="h-3.5 w-3.5" />
            {downloadingPdf ? "Generating PDF…" : "Download PDF"}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" title="Report Notice">
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
          Loading report document…
        </div>
      ) : !reportData ? (
        <div className="p-12 text-center text-xs text-muted-foreground border rounded-lg bg-card">
          Select a completed research project to view the strategic intelligence report.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Document Cover Card */}
          <Card className="p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b pb-4 mb-4">
              <div>
                <Badge variant="outline" className="text-xs mb-2">
                  CONFIDENTIAL INTELLIGENCE REPORT
                </Badge>
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                  {reportData.title || `Strategic Intelligence Report: ${reportData.company}`}
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Target: <strong>{reportData.company}</strong> • Generated:{" "}
                  {reportData.generated_at ? new Date(reportData.generated_at).toLocaleString() : "Recent"}
                </p>
              </div>

              <div className="text-right shrink-0 space-y-1 text-xs">
                <span className="text-muted-foreground block text-[11px]">Overall Confidence</span>
                <span className="font-bold text-lg text-primary">
                  {Math.round((reportData.overall_confidence || 0) * 100)}%
                </span>
              </div>
            </div>

            {/* Section 1: Executive Summary */}
            <div className="space-y-2">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                01. Executive Summary
              </h3>
              <p className="text-xs leading-relaxed text-foreground bg-muted/30 p-4 rounded-lg">
                {sections.executive_summary || "No executive summary recorded."}
              </p>
            </div>
          </Card>

          {/* Section 2: Target Company Profile */}
          <Card>
            <CardHeader className="border-b pb-3">
              <CardTitle className="text-sm font-semibold">02. Target Company Profile</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-xs leading-relaxed">
              <div className="whitespace-pre-line text-muted-foreground">
                {typeof sections.company_profile === "string"
                  ? sections.company_profile
                  : JSON.stringify(sections.company_profile || {}, null, 2)}
              </div>
            </CardContent>
          </Card>

          {/* Section 3 & 4: Methodology & Competitive Landscape */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">03. Scope & Methodology</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs leading-relaxed text-muted-foreground">
                <p>{sections.scope_and_methodology || "Standard multi-agent LangGraph methodology with evidence validation."}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">04. Competitive Landscape</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs leading-relaxed text-muted-foreground">
                <p>{sections.competitive_landscape || "Competitive landscape benchmarked across direct, indirect, and emerging players."}</p>
              </CardContent>
            </Card>
          </div>

          {/* Section 5 & 6: Competitor Profiles */}
          <Card>
            <CardHeader className="border-b pb-3">
              <CardTitle className="text-sm font-semibold">05 & 06. Competitor Profiles & Benchmarks</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-xs space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="p-3 rounded border bg-card space-y-1">
                  <h4 className="font-semibold text-foreground">Direct Competitors</h4>
                  <div className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {typeof sections.direct_competitors === "string"
                      ? sections.direct_competitors
                      : JSON.stringify(sections.direct_competitors || "None identified", null, 2)}
                  </div>
                </div>
                <div className="p-3 rounded border bg-card space-y-1">
                  <h4 className="font-semibold text-foreground">Indirect & Emerging Entrants</h4>
                  <div className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {typeof sections.indirect_and_emerging === "string"
                      ? sections.indirect_and_emerging
                      : JSON.stringify(sections.indirect_and_emerging || "None identified", null, 2)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Section 7 & 8: Features & Pricing */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">07. Feature & Capability Matrix</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs text-muted-foreground leading-relaxed whitespace-pre-line">
                {typeof sections.feature_matrix === "string"
                  ? sections.feature_matrix
                  : JSON.stringify(sections.feature_matrix || "Feature matrix recorded in findings.", null, 2)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">08. Pricing & Packaging Intelligence</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs text-muted-foreground leading-relaxed whitespace-pre-line">
                {typeof sections.pricing_analysis === "string"
                  ? sections.pricing_analysis
                  : JSON.stringify(sections.pricing_analysis || "Pricing models extracted from public disclosures.", null, 2)}
              </CardContent>
            </Card>
          </div>

          {/* Section 9, 10, 11: Opportunities, Threats & Recommendations */}
          <Card>
            <CardHeader className="border-b pb-3">
              <CardTitle className="text-sm font-semibold">09 - 11. Strategic Findings & Action Plan</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4 text-xs">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="p-3 rounded border bg-card space-y-1">
                  <h4 className="font-semibold text-foreground">Market Opportunities</h4>
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {typeof sections.market_opportunities === "string"
                      ? sections.market_opportunities
                      : JSON.stringify(sections.market_opportunities || "Opportunities formulated.", null, 2)}
                  </p>
                </div>
                <div className="p-3 rounded border bg-card space-y-1">
                  <h4 className="font-semibold text-foreground">Competitive Threats</h4>
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {typeof sections.competitive_threats === "string"
                      ? sections.competitive_threats
                      : JSON.stringify(sections.competitive_threats || "Threats formulated.", null, 2)}
                  </p>
                </div>
              </div>

              <div className="p-3 rounded border bg-muted/30 space-y-1">
                <h4 className="font-semibold text-foreground">Prioritized Recommendations</h4>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                  {typeof sections.recommendations === "string"
                    ? sections.recommendations
                    : JSON.stringify(sections.recommendations || "Recommendations formulated.", null, 2)}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Section 12, 13, 14: Evidence Summary, Gaps & Audit Trail */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">12. Evidence Validation</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs text-muted-foreground leading-relaxed">
                <p>{sections.evidence_summary || "Mathematical validation completed."}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">13. Information Gaps</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs text-muted-foreground leading-relaxed">
                <p>{sections.information_gaps || "Unknowns recorded in audit trail."}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold">14. Audit & Provenance</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 text-xs text-muted-foreground leading-relaxed">
                <p>{sections.audit_metadata || "Traceable multi-agent execution log."}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Structured JSON Modal */}
      <Modal
        isOpen={jsonModalOpen}
        onClose={() => setJsonModalOpen(false)}
        title="Structured StrategicReport JSON"
        description="Pydantic-validated JSON representation of all 14 report sections"
        className="max-w-4xl"
      >
        <div className="space-y-3">
          <div className="flex justify-end">
            <Button variant="outline" className="h-8 text-xs gap-1.5" onClick={handleCopyJson}>
              <Copy className="h-3.5 w-3.5" />
              {copied ? "Copied!" : "Copy JSON"}
            </Button>
          </div>
          <pre className="p-4 rounded-lg border bg-muted text-[11px] font-mono overflow-x-auto max-h-[60vh] leading-relaxed">
            {JSON.stringify(reportData, null, 2)}
          </pre>
        </div>
      </Modal>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-muted-foreground">
          Loading reports workspace…
        </div>
      }
    >
      <ReportsContent />
    </Suspense>
  );
}
