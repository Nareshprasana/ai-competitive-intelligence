export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let accessToken = null;
let organizationId = null;

function storeCsrfToken(token) {
  if (typeof window !== "undefined" && token) {
    window.localStorage.setItem("acis-csrf-token", token);
  }
}

function errorMessage(error, fallback) {
  return error.detail || error.message || fallback;
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
  storeCsrfToken(data.csrf_token);
  return data;
}

export async function refreshAccessToken() {
  if (typeof window === "undefined") return null;
  const csrfToken = window.localStorage.getItem("acis-csrf-token");
  if (!csrfToken) return null;
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrfToken },
  });
  if (!response.ok) {
    accessToken = null;
    return null;
  }
  const data = await response.json();
  accessToken = data.access_token;
  storeCsrfToken(data.csrf_token);
  return accessToken;
}

export function setOrganizationId(value) {
  organizationId = value || null;
}

export async function getOrganizations() {
  return authenticatedRequest("/api/v1/auth/organizations", {}, false, false);
}

async function authenticatedRequest(
  path,
  options = {},
  retried = false,
  requiresOrganization = true,
) {
  if (!accessToken) {
    await refreshAccessToken();
  }
  if (!accessToken || (requiresOrganization && !organizationId)) {
    throw new Error(
      requiresOrganization
        ? "Sign in and select an organization to continue."
        : "Sign in to continue.",
    );
  }
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${accessToken}`);
  if (organizationId) headers.set("X-Organization-ID", organizationId);
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (response.status === 401 && !retried && await refreshAccessToken()) {
    return authenticatedRequest(path, options, true, requiresOrganization);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(errorMessage(data, `Request failed (${response.status})`));
  }
  return data;
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
    { cache: "no-store" },
  );
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
        false,
      );
    }
  } finally {
    accessToken = null;
    organizationId = null;
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("acis-csrf-token");
      window.localStorage.removeItem("acis-organization-id");
    }
  }
}

export async function health() {
  const res = await fetch(`${API_URL}/api/v1/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}
