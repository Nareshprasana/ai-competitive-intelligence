import { test, describe, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND_DIR = path.resolve(__dirname, "../..");
const PORT = 3009;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

// Mock data fixtures
const MOCK_ORGS = [
  { organization_id: "org-alpha", name: "Acme Alpha Corp", role: "organization_owner" },
  { organization_id: "org-beta", name: "Beta Global Inc", role: "analyst" },
];

const MOCK_RESEARCH_ALPHA = [
  {
    research_id: "res-alpha-001",
    company_name: "Novastream Data",
    industry: "Data Infrastructure",
    research_question: "Competitive landscape and pricing benchmark?",
    status: "completed",
    created_at: new Date().toISOString(),
    results: {
      research_id: "res-alpha-001",
      company_name: "Novastream Data",
      industry: "Data Infrastructure",
      status: "completed",
      company_profile: {
        description: "Enterprise data observability and stream telemetry platform.",
        website: "https://novastream.example.com",
        products: ["NovaStream Core", "NovaTelemetry Agent"],
        target_customers: ["Fortune 500 Enterprises", "FinTech"],
        geographical_presence: ["North America", "Europe"],
        source_references: ["https://sec.gov/filings/novastream-10k"],
      },
      competitors: [
        {
          name: "VectorPulse",
          competitor_type: "direct",
          website: "https://vectorpulse.example.com",
          overlap_score: 0.88,
          market_presence: "High",
          strengths: ["Cloud-native scaling", "Pre-built dashboards"],
          weaknesses: ["High egress cost"],
          evidence_citations: [
            {
              claim: "VectorPulse captured 18% market share in cloud streaming.",
              source_title: "Cloud Analytics Benchmark 2026",
              source_url: "https://marketreports.example.com/streaming",
            },
          ],
        },
        {
          name: "LogMatrix",
          competitor_type: "indirect",
          website: "https://logmatrix.example.com",
          overlap_score: 0.65,
          market_presence: "Medium",
          strengths: ["Legacy log ingestion"],
          weaknesses: ["Lacks real-time alerts"],
          evidence_citations: [],
        },
      ],
      evidence: [
        {
          evidence_id: "ev-alpha-101",
          claim: "Novastream closed $42M in ARR with 120% net retention rate.",
          source_domain: "sec.gov",
          source_url: "https://sec.gov/filings/novastream",
          verification_status: "verified",
          confidence: 0.94,
          machine_verification_status: "verified",
          machine_confidence: 0.94,
          machine_explanation: "Direct audited SEC 10-K filing.",
        },
        {
          evidence_id: "ev-alpha-102",
          claim: "Novastream offers 99.999% uptime SLA.",
          source_domain: "pricing-review.example.com",
          source_url: "https://pricing-review.example.com",
          verification_status: "contradicted",
          confidence: 0.45,
          machine_verification_status: "contradicted",
          machine_confidence: 0.45,
          machine_explanation: "Public status page indicates 99.9% commitment, contradicting sales brochure.",
        },
      ],
      validation_results: {
        contradictions: [
          {
            topic: "Uptime SLA Guarantee",
            claim_a: "99.999% SLA in enterprise brochure",
            claim_b: "99.9% actual historical availability",
          },
        ],
      },
      strategic_analysis: {
        swot: {
          strengths: ["Strong enterprise retention (120% NRR)", "Patented low-latency pipeline"],
          weaknesses: ["Complex Kubernetes onboarding", "Limited self-service tier"],
          opportunities: ["Expansion into EU sovereign cloud", "Automated compliance modules"],
          threats: ["Open-source streaming alternatives", "Aggressive discounting by VectorPulse"],
        },
        recommendations: [
          {
            action: "Publish transparent tiered consumption pricing",
            time_horizon: "immediate",
            impact: "High",
            effort: "Low",
            driver: "Competitive Transparency",
          },
          {
            action: "Launch self-service developer trial",
            time_horizon: "near_term",
            impact: "High",
            effort: "Medium",
            driver: "Product-Led Growth",
          },
          {
            action: "Establish automated GDPR/HIPAA compliance validator",
            time_horizon: "medium_term",
            impact: "Medium",
            effort: "Medium",
            driver: "Regulatory Moat",
          },
          {
            action: "Acquire sovereign cloud hosting provider in EMEA",
            time_horizon: "long_term",
            impact: "Transformational",
            effort: "High",
            driver: "Geographic Expansion",
          },
        ],
      },
      final_report: {
        title: "Competitive Intelligence Report: Novastream Data",
        company: "Novastream Data",
        sections: {
          executive_summary: "Novastream Data demonstrates strong enterprise growth with 120% NRR...",
          company_profile: "Leading enterprise streaming observability platform.",
          industry_context: "Enterprise observability market undergoing rapid consolidation.",
          market_dynamics: "Data sovereignty requirements driving localized cloud adoption.",
          competitor_landscape: "Direct competitors VectorPulse and LogMatrix hold significant share.",
          direct_competitors: "VectorPulse directly competes with 88% product overlap.",
          indirect_and_emerging: "LogMatrix and emerging open-source toolkits.",
          evidence_base: "Validated across audited SEC filings and technical documentation.",
          contradictions: "Uptime guarantee discrepancy identified between brochure and status logs.",
          swot_analysis: "Strengths include strong retention; weaknesses include Kubernetes onboarding.",
          positioning_matrix: "High-value enterprise segment leader.",
          strategic_scenarios: "Scenario A: Aggressive pricing match. Scenario B: Moat defense via compliance.",
          actionable_recommendations: "Immediate transparent pricing (0-30 days); developer trial (1-3 months).",
          appendix_and_sources: "SEC 10-K, Cloud Benchmark 2026, status telemetry logs.",
        },
      },
      execution_metadata: [
        { node_name: "initialize_research", status: "completed" },
        { node_name: "research_planner", status: "completed" },
        { node_name: "company_researcher", status: "completed" },
        { node_name: "competitor_discovery", status: "completed" },
        { node_name: "evidence_validator", status: "completed" },
        { node_name: "strategic_analyst", status: "completed" },
        { node_name: "report_generator", status: "completed" },
        { node_name: "finalize_research", status: "completed" },
      ],
      errors: [],
    },
  },
];

const MOCK_RESEARCH_BETA = [
  {
    research_id: "res-beta-999",
    company_name: "Beta Horizon",
    industry: "Renewable Energy",
    research_question: "Battery storage market share?",
    status: "completed",
    created_at: new Date().toISOString(),
    results: {
      research_id: "res-beta-999",
      company_name: "Beta Horizon",
      industry: "Renewable Energy",
      status: "completed",
      evidence: [],
      competitors: [],
      errors: [],
    },
  },
];

describe("ACIS Browser-Level End-to-End Tests & User Journeys", () => {
  let serverProcess = null;
  let browser = null;

  // Helper to wait until server is responsive
  const waitForServer = (url, timeoutMs = 25000) => {
    const start = Date.now();
    return new Promise((resolve, reject) => {
      const probe = () => {
        const req = http.get(url, (res) => {
          if (res.statusCode < 500) {
            resolve();
          } else {
            retry();
          }
        });
        req.on("error", retry);
        req.end();
      };
      const retry = () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error(`Timed out waiting for server at ${url}`));
        } else {
          setTimeout(probe, 300);
        }
      };
      probe();
    });
  };

  before(async () => {
    // 1. Start Next.js production server on PORT 3009 using node executable directly
    const nextBin = path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next");
    serverProcess = spawn(process.execPath, [nextBin, "start", "-H", "127.0.0.1", "-p", String(PORT)], {
      cwd: FRONTEND_DIR,
      stdio: "ignore",
    });

    await waitForServer(`${BASE_URL}/login`, 25000);

    // 2. Launch real Google Chrome headlessly
    browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
      args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    });
  });

  after(async () => {
    if (browser) await browser.close();
    if (serverProcess) {
      serverProcess.kill("SIGTERM");
    }
  });

  // Setup standard authenticated route mock
  const setupStandardApiRoutes = async (page, defaultOrg = "org-alpha") => {
    let activeOrgId = defaultOrg;
    let evidenceReviewed = false;
    let reviewedDecision = "approved";
    let reviewedNotes = "";

    await page.route("**/api/v1/**", async (route) => {
      const url = route.request().url();
      const method = route.request().method();
      const headers = route.request().headers();

      // Health endpoint
      if (url.includes("/api/v1/health")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            status: "ok",
            service: "ai-competitive-intelligence",
            database: { available: true, configured: true },
            llm: { configured: true, provider: "openrouter" },
          }),
        });
      }

      // Login endpoint
      if (url.includes("/api/v1/auth/login") && method === "POST") {
        const body = JSON.parse(route.request().postData() || "{}");
        if (body.email === "analyst@enterprise.com" && body.password === "ValidPassword123!") {
          return route.fulfill({
            status: 200,
            contentType: "application/json",
            headers: {
              "Set-Cookie": "acis_refresh_token=mock-refresh-tok; Path=/api/v1/auth; HttpOnly; SameSite=Strict",
            },
            body: JSON.stringify({
              access_token: "mock-jwt-access-token",
              expires_in: 600,
              csrf_token: "mock-csrf-token-abc",
              user: { email: "analyst@enterprise.com", full_name: "Lead Analyst" },
            }),
          });
        }
        return route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Invalid email or password." }),
        });
      }

      // Refresh token endpoint
      if (url.includes("/api/v1/auth/refresh") && method === "POST") {
        const csrf = headers["x-csrf-token"];
        if (!csrf) {
          return route.fulfill({ status: 403, body: JSON.stringify({ detail: "CSRF token missing" }) });
        }
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            access_token: "mock-jwt-access-token-refreshed",
            expires_in: 600,
            csrf_token: "mock-csrf-token-next",
            user: { email: "analyst@enterprise.com", full_name: "Lead Analyst" },
          }),
        });
      }

      // Logout endpoint
      if (url.includes("/api/v1/auth/logout") && method === "POST") {
        return route.fulfill({
          status: 204,
          headers: {
            "Set-Cookie": "acis_refresh_token=; Path=/api/v1/auth; Max-Age=0; HttpOnly; SameSite=Strict",
          },
          body: "",
        });
      }

      // Organizations list
      if (url.includes("/api/v1/auth/organizations")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_ORGS),
        });
      }

      // Report PDF endpoint
      if (url.includes("/report/pdf")) {
        const pdfBytes = Buffer.from(
          "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n" +
            "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
            "3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n" +
            "xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n" +
            "trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
        );
        return route.fulfill({
          status: 200,
          contentType: "application/pdf",
          headers: {
            "Content-Disposition": 'attachment; filename="acis-report-res-alpha-001.pdf"',
            "Content-Type": "application/pdf",
            "X-Content-Type-Options": "nosniff",
          },
          body: pdfBytes,
        });
      }

      // Report Markdown endpoint
      if (url.includes("/report/markdown")) {
        const mdText = "# Competitive Intelligence Report: Novastream Data\n\n## 1. Executive Summary\nValidated content.";
        return route.fulfill({
          status: 200,
          contentType: "text/markdown; charset=utf-8",
          headers: {
            "Content-Disposition": 'attachment; filename="acis-report-res-alpha-001.md"',
          },
          body: mdText,
        });
      }

      // Report JSON endpoint
      if (url.includes("/report") && method === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_RESEARCH_ALPHA[0].results.final_report),
        });
      }

      // Evidence review submit endpoint
      if (url.includes("/evidence/") && url.includes("/review") && method === "POST") {
        const reviewReq = JSON.parse(route.request().postData() || "{}");
        evidenceReviewed = true;
        reviewedDecision = reviewReq.decision;
        reviewedNotes = reviewReq.analyst_notes;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            status: "success",
            evidence_id: "ev-alpha-101",
            verification_status: reviewReq.decision,
            confidence: reviewReq.override_confidence || 0.95,
            machine_verification_status: "verified",
            machine_confidence: 0.94,
            human_review: {
              decision: reviewReq.decision,
              analyst_notes: reviewReq.analyst_notes,
              reviewed_by: "analyst@enterprise.com",
              reviewed_at: new Date().toISOString(),
            },
          }),
        });
      }

      // Evidence review audit log endpoint
      if (url.includes("/evidence/") && url.includes("/reviews") && method === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            research_id: "res-alpha-001",
            evidence_id: "ev-alpha-101",
            machine_verification_status: "verified",
            machine_confidence: 0.94,
            current_verification_status: evidenceReviewed ? reviewedDecision : "verified",
            reviews: evidenceReviewed
              ? [
                  {
                    evidence_id: "ev-alpha-101",
                    decision: reviewedDecision,
                    analyst_notes: reviewedNotes,
                    reviewed_by: "analyst@enterprise.com",
                    reviewed_at: new Date().toISOString(),
                  },
                ]
              : [],
          }),
        });
      }

      // Single Research detail endpoint (matching exact ID path)
      if (url.match(/\/api\/v1\/research\/[a-zA-Z0-9_-]+(\?.*)?$/) && method === "GET") {
        if (url.includes("res-new-555")) {
          return route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              research_id: "res-new-555",
              company_name: "CloudMatrix Tech",
              industry: "Cloud Infrastructure",
              research_question: "What are their core pricing tiers and primary enterprise differentiators?",
              status: "completed",
              created_at: new Date().toISOString(),
              results: {
                research_id: "res-new-555",
                company_name: "CloudMatrix Tech",
                industry: "Cloud Infrastructure",
                status: "completed",
                research_question: "What are their core pricing tiers and primary enterprise differentiators?",
                execution_metadata: [
                  { node_name: "initialize_research", status: "completed" },
                  { node_name: "research_planner", status: "completed" },
                  { node_name: "company_researcher", status: "completed" },
                  { node_name: "finalize_research", status: "completed" },
                ],
                evidence: [],
                competitors: [],
                errors: [],
              },
            }),
          });
        }

        const reqOrg = headers["x-organization-id"] || activeOrgId;
        if (reqOrg !== "org-alpha") {
          return route.fulfill({
            status: 404,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Research not found for this organization." }),
          });
        }
        const alphaCopy = JSON.parse(JSON.stringify(MOCK_RESEARCH_ALPHA[0]));
        if (evidenceReviewed) {
          alphaCopy.results.evidence[0].verification_status = reviewedDecision;
          alphaCopy.results.evidence[0].human_review = {
            decision: reviewedDecision,
            analyst_notes: reviewedNotes,
            reviewed_by: "analyst@enterprise.com",
            reviewed_at: new Date().toISOString(),
          };
        }
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(alphaCopy),
        });
      }

      // Research list endpoint
      if (url.match(/\/api\/v1\/research(\?|$)/) && method === "GET") {
        const reqOrg = headers["x-organization-id"] || activeOrgId;
        const data = reqOrg === "org-beta" ? MOCK_RESEARCH_BETA : MOCK_RESEARCH_ALPHA;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(data),
        });
      }

      // Research submit endpoint
      if (url.includes("/api/v1/research") && method === "POST" && !url.includes("/evidence/")) {
        const postData = JSON.parse(route.request().postData() || "{}");
        const newRun = {
          research_id: "res-new-555",
          company_name: postData.company_name,
          industry: postData.industry,
          research_question: postData.research_question,
          status: "completed",
          created_at: new Date().toISOString(),
          results: {
            research_id: "res-new-555",
            company_name: postData.company_name,
            industry: postData.industry,
            research_question: postData.research_question,
            status: "completed",
            execution_metadata: [
              { node_name: "initialize_research", status: "completed" },
              { node_name: "research_planner", status: "completed" },
              { node_name: "company_researcher", status: "completed" },
              { node_name: "finalize_research", status: "completed" },
            ],
            evidence: [],
            competitors: [],
            errors: [],
          },
        };
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify(newRun),
        });
      }

      // Fallback
      return route.continue();
    });
  };

  test("Journey A: Authentication Lifecycle (Login, Session, Reload, Logout)", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    // 1. Open login page
    await page.goto(`${BASE_URL}/login`);
    await page.waitForSelector('input[type="email"]');
    assert.ok(await page.title());

    // 2. Perform login
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');

    // 3. Confirm redirected to Overview Dashboard
    await page.waitForURL(`${BASE_URL}/`);
    await page.waitForSelector("text=Intelligence Overview");

    // 4. Verify user and organization state loaded
    const bodyText = await page.textContent("body");
    assert.ok(bodyText.includes("Acme Alpha Corp") || bodyText.includes("Intelligence Overview"));

    // 5. Test page reload with session restoration
    await page.reload();
    await page.waitForSelector("text=Intelligence Overview");
    assert.ok((await page.textContent("body")).includes("Intelligence Overview"));

    // 6. Test logout
    const logoutBtn = page.locator('button[title="Sign Out"]');
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await page.waitForURL(`${BASE_URL}/login`);
      await page.waitForSelector('input[type="email"]');
    }

    await testContext.close();
  });

  test("Journey B: Research Formulation, Execution Tracker & Polling", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    // Directly login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/`);

    // Navigate to /research/new
    await page.goto(`${BASE_URL}/research/new`);
    await page.waitForSelector('#company_name');

    // Fill in research formulation form
    await page.fill('#company_name', "CloudMatrix Tech");
    await page.fill('#industry', "Cloud Infrastructure");
    await page.fill(
      '#research_question',
      "What are their core pricing tiers and primary enterprise differentiators?"
    );

    // Submit form
    await page.click('button[type="submit"]');

    // Expect navigation to detail tracker
    await page.waitForURL(/\/research\/res-/);
    await page.waitForSelector("text=CloudMatrix Tech");
    const detailContent = await page.textContent("body");
    assert.ok(detailContent.includes("CloudMatrix Tech"));
    assert.ok(detailContent.includes("completed") || detailContent.includes("Planner"));

    await testContext.close();
  });

  test("Journey C: Multi-Tenant Organization Isolation & Cross-Tenant Rejection", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page, "org-alpha");

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/`);

    // Go to Research listing under Org Alpha
    await page.goto(`${BASE_URL}/research`);
    await page.waitForSelector("text=Novastream Data");
    assert.ok((await page.textContent("body")).includes("Novastream Data"));

    // Switch Organization to Beta via header select
    const orgSelect = page.locator("select").first();
    if (await orgSelect.count() > 0) {
      await orgSelect.selectOption("org-beta");
      await page.waitForTimeout(600);

      // Verify Org Alpha research is purged from view and Beta appears
      const bodyAfterSwitch = await page.textContent("body");
      assert.ok(bodyAfterSwitch.includes("Beta Horizon") || !bodyAfterSwitch.includes("Novastream Data"));
    }

    await testContext.close();
  });

  test("Journey D: Evidence Review, Decision Submission & Machine Preservation", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/`);

    // Navigate to evidence workspace
    await page.goto(`${BASE_URL}/evidence?research_id=res-alpha-001`);
    await page.waitForSelector("text=Evidence Review Workspace");

    // Verify contradiction alert banner is rendered prominently
    await page.waitForSelector("text=Cross-Source Contradictions Detected");
    const pageContent = await page.textContent("body");
    assert.ok(pageContent.includes("Cross-Source Contradictions Detected"));

    // Click Review button on first evidence item
    const reviewBtn = page.locator('button:has-text("Review")').first();
    await reviewBtn.click();

    // Verify modal opened with preserved machine validation details
    await page.waitForSelector("text=Machine Validation Status:");
    const modalText = await page.textContent("body");
    assert.ok(modalText.includes("Machine Validation Status:"));
    assert.ok(modalText.includes("Machine Confidence Score:"));

    // Select Approved decision and provide notes
    await page.locator("form select").selectOption("approved");
    await page.fill('textarea[placeholder*="Provide evidence"]', "Audited and verified by Lead Analyst.");

    // Submit review
    await page.click('button:has-text("Save Review Decision")');
    await page.waitForSelector("text=Review decision recorded successfully.");

    await testContext.close();
  });

  test("Journey E: Strategic Analysis SWOT Matrix & Timelines", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/`);

    // Navigate to Strategy workspace
    await page.goto(`${BASE_URL}/strategy?research_id=res-alpha-001`);
    await page.waitForSelector("text=Strategic Analysis Workspace");
    await page.waitForSelector("text=Strengths");

    const content = await page.textContent("body");
    // Verify 4 SWOT quadrants
    assert.ok(content.includes("Strengths"));
    assert.ok(content.includes("Weaknesses"));
    assert.ok(content.includes("Opportunities"));
    assert.ok(content.includes("Threats"));

    // Verify timeline horizons
    assert.ok(content.includes("Immediate (0–30 days)"));
    assert.ok(content.includes("Short term (1–3 months)"));
    assert.ok(content.includes("Medium term (3–6 months)"));
    assert.ok(content.includes("Long term (6–12 months)"));

    await testContext.close();
  });

  test("Journey F: 14-Section Strategic Report Reader & Document Downloads", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', "analyst@enterprise.com");
    await page.fill('input[type="password"]', "ValidPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/`);

    // Navigate to Reports workspace
    await page.goto(`${BASE_URL}/reports?research_id=res-alpha-001`);
    await page.waitForSelector("text=Competitive Intelligence Reports");
    await page.waitForSelector("text=01. Executive Summary");

    const reportText = await page.textContent("body");
    // Verify sections rendered
    assert.ok(reportText.includes("01. Executive Summary"));
    assert.ok(reportText.includes("05. Direct Competitor Profiles") || reportText.includes("VectorPulse"));

    // Test PDF download click
    const pdfBtn = page.locator('button:has-text("Download PDF")');
    assert.ok(await pdfBtn.count() > 0);

    // Test Markdown download click
    const mdBtn = page.locator('button:has-text("Markdown")');
    assert.ok(await mdBtn.count() > 0);

    // Test Raw JSON modal trigger
    const jsonBtn = page.locator('button:has-text("JSON")');
    if (await jsonBtn.count() > 0) {
      await jsonBtn.click();
      await page.waitForSelector("text=Structured StrategicReport JSON");
      assert.ok((await page.textContent("body")).includes("Structured StrategicReport JSON"));
    }

    await testContext.close();
  });

  test("Journey G: Failure Handling & Error Recovery", async () => {
    const testContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await testContext.newPage();

    // 1. Simulate Backend Unavailable (503 Service Unavailable)
    await page.route("**/api/v1/health", (route) => {
      route.fulfill({ status: 503, body: JSON.stringify({ detail: "Backend offline" }) });
    });
    await page.route("**/api/v1/auth/**", (route) => {
      route.fulfill({ status: 503, body: JSON.stringify({ detail: "Authentication unavailable" }) });
    });

    await page.goto(`${BASE_URL}/login`);
    await page.waitForSelector('input[type="email"]');
    await page.fill('input[type="email"]', "offline@test.com");
    await page.fill('input[type="password"]', "any-password");
    await page.click('button[type="submit"]');

    // Verify error is caught gracefully and presented to user without crashing the app
    const alertLocator = page.locator('.border-rose-200, [role="alert"]:not(#__next-route-announcer__)').first();
    await alertLocator.waitFor({ timeout: 10000 });
    const errorAlert = await alertLocator.textContent();
    assert.ok(errorAlert.includes("Sign In Error") || errorAlert.includes("unavailable") || errorAlert.includes("failed"));

    await testContext.close();
  });

  test("Responsive Viewport Verification (Desktop, Laptop, Tablet, Mobile)", async () => {
    const testContext = await browser.newContext();
    const page = await testContext.newPage();
    await setupStandardApiRoutes(page);

    const viewports = [
      { name: "Desktop", width: 1440, height: 900 },
      { name: "Laptop", width: 1280, height: 800 },
      { name: "Tablet", width: 768, height: 1024 },
      { name: "Mobile", width: 390, height: 844 },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(`${BASE_URL}/login`);
      await page.waitForSelector('input[type="email"]');

      // Verify login card is visible and accessible in this viewport
      const emailInput = page.locator('input[type="email"]');
      assert.ok(await emailInput.isVisible(), `${vp.name} viewport email input should be visible`);
      const submitBtn = page.locator('button[type="submit"]');
      assert.ok(await submitBtn.isVisible(), `${vp.name} viewport submit button should be visible`);
    }

    await testContext.close();
  });
});
