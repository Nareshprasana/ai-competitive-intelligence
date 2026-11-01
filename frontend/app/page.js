"use client";

import { useState, useEffect, useCallback } from "react";
import ResearchForm from "@/components/ResearchForm";
import ReportDisplay from "@/components/ReportDisplay";
import { getResearch, health } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  const [healthOk, setHealthOk] = useState(null);
  const [researchId, setResearchId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    health()
      .then(() => setHealthOk(true))
      .catch(() => setHealthOk(false));
  }, []);

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
        <Card>
          <CardHeader>
            <CardTitle>New Research</CardTitle>
          </Card>
        </Card>
        <ResearchForm onSubmit={handleSubmit} />
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
