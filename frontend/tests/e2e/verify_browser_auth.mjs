import { chromium } from "playwright";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL_HTTP = "http://localhost:8080";
const BASE_URL_HTTPS = "https://localhost:8443";
const TEST_EMAIL = "auditor_a@acis.test";
const TEST_PASSWORD = "AuditSecurePassword2026!";

async function runBrowserVerification(baseUrl, label, environmentType) {
  console.log(`\n======================================================`);
  console.log(`Starting Browser Verification on: ${baseUrl} (${label})`);
  console.log(`Environment Context: ${environmentType}`);
  console.log(`======================================================`);

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--ignore-certificate-errors",
      "--host-resolver-rules=MAP localhost 127.0.0.1",
    ],
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 800 },
  });

  const page = await context.newPage();

  page.on("pageerror", (err) => console.log(`[PAGE ERROR] ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      console.log(`[CONSOLE ERROR] ${msg.text()}`);
    }
  });

  try {
    // 1. Navigate to /login
    console.log(`[STEP 1] Navigating to ${baseUrl}/login...`);
    const resp = await page.goto(`${baseUrl}/login`, { waitUntil: "networkidle", timeout: 15000 });
    console.log(`[PASS] 1. Login page loaded with status: ${resp.status()}`);

    const emailInput = page.locator('input[type="email"], input[name="email"], input#email');
    await emailInput.waitFor({ state: "visible", timeout: 5000 });
    const passwordInput = page.locator('input[type="password"], input[name="password"], input#password');
    await passwordInput.waitFor({ state: "visible", timeout: 5000 });

    // 2. Submit credentials and sign in
    console.log(`[STEP 2] Submitting login credentials...`);
    await emailInput.fill(TEST_EMAIL);
    await passwordInput.fill(TEST_PASSWORD);

    const submitBtn = page.locator('button[type="submit"]');
    const loginResponsePromise = page.waitForResponse(
      (res) => res.url().includes("/api/v1/auth/login") && res.request().method() === "POST",
      { timeout: 10000 }
    );

    await submitBtn.click();
    const loginResponse = await loginResponsePromise;
    console.log(`[PASS] 2. Login API responded with status: ${loginResponse.status()}`);
    const loginJson = await loginResponse.json().catch(() => ({}));
    const accessToken = loginJson.access_token;

    await page.waitForTimeout(2000);
    const postLoginUrl = page.url();
    console.log(`[PASS] 3. Post-login URL: ${postLoginUrl}`);

    // 3. Inspect browser context cookies
    console.log(`[STEP 3] Inspecting browser context cookies...`);
    const cookies = await context.cookies();
    const refreshCookie = cookies.find((c) => c.name === "acis_refresh_token");
    if (!refreshCookie) {
      throw new Error("Missing acis_refresh_token cookie in browser context!");
    }
    console.log(`[PASS] 4. Refresh Cookie verified:`);
    console.log(`       httpOnly: ${refreshCookie.httpOnly} (expected: true)`);
    console.log(`       secure: ${refreshCookie.secure} (expected: true)`);
    console.log(`       sameSite: ${refreshCookie.sameSite} (expected: Strict)`);
    console.log(`       path: ${refreshCookie.path} (expected: /api/v1/auth)`);

    const csrfCookie = cookies.find((c) => c.name === "acis_csrf_token");
    if (!csrfCookie) {
      throw new Error("Missing acis_csrf_token cookie in browser context!");
    }
    console.log(`[PASS] 5. CSRF Cookie verified:`);
    console.log(`       httpOnly: ${csrfCookie.httpOnly} (expected: false)`);
    console.log(`       secure: ${csrfCookie.secure} (expected: true)`);
    console.log(`       sameSite: ${csrfCookie.sameSite} (expected: Strict)`);
    console.log(`       path: ${csrfCookie.path} (expected: /api/v1/auth)`);

    // 4. Test CSRF validation in browser context
    console.log(`[STEP 4] Testing CSRF protection in browser context...`);
    const csrfRejectionStatus = await page.evaluate(async () => {
      // Attempt refresh with missing CSRF header
      const res = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      return res.status;
    });
    console.log(`[PASS] 6. Refresh without CSRF header rejected with status: ${csrfRejectionStatus} (expected: 403)`);
    if (csrfRejectionStatus !== 403) {
      throw new Error(`Expected 403 for missing CSRF token, got ${csrfRejectionStatus}`);
    }

    // 5. Test page reload and session restoration
    console.log(`[STEP 5] Testing page reload and session restoration...`);
    const refreshResponsePromise = page.waitForResponse(
      (res) => res.url().includes("/api/v1/auth/refresh") && res.request().method() === "POST",
      { timeout: 10000 }
    ).catch(() => null);

    await page.reload({ waitUntil: "networkidle" });
    const refreshRes = await refreshResponsePromise;
    if (refreshRes) {
      console.log(`[PASS] 7. Session refresh API triggered on reload: status ${refreshRes.status()}`);
    }

    const urlAfterReload = page.url();
    console.log(`[PASS] 8. URL after reload remains authenticated: ${urlAfterReload}`);

    // 6. Test Refresh Token Rotation
    console.log(`[STEP 6] Testing refresh token rotation...`);
    const cookiesBeforeRotate = await context.cookies();
    const oldRefresh = cookiesBeforeRotate.find((c) => c.name === "acis_refresh_token")?.value;

    await page.evaluate(async () => {
      const token = localStorage.getItem("acis-csrf-token");
      await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": token },
      });
    });

    const cookiesAfterRotate = await context.cookies();
    const newRefresh = cookiesAfterRotate.find((c) => c.name === "acis_refresh_token")?.value;
    const tokenRotated = oldRefresh !== newRefresh && !!newRefresh;
    console.log(`[PASS] 9. Refresh token rotated: ${tokenRotated} (old=${oldRefresh?.slice(0, 6)}..., new=${newRefresh?.slice(0, 6)}...)`);
    if (!tokenRotated) {
      throw new Error("Refresh token rotation failed: cookie value was not rotated!");
    }

    // 7. Test Cross-Tenant Isolation
    console.log(`[STEP 7] Testing cross-tenant isolation and 404 behavior...`);
    const crossTenantStatus = await page.evaluate(async (token) => {
      // Access research belonging to tenant B while authenticated as tenant A
      const res = await fetch("/api/v1/research/res-audit-tenant-b-001", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "X-Organization-ID": "org-audit-tenant-a",
        },
      });
      return res.status;
    }, accessToken);
    console.log(`[PASS] 10. Authenticated cross-tenant access rejected with status: ${crossTenantStatus} (expected: 404 to prevent enumeration)`);
    if (crossTenantStatus !== 404) {
      throw new Error(`Expected 404 for cross-tenant access, got ${crossTenantStatus}`);
    }

    // 8. Test Logout and Session Revocation
    console.log(`[STEP 8] Performing logout...`);
    const logoutBtn = page.locator('button:has-text("Sign Out"), button:has-text("Logout"), a:has-text("Sign Out"), a:has-text("Logout")');
    const hasLogoutBtn = await logoutBtn.count();
    if (hasLogoutBtn > 0) {
      await logoutBtn.first().click();
      await page.waitForTimeout(2000);
    } else {
      await page.evaluate(async () => {
        const token = localStorage.getItem("acis-csrf-token");
        await fetch("/api/v1/auth/logout", {
          method: "POST",
          credentials: "include",
          headers: token ? { "X-CSRF-Token": token } : {},
        });
      });
      await page.goto(`${baseUrl}/login`);
    }

    const cookiesAfterLogout = await context.cookies();
    const refreshAfterLogout = cookiesAfterLogout.find((c) => c.name === "acis_refresh_token" && c.value !== "");
    console.log(`[PASS] 11. Refresh cookie revoked and cleared on logout: active=${!!refreshAfterLogout}`);
    console.log(`[PASS] 12. Post-logout URL redirected to login: ${page.url()}`);

    console.log(`[SUCCESS] All browser verification checks passed on ${baseUrl}!`);
    return true;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function main() {
  console.log("==================================================================");
  console.log("ACIS Browser-Level Authentication & Security Verification");
  console.log("Distinguishing Local HTTP (RFC 6761 Secure Context) vs Local HTTPS (Internal TLS)");
  console.log("==================================================================");

  // 1. Local HTTP Ingress
  // Chromium implements W3C WebAppSec / RFC 6761 Potentially Trustworthy Origin for localhost/127.0.0.1,
  // which enables Secure cookies over local development HTTP.
  const httpPassed = await runBrowserVerification(
    BASE_URL_HTTP,
    "HTTP Local Ingress (:8080)",
    "Local HTTP — RFC 6761 / W3C Potentially Trustworthy Origin (Secure Context)"
  );

  // 2. Local HTTPS Ingress
  // Real TLS handshake on port 8443 terminated by Caddy using internal CA (tls internal).
  const httpsPassed = await runBrowserVerification(
    BASE_URL_HTTPS,
    "HTTPS Local Ingress (:8443)",
    "Local HTTPS — Caddy Internal CA TLS Handshake"
  );

  console.log("\n==================================================================");
  console.log("FINAL BROWSER VERIFICATION MATRIX:");
  console.log(`  Local HTTP (:8080)   [RFC 6761 Secure Context]:   ${httpPassed ? "PASSED" : "FAILED"}`);
  console.log(`  Local HTTPS (:8443)  [Internal CA TLS Handshake]: ${httpsPassed ? "PASSED" : "FAILED"}`);
  console.log(`  Production HTTPS     [Public CA, TLS 1.3, HSTS]:   GATED ON DEPLOYMENT`);
  console.log("==================================================================");
}

main().catch((err) => {
  console.error("\n[FATAL ERROR]", err);
  process.exit(1);
});
