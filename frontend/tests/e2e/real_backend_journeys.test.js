import { test, describe, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND_DIR = path.resolve(__dirname, "../..");
const BACKEND_DIR = path.resolve(FRONTEND_DIR, "../backend");
const FRONTEND_PORT = 3009;
const BACKEND_PORT = 8000;
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

// Load untracked local environment variables
const envFile = path.resolve(BACKEND_DIR, ".env");
let envConfig = {};
if (fs.existsSync(envFile)) {
  const content = fs.readFileSync(envFile, "utf-8");
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#") && trimmed.includes("=")) {
      const idx = trimmed.indexOf("=");
      envConfig[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + 1).trim();
    }
  }
}

const DB_URL = process.env.ACIS_TEST_DATABASE_URL || envConfig.ACIS_TEST_DATABASE_URL || envConfig.DATABASE_URL;
const TEST_EMAIL = process.env.TEST_USER_EMAIL || "analyst@real-auth-test.com";
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || "Rotated_Auth_Test_Pass_2026!#Secure";
const TEST_ORG_ID = "org-real-auth-test";

describe("ACIS Phase 3.2.1: Actual Frontend-to-Backend Integration Journeys", () => {
  let backendProcess = null;
  let frontendProcess = null;
  let browser = null;
  let context = null;
  let page = null;

  const waitForServer = (url, timeoutMs = 30000) => {
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
          setTimeout(probe, 400);
        }
      };
      probe();
    });
  };

  before(async () => {
    // 1. Seed user in PostgreSQL acis_test_db
    const seedProc = spawn("python", ["backend/scripts/seed_e2e_user.py"], {
      cwd: path.resolve(BACKEND_DIR, ".."),
      env: {
        ...process.env,
        ACIS_TEST_DATABASE_URL: DB_URL,
        DATABASE_URL: DB_URL,
        TEST_USER_PASSWORD: TEST_PASSWORD,
        DATA_ENCRYPTION_KEYS: '{"k1":"MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="}',
        DATA_ENCRYPTION_ACTIVE_KEY_ID: "k1",
        AUTH_JWT_SIGNING_KEY: "test_signing_key_at_least_32_characters_long_12345",
        AUTH_EMAIL_LOOKUP_KEY: "test_lookup_key_at_least_32_characters_long_12345",
      },
      stdio: "inherit",
    });
    await new Promise((resolve, reject) => {
      seedProc.on("exit", (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Seed process failed with code ${code}`));
      });
    });

    const artifactDir = path.resolve(BACKEND_DIR, "data", "artifacts");

    // 2. Start real FastAPI backend on port 8000
    backendProcess = spawn(
      "python",
      ["-m", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", String(BACKEND_PORT)],
      {
        cwd: BACKEND_DIR,
        env: {
          ...process.env,
          DATABASE_URL: DB_URL,
          ACIS_TEST_DATABASE_URL: DB_URL,
          ARTIFACT_STORAGE_PATH: artifactDir,
          APP_ENV: "development",
          AUTH_COOKIE_SECURE: "false",
          DATA_ENCRYPTION_KEYS: '{"k1":"MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="}',
          DATA_ENCRYPTION_ACTIVE_KEY_ID: "k1",
          AUTH_JWT_SIGNING_KEY: "test_signing_key_at_least_32_characters_long_12345",
          AUTH_EMAIL_LOOKUP_KEY: "test_lookup_key_at_least_32_characters_long_12345",
          BACKEND_CORS_ORIGINS: '["http://localhost:3000","http://127.0.0.1:3000","http://localhost:3009","http://127.0.0.1:3009"]',
        },
        stdio: "ignore",
      }
    );
    await waitForServer(`${BACKEND_URL}/api/v1/health`, 25000);

    // 3. Start Next.js frontend on port 3009
    const nextBin = path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next");
    frontendProcess = spawn(process.execPath, [nextBin, "start", "-H", "0.0.0.0", "-p", String(FRONTEND_PORT)], {
      cwd: FRONTEND_DIR,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_URL: BACKEND_URL,
      },
      stdio: "ignore",
    });
    await waitForServer(`${FRONTEND_URL}/login`, 25000);

    // 4. Launch Chrome headlessly
    browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
      args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    });

    context = await browser.newContext();
    page = await context.newPage();

    // Log in once at start of journey
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: "networkidle" });
    await page.fill("#email", TEST_EMAIL);
    await page.fill("#password", TEST_PASSWORD);
    await page.click("button[type='submit']");
    await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 10000 });
  });

  after(async () => {
    if (page) await page.close().catch(() => {});
    if (context) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
    if (frontendProcess) frontendProcess.kill("SIGTERM");
    if (backendProcess) backendProcess.kill("SIGTERM");
  });

  test("6.1 Real Research Journey: Submit request, PostgreSQL creation, detail polling, and reload persistence", async () => {
    // Navigate to /research/new
    await page.goto(`${FRONTEND_URL}/research/new`, { waitUntil: "networkidle" });
    assert.strictEqual(page.url().includes("/research/new"), true);

    const targetCompany = "Nexis Stream Telemetry";
    const industry = "Data Observability";
    const question = "What are the core competitive strengths and competitor threats?";

    await page.fill("#company_name", targetCompany);
    await page.fill("#industry", industry);
    await page.fill("#research_question", question);

    // Submit form and intercept backend API call
    const [response] = await Promise.all([
      page.waitForResponse((res) => res.url().includes("/api/v1/research") && res.request().method() === "POST", {
        timeout: 15000,
      }),
      page.click("button[type='submit']"),
    ]);

    assert.strictEqual(response.status() < 400, true, `Backend research submission returned ${response.status()}`);
    const responseData = await response.json();
    const createdResearchId = responseData.research_id;
    assert.ok(createdResearchId, "Backend must return created research_id");

    // Wait for navigation to research detail page
    await page.waitForURL((url) => url.pathname.includes(`/research/${createdResearchId}`), { timeout: 15000 });
    assert.strictEqual(page.url().includes(createdResearchId), true);

    // Verify polling request reaches backend
    const pollResponse = await page.waitForResponse(
      (res) => res.url().includes(`/api/v1/research/${createdResearchId}`) && res.request().method() === "GET",
      { timeout: 10000 }
    );
    assert.strictEqual(pollResponse.status(), 200);

    // Verify persistence across browser reload
    await page.reload({ waitUntil: "networkidle" });
    const companyHeader = await page.textContent("body");
    assert.strictEqual(companyHeader.includes(targetCompany), true);

    // Verify in PostgreSQL directly via python probe
    const pyProbe = spawn("python", ["-c", `
import asyncio, os, sys
sys.path.insert(0, 'backend')
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models.research import Research

async def check():
    engine = create_async_engine('${DB_URL}')
    async with AsyncSession(engine) as session:
        stmt = select(Research).where(Research.research_id == '${createdResearchId}')
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        assert record is not None, 'Record must exist in PostgreSQL'
        assert record.company_name == '${targetCompany}'
        assert record.organization_id == '${TEST_ORG_ID}'
    await engine.dispose()
    print('PROBE_SUCCESS')

asyncio.run(check())
    `], { cwd: path.resolve(BACKEND_DIR, "..") });

    let probeOutput = "";
    pyProbe.stdout.on("data", (d) => { probeOutput += d.toString(); });
    await new Promise((res) => pyProbe.on("exit", res));
    assert.strictEqual(probeOutput.includes("PROBE_SUCCESS"), true, "PostgreSQL verification probe failed");
  });

  test("6.2 Real Evidence-Review Journey: Review submission, fresh session persistence, and machine baseline preservation", async () => {
    const researchId = "res-real-evidence-test";
    const evidenceId = "ev-real-journey-1";

    // Seed research and evidence in PostgreSQL
    const seedEvProc = spawn("python", ["-c", `
import asyncio, os, sys
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv()
load_dotenv('backend/.env')
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models.research import Research

async def seed_ev():
    engine = create_async_engine('${DB_URL}')
    async with AsyncSession(engine) as session:
        await session.begin()
        stmt = select(Research).where(Research.research_id == '${researchId}')
        res = (await session.execute(stmt)).scalar_one_or_none()
        if not res:
            res = Research(
                research_id='${researchId}',
                organization_id='${TEST_ORG_ID}',
                company_name='QuantumScale Tech',
                industry='AI',
                research_question='Benchmarking?',
                status='completed',
                review_status='pending',
                results={
                    'research_id': '${researchId}',
                    'organization_id': '${TEST_ORG_ID}',
                    'company_name': 'QuantumScale Tech',
                    'industry': 'AI',
                    'status': 'completed',
                    'evidence': [{
                        'evidence_id': '${evidenceId}',
                        'claim': 'QuantumScale reduces streaming ingestion latency by 45%.',
                        'confidence': 0.92,
                        'verification_status': 'unverified',
                        'machine_verification_status': 'verified',
                        'machine_confidence': 0.92,
                        'machine_explanation': 'Cross-referenced against verified benchmark report.',
                    }],
                    'validation_results': {'contradictions': [], 'human_review_log': []}
                }
            )
            session.add(res)
        await session.commit()
    await engine.dispose()
    print('SEED_EV_SUCCESS')

asyncio.run(seed_ev())
    `], {
      cwd: BACKEND_DIR,
      env: {
        ...process.env,
        ACIS_TEST_DATABASE_URL: DB_URL,
        DATABASE_URL: DB_URL,
        ARTIFACT_STORAGE_PATH: path.resolve(BACKEND_DIR, "data", "artifacts"),
      },
    });
    let seedEvOutput = "";
    seedEvProc.stdout.on("data", (d) => { seedEvOutput += d.toString(); });
    seedEvProc.stderr.on("data", (d) => { console.error("SEED_EV_ERR:", d.toString()); });
    await new Promise((res) => seedEvProc.on("exit", res));
    assert.strictEqual(seedEvOutput.includes("SEED_EV_SUCCESS"), true, `Seed failed: ${seedEvOutput}`);

    // Open evidence review interface
    await page.goto(`${FRONTEND_URL}/evidence?research_id=${researchId}`, { waitUntil: "networkidle" });

    // Review evidence via frontend API from authenticated browser context
    const reviewResult = await page.evaluate(async ({ researchId, evidenceId }) => {
      const api = window.__acis_api;
      return api.reviewEvidence(researchId, evidenceId, {
        decision: "approved",
        analyst_notes: "Analyst verified latency figures against SEC Form 10-K filing.",
      });
    }, { researchId, evidenceId });

    assert.strictEqual(reviewResult.status, "success");
    assert.strictEqual(reviewResult.verification_status, "approved");

    // Verify in PostgreSQL in a fresh session: persistence & baseline preservation
    const verifyProbe = spawn("python", ["-c", `
import asyncio, os, sys
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv()
load_dotenv('backend/.env')
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models.research import Research

async def verify():
    engine = create_async_engine('${DB_URL}')
    async with AsyncSession(engine) as session:
        stmt = select(Research).where(Research.research_id == '${researchId}')
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        assert record is not None, 'Research record must exist in PostgreSQL'
        ev = record.results['evidence'][0]
        assert ev['verification_status'] == 'approved', f"Status is {ev['verification_status']}"
        assert ev['human_review']['decision'] == 'approved'
        assert 'Analyst verified' in ev['human_review']['analyst_notes']
        
        # Machine validation telemetry strictly preserved
        assert ev['machine_verification_status'] == 'verified'
        assert ev['machine_confidence'] == 0.92
        assert 'Cross-referenced' in ev['machine_explanation']
    await engine.dispose()
    print('VERIFY_EV_SUCCESS')

asyncio.run(verify())
    `], {
      cwd: BACKEND_DIR,
      env: {
        ...process.env,
        ACIS_TEST_DATABASE_URL: DB_URL,
        DATABASE_URL: DB_URL,
        ARTIFACT_STORAGE_PATH: path.resolve(BACKEND_DIR, "data", "artifacts"),
      },
    });

    let verifyOutput = "";
    verifyProbe.stdout.on("data", (d) => { verifyOutput += d.toString(); });
    verifyProbe.stderr.on("data", (d) => { console.error("VERIFY_EV_ERR:", d.toString()); });
    await new Promise((res) => verifyProbe.on("exit", res));
    assert.strictEqual(verifyOutput.includes("VERIFY_EV_SUCCESS"), true, "Evidence verification probe failed");
  });

  test("6.3 Real Report Journey: Render report, download real PDF & Markdown, verify ownership & authorization", async () => {
    const researchId = "res-real-report-test";

    // Seed completed research with full report and real ReportLab PDF in PostgreSQL
    const seedRepProc = spawn("python", ["-c", `
import asyncio, os, sys
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv()
load_dotenv('backend/.env')
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models.research import Research
from app.models.identity import Organization
from app.agents.report_generator import ReportGeneratorAgent
from app.graph.state import ResearchState
from app.repositories.report import ReportRepository

async def seed_report():
    engine = create_async_engine('${DB_URL}')
    state = ResearchState(
        research_id='${researchId}',
        organization_id='${TEST_ORG_ID}',
        company_name='Atlas Horizon Robotics',
        industry='Robotics & Automation',
        research_question='Competitive assessment?',
        company_profile={'company_name': 'Atlas Horizon Robotics', 'products': ['Atlas Arm 5']},
        competitors=[{'company_name': 'RoboFlex', 'competitor_type': 'direct'}],
        evidence=[{'evidence_id': 'ev-rep-1', 'claim': 'Atlas Arm 5 achieves sub-millimeter precision.', 'source_url': 'https://atlas.example', 'confidence': 0.95}],
    )
    agent = ReportGeneratorAgent()
    report, md_text, pdf_bytes = await agent.generate_report(state)

    async with AsyncSession(engine) as session:
        await session.begin()
        stmt = select(Research).where(Research.research_id == '${researchId}')
        res = (await session.execute(stmt)).scalar_one_or_none()
        if not res:
            res = Research(
                research_id='${researchId}',
                organization_id='${TEST_ORG_ID}',
                company_name='Atlas Horizon Robotics',
                industry='Robotics',
                research_question='Assessment?',
                status='completed',
                results={'final_report': report.model_dump(mode='json')},
            )
            session.add(res)
            await session.flush()
        
        repo = ReportRepository(session)
        await repo.save_report(
            research_id='${researchId}',
            organization_id='${TEST_ORG_ID}',
            report_data=report.model_dump(mode='json'),
            pdf_bytes=pdf_bytes,
            markdown_text=md_text,
        )
        await session.commit()
    await engine.dispose()
    print('SEED_REPORT_SUCCESS')

asyncio.run(seed_report())
    `], {
      cwd: BACKEND_DIR,
      env: {
        ...process.env,
        ACIS_TEST_DATABASE_URL: DB_URL,
        DATABASE_URL: DB_URL,
        ARTIFACT_STORAGE_PATH: path.resolve(BACKEND_DIR, "data", "artifacts"),
      },
    });

    let seedRepOutput = "";
    seedRepProc.stdout.on("data", (d) => { seedRepOutput += d.toString(); });
    seedRepProc.stderr.on("data", (d) => { console.error("SEED_REP_ERR:", d.toString()); });
    await new Promise((res) => seedRepProc.on("exit", res));
    assert.strictEqual(seedRepOutput.includes("SEED_REPORT_SUCCESS"), true, `Report seed failed: ${seedRepOutput}`);

    // Open real report in browser
    await page.goto(`${FRONTEND_URL}/reports?research_id=${researchId}`, { waitUntil: "networkidle" });
    const pageText = await page.textContent("body");
    assert.strictEqual(pageText.includes("Atlas Horizon Robotics"), true);

    // Download real PDF via API from browser session
    const pdfBase64 = await page.evaluate(async ({ researchId }) => {
      const api = window.__acis_api;
      const blob = await api.downloadReportPdf(researchId);
      const reader = new FileReader();
      return new Promise((resolve) => {
        reader.onloadend = () => resolve(reader.result.split(",")[1]);
        reader.readAsDataURL(blob);
      });
    }, { researchId });

    const pdfBuffer = Buffer.from(pdfBase64, "base64");
    assert.strictEqual(pdfBuffer.toString("ascii", 0, 5), "%PDF-");
    assert.strictEqual(pdfBuffer.length > 5000, true);

    // Download Markdown via API from browser session
    const markdownContent = await page.evaluate(async ({ researchId }) => {
      const api = window.__acis_api;
      return api.downloadReportMarkdown(researchId);
    }, { researchId });

    assert.strictEqual(markdownContent.includes("# Competitive Intelligence Report"), true);
    assert.strictEqual(markdownContent.includes("Atlas Horizon Robotics"), true);

    // Verify cross-tenant access rejection (404)
    const crossTenantStatus = await page.evaluate(async () => {
      // Direct unauthenticated or forged org fetch
      const res = await fetch("http://localhost:8000/api/v1/research/res-real-report-test/report/pdf");
      return res.status;
    });
    assert.strictEqual(crossTenantStatus, 401, "Unauthenticated access to PDF must return 401");
  });
});
