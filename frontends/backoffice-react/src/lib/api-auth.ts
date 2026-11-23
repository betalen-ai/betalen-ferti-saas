export type ApiLoginCredentials = {
  subdomain?: string;
  tenantId?: string;
  email: string;
  password: string;
};

export type ApiLoginSession = {
  accessToken: string;
  tokenType: "bearer";
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

export async function loginWithApi(
  credentials: ApiLoginCredentials,
  request: typeof fetch = fetch,
): Promise<ApiLoginSession> {
  const email = credentials.email.trim().toLowerCase();

  let response: Response;
  try {
    response = await request("/api/v1/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        subdomain: credentials.subdomain?.trim() || undefined,
        tenant_id: credentials.tenantId?.trim() || undefined,
        email,
        password: credentials.password,
      }),
    });
  } catch {
    throw new Error("The login API is unavailable. Check that the local API gateway is running.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(
      response.status === 401
        ? "The subdomain, email, or password is incorrect."
        : "The login API returned an unreadable response.",
    );
  }
  function getErrorDetail(payload: unknown): string {
    if (!isRecord(payload)) return "";
    const detail = payload["detail"];
    if (typeof detail === "string") return detail;
    if (isRecord(detail) && typeof detail["code"] === "string") return detail["code"];
    return "";
  }

  if (!response.ok) {
    const detail = getErrorDetail(payload);
    if (response.status === 401 || detail === "invalid_credentials") {
      throw new Error("The subdomain, email, or password is incorrect.");
    }
    throw new Error("The login API could not sign you in.");
  }

  if (!isRecord(payload)) {
    throw new Error("The login API returned an invalid session.");
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
    throw new Error("The login API returned an invalid session.");
  }

  return {
    accessToken: result.access_token,
    tokenType: "bearer",
    expiresAt: Date.now() + result.expires_in * 1000,
    profile: { subdomain: credentials.subdomain?.trim() ?? "", email },
  };
}