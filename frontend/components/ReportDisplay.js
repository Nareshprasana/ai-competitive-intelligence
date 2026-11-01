"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ReportDisplay({ result }) {
  if (!result) return null;

  const metadata = result.execution_metadata || [];
  const errors = result.errors || [];
  const statusOk = result.status === "completed" && errors.length === 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>
          {result.final_report?.title || "Competitive Intelligence Report"}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-4 text-sm text-muted-foreground grid grid-cols-2 gap-4">
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider">
                Research ID
              </span>
              <span>{result.research_id}</span>
            </div>
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider">
                Status
              </span>
              <span className={statusOk ? "text-green-600" : "text-amber-600"}>
                {result.status}
              </span>
            </div>
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider">
                Company
              </span>
              <span>{result.company_name}</span>
            </div>
            <div>
              <span className="block text-xs font-semibold uppercase tracking-wider">
                Industry
              </span>
              <span>{result.industry}</span>
            </div>
          </div>

          <section className="mb-6">
            <h3 className="font-semibold mb-2">Executive Summary</h3>
            <p className="text-sm text-foreground">
              {result.final_report?.sections?.executive_summary ||
                "No executive summary available."}
            </p>
          </section>

          <section className="mb-6">
            <h3 className="font-semibold mb-2">Strategic Analysis</h3>
            <pre className="text-sm p-3 rounded border bg-muted/50 overflow-x-auto">
              {JSON.stringify(
                result.strategic_analysis || {},
                null,
                2,
              )}
            </pre>
          </section>
        </div>

        <div className="lg:col-span-1 flex flex-col gap-4">
          <Card className="flex-1">
            <CardHeader>
              <CardTitle>Execution Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="text-xs space-y-2">
                {metadata.map((m, i) => (
                  <li key={i} className="flex justify-between border-b pb-1 last:border-0">
                    <span>{m.node_name}</span>
                    <span className={m.status === "completed" ? "text-green-600" : "text-red-600"}>
                      {m.status}
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {errors.length > 0 && (
            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="text-destructive">Errors</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-xs space-y-2 text-destructive">
                  {errors.map((e, i) => (
                    <li key={i}>{e.node_name || "unknown"}: {e.error}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
