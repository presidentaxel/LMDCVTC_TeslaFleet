export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

export type HealthResponse = { status: string };

export async function apiHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health failed: ${res.status} ${res.statusText}`);
  return (await res.json()) as HealthResponse;
}

export async function getAuthStatus() {
  const res = await fetch(`${API_BASE}/auth/debug`);
  if (!res.ok) throw new Error(`Auth status failed: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function getAuthorizeUrl() {
  const res = await fetch(`${API_BASE}/auth/authorize-url`);
  if (!res.ok) throw new Error(`Failed to get authorize URL: ${res.status} ${res.statusText}`);
  return res.json();
}