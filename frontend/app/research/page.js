"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Building2,
  Filter,
  FileText,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listResearch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";

export default function ResearchListPage() {
  const { isAuthenticated, canCreateResearch, currentOrg } = useAuth();
  const [researchList, setResearchList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const loadResearch = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const items = await listResearch({ limit: 100 });
      setResearchList(items || []);
    } catch (err) {
      setError(err.message || "Failed to load research projects.");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadResearch();
  }, [loadResearch]);

  // Client-side filtering & sorting
  const filteredItems = useMemo(() => {
    let result = [...researchList];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (r) =>
          r.company_name?.toLowerCase().includes(q) ||
          r.industry?.toLowerCase().includes(q) ||
          r.research_question?.toLowerCase().includes(q) ||
          r.research_id?.toLowerCase().includes(q)
      );
    }

    if (statusFilter !== "all") {
      result = result.filter((r) => r.status === statusFilter);
    }

    if (sortBy === "newest") {
      result.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    } else if (sortBy === "oldest") {
      result.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
    } else if (sortBy === "company") {
      result.sort((a, b) => (a.company_name || "").localeCompare(b.company_name || ""));
    }

    return result;
  }, [researchList, searchQuery, statusFilter, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, page, pageSize]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Research Projects
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage and inspect competitive intelligence research pipelines for {currentOrg?.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="h-9 text-xs gap-1.5"
            onClick={loadResearch}
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
        <Alert variant="destructive" title="Error">
          {error}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by company, industry, question, or ID…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="pl-9 h-9 text-xs"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Filter className="h-3.5 w-3.5" />
              <span>Status:</span>
            </div>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-xs"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="running">In Progress</option>
            </select>

            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-xs"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="newest">Sort: Newest First</option>
              <option value="oldest">Sort: Oldest First</option>
              <option value="company">Sort: Company Name</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Projects Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
              Loading research projects…
            </div>
          ) : paginatedItems.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <div className="p-3 rounded-full bg-muted w-fit mx-auto text-muted-foreground">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">No projects match your criteria</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                {searchQuery || statusFilter !== "all"
                  ? "Try adjusting your search query or status filter."
                  : "No research projects exist in this organization yet."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground border-b font-medium">
                  <tr>
                    <th className="py-3 px-4">Target Company</th>
                    <th className="py-3 px-4">Research Question</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Review Status</th>
                    <th className="py-3 px-4">Artifacts</th>
                    <th className="py-3 px-4">Created Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-input/50">
                  {paginatedItems.map((r) => {
                    const isSuccess = r.status === "completed";
                    const isFail = r.status === "failed";
                    const needsReview = r.review_status === "requires_review";

                    return (
                      <tr key={r.research_id} className="hover:bg-muted/30 transition-colors">
                        <td className="py-3 px-4">
                          <Link
                            href={`/research/${encodeURIComponent(r.research_id)}`}
                            className="font-semibold text-foreground hover:underline hover:text-primary block"
                          >
                            {r.company_name}
                          </Link>
                          <span className="text-[10px] text-muted-foreground">
                            {r.industry || "General Industry"}
                          </span>
                        </td>
                        <td className="py-3 px-4 max-w-sm truncate text-muted-foreground" title={r.research_question}>
                          {r.research_question}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
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
                        <td className="py-3 px-4 whitespace-nowrap">
                          {needsReview ? (
                            <Badge variant="warning" className="text-[10px] gap-1">
                              <ShieldAlert className="h-3 w-3" />
                              Needs Review
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px]">
                              {r.review_status || "Standard"}
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
                          <span>{r.competitors_count || 0} competitors</span> •{" "}
                          <span>{r.evidence_count || 0} claims</span>
                        </td>
                        <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                        </td>
                        <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                          <Link href={`/research/${encodeURIComponent(r.research_id)}`}>
                            <Button variant="outline" className="h-7 px-2.5 text-[11px]">
                              Details
                            </Button>
                          </Link>
                          {r.has_report && (
                            <Link href={`/reports?research_id=${encodeURIComponent(r.research_id)}`}>
                              <Button variant="secondary" className="h-7 px-2.5 text-[11px] gap-1">
                                <FileText className="h-3 w-3" />
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t text-xs text-muted-foreground">
              <div>
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, filteredItems.length)} of {filteredItems.length} projects
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  className="h-8 text-xs"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <span>
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  className="h-8 text-xs"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
