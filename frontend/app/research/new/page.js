"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Search, Sparkles, AlertCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { submitResearch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert } from "@/components/ui/alert";

export default function NewResearchPage() {
  const router = useRouter();
  const { currentOrg, canCreateResearch } = useAuth();

  const [form, setForm] = useState({
    company_name: "",
    industry: "",
    research_question: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!canCreateResearch) {
    return (
      <div className="py-12 text-center max-w-md mx-auto space-y-4">
        <Alert variant="destructive" title="Unauthorized Access">
          You do not have permission to submit new research runs. An Analyst or Admin role is required.
        </Alert>
        <Link href="/research">
          <Button variant="outline" className="text-xs">
            Return to Research Listing
          </Button>
        </Link>
      </div>
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.company_name.trim() || !form.research_question.trim()) {
      setError("Target company name and research question are required.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const data = await submitResearch({
        company_name: form.company_name.trim(),
        industry: form.industry.trim() || "Technology",
        research_question: form.research_question.trim(),
      });

      if (data && data.research_id) {
        router.push(`/research/${encodeURIComponent(data.research_id)}`);
      } else {
        router.push("/research");
      }
    } catch (err) {
      setError(err.message || "Failed to initiate research execution.");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Breadcrumb Header */}
      <div className="flex items-center gap-2">
        <Link href="/research">
          <Button variant="ghost" className="h-8 px-2 text-xs gap-1 text-muted-foreground">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Projects
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Initiate Competitive Intelligence Research
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Execute multi-agent research across target company, competitors, evidence validation, and strategic analysis for <strong>{currentOrg?.name}</strong>.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" title="Submission Error">
          {error}
        </Alert>
      )}

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Search className="h-4 w-4 text-primary" />
            Research Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="company_name" className="text-xs font-medium">
                  Target Company Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="company_name"
                  placeholder="e.g. Datadog, Snowflake, Acme Corp"
                  required
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                  className="text-xs"
                />
                <p className="text-[11px] text-muted-foreground">
                  The primary organization to profile and benchmark.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="industry" className="text-xs font-medium">
                  Industry / Domain
                </Label>
                <Input
                  id="industry"
                  placeholder="e.g. Data Observability, Cloud Security, FinTech"
                  value={form.industry}
                  onChange={(e) => setForm({ ...form, industry: e.target.value })}
                  className="text-xs"
                />
                <p className="text-[11px] text-muted-foreground">
                  Helps focus candidate discovery and market overlap scoring.
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="research_question" className="text-xs font-medium">
                Research Question / Strategic Objective <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="research_question"
                rows={4}
                placeholder="e.g. How does the target company compare to direct competitors on enterprise security, pricing models, and feature roadmap?"
                required
                value={form.research_question}
                onChange={(e) => setForm({ ...form, research_question: e.target.value })}
                className="text-xs leading-relaxed"
              />
              <p className="text-[11px] text-muted-foreground">
                Framing the strategic research question guides the Planner and SWOT Analyst agents.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-muted/40 border text-xs space-y-2">
              <div className="font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-primary" />
                Pipeline Execution Steps
              </div>
              <p className="text-muted-foreground leading-relaxed">
                Submitting will trigger all 8 LangGraph nodes: Research Planner &rarr; Company Profiling &rarr; Competitor Discovery &rarr; Mathematical Evidence Validation &rarr; Strategic SWOT Synthesis &rarr; 14-Section Report Generation.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t">
              <Link href="/research">
                <Button variant="outline" type="button" className="text-xs">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={loading} className="text-xs gap-1.5">
                {loading ? (
                  <>
                    <Sparkles className="h-4 w-4 animate-spin" />
                    Executing Multi-Agent Graph…
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    Launch Research Run
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
