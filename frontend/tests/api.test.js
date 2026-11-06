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
});
