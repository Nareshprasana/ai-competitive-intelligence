"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  Globe,
  Tag,
  Users,
  Layers,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  Search,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch, getResearch, getOrganizationId, safeUrl } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";

function CompaniesContent() {
  const searchParams = useSearchParams();
  const initialResearchId = searchParams?.get("research_id") || "";
  const { isAuthenticated, currentOrg, currentOrgId } = useAuth();

  const [researchList, setResearchList] = useState([]);
  const [selectedId, setSelectedId] = useState(initialResearchId);
  const [currentResearch, setCurrentResearch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  // Load detail for selected research
  const loadProfile = useCallback(async () => {
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
        setError(err.message || "Failed to load company profile.");
      }
    } finally {
      if (getOrganizationId() === activeAtStart) {
        setLoading(false);
      }
    }
  }, [selectedId, currentOrgId, currentOrg]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const profile = currentResearch?.company_profile || {};
  const products = profile.products || [];
  const customers = profile.target_customers || [];
  const markets = profile.geographical_presence || [];
  const sources = profile.source_references || [];

  return (
    <div className="space-y-6">
      {/* Header & Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" />
            Company Intelligence Workspace
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Verified corporate profiling, product portfolio, customer segments, and technical positioning
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground whitespace-nowrap">Research Project:</span>
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
          <Button variant="outline" className="h-9 text-xs" onClick={loadProfile} disabled={loading}>
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
          Loading company profile…
        </div>
      ) : !currentResearch ? (
        <div className="p-12 text-center text-xs text-muted-foreground border rounded-lg bg-card">
          Select or launch a research project to inspect company intelligence.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Target Company Header Card */}
          <Card className="p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-bold tracking-tight text-foreground">
                    {profile.company_name || currentResearch.company_name}
                  </h2>
                  <Badge variant="outline" className="text-xs">
                    {profile.industry || currentResearch.industry}
                  </Badge>
                  {profile.business_model && (
                    <Badge variant="secondary" className="text-xs">
                      {profile.business_model}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed">
                  {profile.description || "Company description extracted from research sources."}
                </p>
                {profile.website && (
                  <div className="flex items-center gap-1.5 text-xs text-primary pt-1">
                    <Globe className="h-3.5 w-3.5" />
                    <a
                      href={safeUrl(profile.website)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline flex items-center gap-1"
                    >
                      {profile.website}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                )}
              </div>

              <div className="text-right shrink-0 space-y-1 text-xs">
                <div className="text-muted-foreground text-[11px]">Headquarters</div>
                <div className="font-semibold text-foreground">
                  {profile.headquarters || "Global / Distributed"}
                </div>
              </div>
            </div>
          </Card>

          {/* Grid of Key Capabilities */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Products & Services */}
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" />
                  Products & Core Offerings
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {products.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No explicit product catalog listed.</p>
                ) : (
                  <ul className="space-y-2">
                    {products.map((p, i) => (
                      <li key={i} className="text-xs flex items-center gap-2 border-b pb-2 last:border-0">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                        <span className="font-medium text-foreground">{p}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Target Customers */}
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Users className="h-4 w-4 text-emerald-600" />
                  Target Customer Segments
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {customers.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No customer segments identified.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {customers.map((c, i) => (
                      <Badge key={i} variant="outline" className="text-xs py-1 px-2.5">
                        {c}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Geographical Markets */}
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Globe className="h-4 w-4 text-sky-600" />
                  Geographic Presence
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {markets.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Global / North America default presence.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {markets.map((m, i) => (
                      <Badge key={i} variant="secondary" className="text-xs py-1 px-2.5">
                        {m}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Primary Source Citations */}
            <Card>
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-violet-600" />
                  Primary Source Citations
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {sources.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Derived from search provider snippet discovery.
                  </p>
                ) : (
                  <ul className="space-y-1.5 text-xs">
                    {sources.map((src, i) => (
                      <li key={i} className="truncate">
                        <a
                          href={safeUrl(src)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1.5"
                        >
                          <ExternalLink className="h-3 w-3 shrink-0" />
                          <span className="truncate">{src}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CompaniesPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-muted-foreground">
          Loading company workspace…
        </div>
      }
    >
      <CompaniesContent />
    </Suspense>
  );
}
