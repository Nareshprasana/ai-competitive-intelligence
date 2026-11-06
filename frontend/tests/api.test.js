import { test, describe, before, after, mock } from "node:test";
import assert from "node:assert/strict";

// Import modules to test
import {
  API_URL,
  setAccessToken,
  getAccessToken,
  setOrganizationId,
  getOrganizationId,
  login,
  refreshAccessToken,
  logout,
  listResearch,
  submitResearch,
  getResearch,
  reviewEvidence,
  getReport,
  downloadReportPdf,
  downloadReportMarkdown,
  getEvidenceReviews,
  safeUrl,
  health,
} from "../lib/api.js";

describe("ACIS Frontend Centralized API Client", () => {
  const originalFetch = global.fetch;

  after(() => {
    global.fetch = originalFetch;
  });

  test("API_URL defaults to http://localhost:8000 or configured env", () => {
    assert.ok(API_URL.startsWith("http://"));
  });

  test("Organization ID and Access Token management in memory", () => {
    setAccessToken("test-jwt-token");
    assert.equal(getAccessToken(), "test-jwt-token");

    setOrganizationId("org-alpha-123");
    assert.equal(getOrganizationId(), "org-alpha-123");
  });

  test("login sends credentials and stores token on success", async () => {
    global.fetch = mock.fn(async (url, opts) => {
      assert.ok(url.includes("/api/v1/auth/login"));
      assert.equal(opts.method, "POST");
      const body = JSON.parse(opts.body);
      assert.equal(body.email, "analyst@enterprise.com");
      return {
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "jwt-analyst-token",
          token_type: "bearer",
          csrf_token: "csrf-token-123",
          user: { email: "analyst@enterprise.com", full_name: "Analyst One" },
        }),
      };
    });

    const data = await login("analyst@enterprise.com", "SecureP@ssw0rd123");
    assert.equal(data.access_token, "jwt-analyst-token");
    assert.equal(getAccessToken(), "jwt-analyst-token");
  });

  test("login raises normalized error on bad credentials", async () => {
    global.fetch = mock.fn(async () => {
      return {
        ok: false,
        status: 401,
        json: async () => ({ detail: "Invalid email or password." }),
      };
    });

    await assert.rejects(
      async () => {
        await login("bad@enterprise.com", "wrongpassword");
      },
      /Invalid email or password/
    );
  });

  test("listResearch attaches Authorization and X-Organization-ID headers", async () => {
    setAccessToken("auth-token-xyz");
    setOrganizationId("org-test-456");

    global.fetch = mock.fn(async (url, opts) => {
      assert.ok(url.includes("/api/v1/research?limit=20&offset=0"));
      assert.equal(opts.headers.get("Authorization"), "Bearer auth-token-xyz");
      assert.equal(opts.headers.get("X-Organization-ID"), "org-test-456");
      return {
        ok: true,
        status: 200,
        json: async () => [
          {
            research_id: "res-1",
            company_name: "Novastream",
            status: "completed",
          },
        ],
      };
    });

    const list = await listResearch({ limit: 20, offset: 0 });
    assert.equal(list.length, 1);
    assert.equal(list[0].company_name, "Novastream");
  });

  test("submitResearch submits company, industry, and research_question", async () => {
    setAccessToken("auth-token-xyz");
    setOrganizationId("org-test-456");

    global.fetch = mock.fn(async (url, opts) => {
      assert.ok(url.includes("/api/v1/research"));
      assert.equal(opts.method, "POST");
      const body = JSON.parse(opts.body);
      assert.equal(body.company_name, "Novastream Data");
      assert.equal(body.industry, "Data Observability");
      return {
        ok: true,
        status: 201,
        json: async () => ({
          research_id: "res-novastream-999",
          status: "completed",
        }),
      };
    });

    const res = await submitResearch({
      company_name: "Novastream Data",
      industry: "Data Observability",
      research_question: "How do they compare on pricing?",
    });
    assert.equal(res.research_id, "res-novastream-999");
  });

  test("reviewEvidence records analyst decision and notes", async () => {
    setAccessToken("auth-token-xyz");
    setOrganizationId("org-test-456");

    global.fetch = mock.fn(async (url, opts) => {
      assert.ok(url.includes("/evidence/ev-123/review"));
      assert.equal(opts.method, "POST");
      const body = JSON.parse(opts.body);
      assert.equal(body.decision, "verified");
      assert.equal(body.analyst_notes, "Confirmed via official SEC 10-K filing.");
      assert.equal(body.override_confidence, 0.95);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          status: "success",
          evidence_id: "ev-123",
          verification_status: "verified",
          confidence: 0.95,
        }),
      };
    });

    const reviewRes = await reviewEvidence("res-novastream-999", "ev-123", {
      decision: "verified",
      analyst_notes: "Confirmed via official SEC 10-K filing.",
      override_confidence: 0.95,
    });
    assert.equal(reviewRes.status, "success");
    assert.equal(reviewRes.verification_status, "verified");
  });

  test("getReport retrieves structured JSON with 14 sections", async () => {
    setAccessToken("auth-token-xyz");
    setOrganizationId("org-test-456");

    global.fetch = mock.fn(async (url) => {
      assert.ok(url.includes("/api/v1/research/res-1/report"));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          title: "Strategic Intelligence Report: Novastream Data",
          company: "Novastream Data",
          sections: {
            executive_summary: "Novastream demonstrates robust growth...",
            company_profile: "Leading data observability platform...",
            scope_and_methodology: "Multi-agent LangGraph workflow...",
            competitive_landscape: "Market landscape benchmark...",
            direct_competitors: "VectorPulse, LogMatrix...",
            indirect_and_emerging: "Cloud watch platforms...",
            feature_matrix: "Real-time telemetry, SAML SSO...",
            pricing_analysis: "Enterprise tier with consumption model...",
            market_opportunities: "Security compliance expansion...",
            competitive_threats: "Price compression from emerging entrants...",
            recommendations: "Immediate: transparent pricing (0-30 days)...",
            evidence_summary: "Validated across Tier 1 & 2 sources...",
            information_gaps: "Exact customer retention metrics...",
            audit_metadata: "Run ID: res-1, 8 nodes executed...",
          },
        }),
      };
    });

    const report = await getReport("res-1");
    assert.equal(report.company, "Novastream Data");
    assert.ok(report.sections.executive_summary);
    assert.ok(report.sections.direct_competitors);
    assert.ok(report.sections.recommendations);
  });

  test("logout clears in-memory state and credentials", async () => {
    setAccessToken("valid-token");
    setOrganizationId("org-valid");

    global.fetch = mock.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ message: "Logged out" }),
    }));

    await logout();
    assert.equal(getAccessToken(), null);
    assert.equal(getOrganizationId(), null);
  });

  test("refreshAccessToken coordinates concurrent requests into a single fetch call", async () => {
    let callCount = 0;
    // Mock window and localStorage
    global.window = {
      localStorage: {
        getItem: (k) => (k === "acis-csrf-token" ? "csrf-secret-123" : null),
        setItem: () => {},
        removeItem: () => {},
      },
    };

    global.fetch = mock.fn(async (url) => {
      if (url.includes("/api/v1/auth/refresh")) {
        callCount++;
        // Simulate a small delay
        await new Promise((resolve) => setTimeout(resolve, 20));
        return {
          ok: true,
          status: 200,
          json: async () => ({
            access_token: "new-coordinated-token",
            expires_in: 600,
            csrf_token: "next-csrf-token",
          }),
        };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    });

    // Fire 3 concurrent refresh calls simultaneously
    const [t1, t2, t3] = await Promise.all([
      refreshAccessToken(),
      refreshAccessToken(),
      refreshAccessToken(),
    ]);

    assert.equal(t1, "new-coordinated-token");
    assert.equal(t2, "new-coordinated-token");
    assert.equal(t3, "new-coordinated-token");
    // Strictly 1 single request was sent to the server, preventing token reuse session invalidation
    assert.equal(callCount, 1);
  });

  test("getEvidenceReviews retrieves audit logs and preserved machine validation", async () => {
    setAccessToken("test-token");
    setOrganizationId("org-test");

    global.fetch = mock.fn(async (url) => {
      assert.ok(url.includes("/evidence/ev-123/reviews"));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          research_id: "res-1",
          evidence_id: "ev-123",
          machine_verification_status: "verified",
          machine_confidence: 0.92,
          machine_explanation: "Direct SEC filing citation.",
          current_verification_status: "approved",
          current_confidence: 0.95,
          reviews: [
            {
              evidence_id: "ev-123",
              decision: "approved",
              analyst_notes: "Audited and verified by Lead Analyst.",
              reviewed_by: "lead@enterprise.com",
              reviewed_at: "2026-11-06T12:00:00Z",
            },
          ],
        }),
      };
    });

    const data = await getEvidenceReviews("res-1", "ev-123");
    assert.equal(data.evidence_id, "ev-123");
    assert.equal(data.machine_verification_status, "verified");
    assert.equal(data.current_verification_status, "approved");
    assert.equal(data.reviews.length, 1);
    assert.equal(data.reviews[0].decision, "approved");
  });

  test("safeUrl prevents XSS by neutralizing javascript:, data:, and vbscript: URIs", () => {
    assert.equal(safeUrl("javascript:alert(1)"), "#");
    assert.equal(safeUrl("JAVASCRIPT:/*malicious*/window.location='bad.com'"), "#");
    assert.equal(safeUrl("data:text/html,<script>alert(1)</script>"), "#");
    assert.equal(safeUrl("vbscript:msgbox(1)"), "#");
    assert.equal(safeUrl("https://example.com/company-profile"), "https://example.com/company-profile");
    assert.equal(safeUrl("/research/123"), "/research/123");
    assert.equal(safeUrl(null), "#");
    assert.equal(safeUrl(undefined), "#");
  });
});
