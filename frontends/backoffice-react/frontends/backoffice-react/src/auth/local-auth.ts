export type ApiLoginCredentials = {
  subdomain?: string;
  tenantId?: string;
  email: string;
  password: string;
};

export type ApiAuthSession = {
  expiresAt: number;
  profile: {
    subdomain: string;
    email: string;
  };
};

type LoginResponse = {
  access_token?: unknown;
  token_type?: unknown;
  expires_in?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function loginToApi(
  credentials: ApiLoginCredentials,
  request: typeof fetch = fetch,
): Promise<ApiAuthSession> {
  let response: Response;
  try {
    response = await request("/api/v1/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        subdomain: credentials.subdomain?.trim() || undefined,
        tenant_id: credentials.tenantId?.trim() || undefined,
        email: credentials.email.trim(),
        password: credentials.password,
      }),
    });
  } catch {
    throw new Error("The authentication API is unavailable.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("The authentication API returned an unreadable response.");
  }

  if (!response.ok) {
    const detail = isRecord(payload) && typeof payload.detail === "string" ? payload.detail : "";
    if (detail === "invalid_credentials" || response.status === 401) {
      throw new Error("The subdomain, email, or password is incorrect.");
    }
    throw new Error("The authentication API could not sign you in.");
  }

  const result = payload as LoginResponse;
  if (
    typeof result.access_token !== "string" ||
    result.access_token.length === 0 ||
    typeof result.token_type !== "string" ||
    result.token_type.toLowerCase() !== "bearer" ||
    typeof result.expires_in !== "number" ||
    !Number.isFinite(result.expires_in) ||
    result.expires_in <= 0
  ) {
    throw new Error("The authentication API returned an invalid session.");
  }

  return {
    expiresAt: Date.now() + result.expires_in * 1000,
    profile: {
      subdomain: credentials.subdomain?.trim() ?? "",
      email: credentials.email.trim(),
    },
  };
}