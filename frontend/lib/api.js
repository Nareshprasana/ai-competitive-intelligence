export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function submitResearch(payload) {
  const res = await fetch(`${API_URL}/api/v1/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || `Research submission failed (${res.status})`);
  }
  return res.json();
}

export async function getResearch(researchId) {
  const res = await fetch(`${API_URL}/api/v1/research/${encodeURIComponent(researchId)}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || `Failed to load research (${res.status})`);
  }
  return res.json();
}

export async function health() {
  const res = await fetch(`${API_URL}/api/v1/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}
