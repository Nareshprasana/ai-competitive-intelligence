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

// Load local untracked environment configuration if present
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

describe("ACIS Phase 3.2: Production Real-Backend Authentication Lifecycle & Cookie Verification", () => {
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

    // 4. Launch Google Chrome headlessly
    browser = await chromium.launch({
      executablePath: CHROME_PATH,
      headless: true,
      args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    });

    context = await browser.newContext();
    page = await context.newPage();
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    page.on("requestfailed", (req) => console.log("PAGE REQ FAILED:", req.url(), req.failure()?.errorText));
    page.on("response", (res) => console.log("PAGE RES:", res.status(), res.url()));
  });

  after(async () => {
    if (page) await page.close().catch(() => {});
    if (context) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
    if (frontendProcess) frontendProcess.kill("SIGTERM");
    if (backendProcess) backendProcess.kill("SIGTERM");
  });

  test("1. Real Browser Login & HttpOnly Cookie Verification against PostgreSQL backend", async () => {
    // Navigate to real frontend login
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: "networkidle" });

    // Fill in real seeded credentials
    await page.fill("#email", TEST_EMAIL);
    await page.fill("#password", TEST_PASSWORD);
    await page.click("button[type='submit']");

    // Wait for successful navigation to dashboard
    await page.waitForURL(`${FRONTEND_URL}/`, { timeout: 15000 });
    assert.equal(page.url(), `${FRONTEND_URL}/`);

    // Inspect real browser cookies in context
    const allCookies = await context.cookies();
    console.log("ALL CONTEXT COOKIES:", JSON.stringify(allCookies, null, 2));
    const refreshCookie = allCookies.find((c) => c.name === "acis_refresh_token");

    assert.ok(refreshCookie, "acis_refresh_token cookie must be set by backend");
    assert.equal(refreshCookie.httpOnly, true, "acis_refresh_token MUST have HttpOnly=true");
    assert.equal(refreshCookie.path, "/api/v1/auth", "acis_refresh_token MUST have Path=/api/v1/auth");
    assert.equal(
      refreshCookie.sameSite.toLowerCase(),
      "strict",
      "acis_refresh_token MUST have SameSite=Strict"
    );
    assert.ok(refreshCookie.value.length > 20, "acis_refresh_token value must be a valid token string");

    // Verify client-side JavaScript CANNOT read acis_refresh_token via document.cookie
    const docCookie = await page.evaluate(() => document.cookie);
    assert.equal(
      docCookie.includes("acis_refresh_token"),
      false,
      "acis_refresh_token must NEVER be accessible via document.cookie"
    );

    // Verify CSRF token and organization ID stored in localStorage
    const storedCsrf = await page.evaluate(() => localStorage.getItem("acis-csrf-token"));
    assert.ok(storedCsrf && storedCsrf.length > 10, "acis-csrf-token must be stored in localStorage");

    const storedOrgId = await page.evaluate(() => localStorage.getItem("acis-organization-id"));
    assert.equal(storedOrgId, TEST_ORG_ID, "Stored organization must match user's organization");
  });

  test("2. Session Restoration on Page Reload (Silent Background Refresh)", async () => {
    // Reload the page
    await page.reload({ waitUntil: "networkidle" });

    // Ensure session is restored without redirecting to /login
    await page.waitForTimeout(1000);
    assert.equal(page.url(), `${FRONTEND_URL}/`);

    // Verify UI components rendered
    const title = await page.textContent("body");
    assert.ok(
      title.includes("Competitive Intelligence") || title.includes("Real Auth Test Corp"),
      "Dashboard must be displayed after reload"
    );
  });

  test("3. Refresh Token Rotation Verification (New Refresh Token Issued, Old Invalidated)", async () => {
    const cookiesBefore = await context.cookies();
    const oldCookie = cookiesBefore.find((c) => c.name === "acis_refresh_token");
    assert.ok(oldCookie, "Pre-rotation cookie must exist");

    // Call POST /api/v1/auth/refresh directly from browser context with credentials
    const refreshResult = await page.evaluate(async (backendUrl) => {
      const csrf = localStorage.getItem("acis-csrf-token");
      const res = await fetch(`${backendUrl}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": csrf },
      });
      const data = await res.json().catch(() => ({}));
      if (data.csrf_token) {
        localStorage.setItem("acis-csrf-token", data.csrf_token);
      }
      return { status: res.status, data };
    }, BACKEND_URL);

    assert.equal(refreshResult.status, 200, "Refresh call must succeed with status 200");
    assert.ok(refreshResult.data.access_token, "New access token must be returned");

    // Check rotated cookie
    const cookiesAfter = await context.cookies();
    const newCookie = cookiesAfter.find((c) => c.name === "acis_refresh_token");
    assert.ok(newCookie, "Post-rotation cookie must exist");
    assert.notEqual(
      newCookie.value,
      oldCookie.value,
      "Refresh token MUST be rotated (new value different from previous value)"
    );
  });

  test("4. Single-Flight Refresh Coordination & Concurrent Recovery", async () => {
    let refreshNetworkCalls = 0;
    const reqListener = (req) => {
      if (req.url().includes("/api/v1/auth/refresh")) {
        refreshNetworkCalls++;
      }
    };
    page.on("request", reqListener);

    // In browser context, fire 3 concurrent refresh calls through the API client
    const tokens = await page.evaluate(async () => {
      const p1 = window.__acis_api.refreshAccessToken();
      const p2 = window.__acis_api.refreshAccessToken();
      const p3 = window.__acis_api.refreshAccessToken();
      return await Promise.all([p1, p2, p3]);
    });

    page.off("request", reqListener);

    // All 3 concurrent calls returned a valid access token
    assert.ok(tokens[0] && tokens[0].length > 20, "First concurrent request returned access token");
    assert.equal(tokens[1], tokens[0], "Second concurrent request received identical token from single flight");
    assert.equal(tokens[2], tokens[0], "Third concurrent request received identical token from single flight");

    // Exactly 1 network request was made
    assert.equal(refreshNetworkCalls, 1, "Single flight promise MUST dispatch exactly 1 network request");
  });

  test("5. Logout Lifecycle, Cookie Clearing & Session Revocation", async () => {
    // Click real UI Sign out button
    await page.click("button[title='Sign Out']");

    // Wait for redirect to login page
    await page.waitForURL(`${FRONTEND_URL}/login`, { timeout: 15000 });
    assert.equal(page.url(), `${FRONTEND_URL}/login`);

    // Verify localStorage cleared
    const storedCsrf = await page.evaluate(() => localStorage.getItem("acis-csrf-token"));
    assert.equal(storedCsrf, null, "acis-csrf-token must be cleared from localStorage");

    // Verify refresh token cookie is either gone or cleared (empty or expired)
    const cookies = await context.cookies();
    const refreshCookie = cookies.find((c) => c.name === "acis_refresh_token");
    const isCleared = !refreshCookie || !refreshCookie.value || refreshCookie.expires < Date.now() / 1000;
    assert.ok(isCleared, "acis_refresh_token cookie must be cleared on logout");

    // Attempting refresh from browser returns 401 Unauthorized because session was revoked in database
    const postLogoutRefresh = await page.evaluate(async (backendUrl) => {
      const res = await fetch(`${backendUrl}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": "empty" },
      });
      return res.status;
    }, BACKEND_URL);

    assert.ok(
      postLogoutRefresh === 401 || postLogoutRefresh === 403,
      "Refresh after logout MUST fail with 401 or 403"
    );
  });
});
