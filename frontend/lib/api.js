/**
 * ACIS Centralized API Client
 *
 * Implements token & session management with HttpOnly refresh cookies,
 * CSRF protection, tenant isolation via X-Organization-ID header,
 * normalized error handling, non-idempotent submission safety, and
 * multi-format report downloads.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : "";

let accessToken = null;
let organizationId = null;
let currentUser = null;
let refreshPromise = null;

function storeCsrfToken(token) {
  if (typeof window !== "undefined" && token) {
    window.localStorage.setItem("acis-csrf-token", token);
  }
}

function getStoredCsrfToken() {
  if (typeof window !== "undefined") {
    return window.localStorage.getItem("acis-csrf-token");
  }
  return null;
}

function errorMessage(error, fallback) {
  if (error && typeof error === "object") {
    return error.detail || error.message || fallback;
  }
  return fallback;
}

export function safeUrl(url) {
  if (!url || typeof url !== "string") return "#";
  const trimmed = url.trim();
  if (/^(javascript|data|vbscript):/i.test(trimmed)) {
    return "#";
  }
  return trimmed;
}

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function setOrganizationId(value) {
  organizationId = value || null;
  if (typeof window !== "undefined") {
    if (value) {
      window.localStorage.setItem("acis-organization-id", value);
    } else {
      window.localStorage.removeItem("acis-organization-id");
    }
  }
}

export function getOrganizationId() {
  if (!organizationId && typeof window !== "undefined") {
    organizationId = window.localStorage.getItem("acis-organization-id");
  }
  return organizationId;
}

export function setCurrentUser(user) {
  currentUser = user;
}

export function getCurrentUser() {
  return currentUser;
}

export async function login(email, password) {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(errorMessage(data, `Sign-in failed (${response.status})`));
  }
  accessToken = data.access_token;
  currentUser = data.user || null;
  storeCsrfToken(data.csrf_token);
  return data;
}

export async function refreshAccessToken() {
  if (typeof window === "undefined") return null;
  const csrfToken = getStoredCsrfToken();
  if (!csrfToken) return null;

  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": csrfToken },
      });
      if (!response.ok) {
        accessToken = null;
        return null;
      }
      const data = await response.json().catch(() => ({}));
      accessToken = data.access_token;
      if (data.user) currentUser = data.user;
      storeCsrfToken(data.csrf_token);
      return accessToken;
    } catch {
      accessToken = null;
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function logout() {
  try {
    if (!accessToken) {
      await refreshAccessToken();
    }
    if (accessToken) {
      await authenticatedRequest(
        "/api/v1/auth/logout",
        { method: "POST" },
        false,
        false
      );
    }
  } catch {
    // Non-blocking cleanup on logout
  } finally {
    accessToken = null;
    organizationId = null;
    currentUser = null;
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("acis-csrf-token");
      window.localStorage.removeItem("acis-organization-id");
    }
  }
}

export async function getOrganizations() {
  return authenticatedRequest("/api/v1/auth/organizations", {}, false, false);
}

export async function inviteUser({ email, role }) {
  return authenticatedRequest("/api/v1/auth/invite", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, role }),
  });
}

export async function acceptInvitation(token, { full_name, password }) {
  const res = await fetch(`${API_URL}/api/v1/auth/invitations/${encodeURIComponent(token)}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(errorMessage(data, `Failed to accept invitation (${res.status})`));
  }
  return data;
}

export async function authenticatedRequest(
  path,
  options = {},
  retried = false,
  requiresOrganization = true
) {
  if (!accessToken) {
    await refreshAccessToken();
  }
  const activeOrg = getOrganizationId();
  if (!accessToken || (requiresOrganization && !activeOrg)) {
    throw new Error(
      requiresOrganization
        ? "Sign in and select an organization to continue."
        : "Sign in to continue."
    );
  }
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${accessToken}`);
  if (activeOrg) headers.set("X-Organization-ID", activeOrg);

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  // Handle 401 token expiry retry (strictly idempotent)
  if (response.status === 401 && !retried && (await refreshAccessToken())) {
    // Never auto-retry research creation (prevent accidental duplicate runs)
    if (options.method === "POST" && path.startsWith("/api/v1/research") && !path.includes("/evidence/")) {
      throw new Error("Session expired during submission. Please sign in again.");
    }
    return authenticatedRequest(path, options, true, requiresOrganization);
  }

  // Handle blob responses (e.g. PDF downloads)
  if (options.asBlob) {
    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errorMessage(errJson, `Download failed (${response.status})`));
    }
    return response.blob();
  }

  // Handle raw text responses (e.g. Markdown downloads)
  if (options.asText) {
    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errorMessage(errJson, `Download failed (${response.status})`));
    }
    return response.text();
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(errorMessage(data, `Request failed (${response.status})`));
  }
  return data;
}

/* =============================================================================
   Research Intelligence APIs
============================================================================= */

export async function listResearch({ limit = 50, offset = 0 } = {}) {
  return authenticatedRequest(`/api/v1/research?limit=${limit}&offset=${offset}`, {
    cache: "no-store",
  });
}

export async function submitResearch(payload) {
  return authenticatedRequest("/api/v1/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getResearch(researchId) {
  return authenticatedRequest(
    `/api/v1/research/${encodeURIComponent(researchId)}`,
    { cache: "no-store" }
  );
}

export async function reviewEvidence(researchId, evidenceId, { decision, analyst_notes, override_confidence }) {
  return authenticatedRequest(
    `/api/v1/research/${encodeURIComponent(researchId)}/evidence/${encodeURIComponent(evidenceId)}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision,
        analyst_notes: analyst_notes || null,
        override_confidence: typeof override_confidence === "number" ? override_confidence : null,
      }),
    }
  );
}

export async function getEvidenceReviews(researchId, evidenceId) {
  const path = evidenceId
    ? `/api/v1/research/${encodeURIComponent(researchId)}/evidence/${encodeURIComponent(evidenceId)}/reviews`
    : `/api/v1/research/${encodeURIComponent(researchId)}/evidence/reviews`;
  return authenticatedRequest(path, { cache: "no-store" });
}

/* =============================================================================
   Strategic Report APIs
============================================================================= */

export async function getReport(researchId) {
  return authenticatedRequest(
    `/api/v1/research/${encodeURIComponent(researchId)}/report`,
    { cache: "no-store" }
  );
}

export async function downloadReportPdf(researchId) {
  const safeId = String(researchId).replace(/[^a-zA-Z0-9_-]/g, "");
  const blob = await authenticatedRequest(
    `/api/v1/research/${encodeURIComponent(researchId)}/report/pdf`,
    { asBlob: true, cache: "no-store" }
  );
  if (typeof window !== "undefined") {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `acis-report-${safeId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => {
      try {
        window.URL.revokeObjectURL(url);
      } catch {
        // ignore cleanup error
      }
    }, 100);
  }
  return blob;
}

export async function downloadReportMarkdown(researchId) {
  const safeId = String(researchId).replace(/[^a-zA-Z0-9_-]/g, "");
  const text = await authenticatedRequest(
    `/api/v1/research/${encodeURIComponent(researchId)}/report/markdown`,
    { asText: true, cache: "no-store" }
  );
  if (typeof window !== "undefined") {
    const blob = new Blob([text], { type: "text/markdown; charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `acis-report-${safeId}.md`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => {
      try {
        window.URL.revokeObjectURL(url);
      } catch {
        // ignore cleanup error
      }
    }, 100);
  }
  return text;
}

export async function health() {
  const res = await fetch(`${API_URL}/api/v1/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

if (typeof window !== "undefined") {
  window.__acis_api = {
    refreshAccessToken,
    authenticatedRequest,
    getAccessToken,
    setAccessToken,
    logout,
    login,
    reviewEvidence,
    getReport,
    downloadReportPdf,
    downloadReportMarkdown,
  };
}
