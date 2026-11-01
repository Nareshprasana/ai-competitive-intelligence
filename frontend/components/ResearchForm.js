"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { submitResearch } from "@/lib/api";

export default function ResearchForm({ onSubmit }) {
  const [form, setForm] = useState({
    company_name: "",
    industry: "",
    research_question: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await submitResearch(form);
      setSubmitted(data);
      if (onSubmit) onSubmit(data);
    } catch (err) {
      setError(err.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Submit Research</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="company_name">Company name</Label>
            <Input
              id="company_name"
              placeholder="e.g. Acme Corp"
              required
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="industry">Industry</Label>
            <Input
              id="industry"
              placeholder="e.g. AI Software"
              required
              value={form.industry}
              onChange={(e) => setForm({ ...form, industry: e.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="research_question">Research question</Label>
            <Textarea
              id="research_question"
              placeholder="e.g. How does Acme Corp pricing compare to direct competitors?"
              required
              value={form.research_question}
              onChange={(e) => setForm({ ...form, research_question: e.target.value })}
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "Running research…" : "Start research"}
          </Button>
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          {submitted && (
            <div className="mt-4 p-3 rounded-md bg-green-50 text-green-800 text-sm">
              Research started: <strong>{submitted.research_id}</strong> — status:{submitted.status}
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
