const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const j = JSON.parse(text);
      detail = j.detail ?? text;
    } catch {
      /* keep text */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export type HealthResponse = { status: string };

export type BusinessStatus = {
  token_active: boolean;
  access_token_preview: string | null;
  client_id_set: boolean;
  client_secret_set: boolean;
  audience: string;
  consent_steps_completed: boolean;
};

export type ConsentGuide = {
  title: string;
  note: string;
  steps: { step: number; title: string; description?: string; url?: string; action?: string }[];
  docs_url: string;
};

export type VehicleListResponse = {
  response?: unknown[];
  count?: number;
  pagination?: Record<string, unknown>;
};

export type CommandCatalog = {
  categories: Record<
    string,
    { name: string; label_fr: string; needs_body: boolean; body_hint: string | null }[]
  >;
  total: number;
};

export function apiHealth() {
  return request<HealthResponse>("/health");
}

export function getConsentGuide() {
  return request<ConsentGuide>("/business/consent-guide");
}

export function getBusinessStatus() {
  return request<BusinessStatus>("/business/status");
}

export function exchangeBusinessCode(authCode: string) {
  return request<{ success: boolean; access_token_preview: string }>("/business/exchange", {
    method: "POST",
    body: JSON.stringify({ auth_code: authCode }),
  });
}

export function revokeBusinessToken() {
  return request<{ ok: boolean }>("/business/token", { method: "DELETE" });
}

export function listBusinessVehicles(page = 1, pageSize = 50) {
  return request<VehicleListResponse>(
    `/business/vehicles?page=${page}&page_size=${pageSize}`,
  );
}

export function getCommandCatalog() {
  return request<CommandCatalog>("/business/commands/catalog");
}

export function runCommand(vehicleRef: string, commandName: string, body?: Record<string, unknown>) {
  return request<{ success: boolean; status_code: number; body: unknown }>(
    `/business/vehicles/${encodeURIComponent(vehicleRef)}/commands/${commandName}`,
    {
      method: "POST",
      body: JSON.stringify({ body: body ?? {} }),
    },
  );
}

export function partnerTokenDebug(refresh = false) {
  return request<Record<string, unknown>>(
    `/fleet/partner/token-debug${refresh ? "?refresh=1" : ""}`,
  );
}

export function partnerRegister() {
  return request<Record<string, unknown>>("/fleet/partner/register", { method: "POST" });
}
