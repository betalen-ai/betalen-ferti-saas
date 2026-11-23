import { describe, expect, it, vi } from "vitest";
import { loginWithApi } from "./api-auth";

describe("API sign-in", () => {
  it("posts the shop subdomain, email, and password and returns an expiring profile", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "test-token",
          token_type: "bearer",
          expires_in: 3600,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const session = await loginWithApi(
      {
        subdomain: " GreenValley ",
        email: " Owner@Example.com ",
        password: "private",
      },
      request,
    );

    expect(request).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          subdomain: "greenvalley",
          email: "owner@example.com",
          password: "private",
        }),
      }),
    );
    expect(session.profile).toEqual({ subdomain: "greenvalley", email: "owner@example.com" });
    expect(session.accessToken).toBe("test-token");
    expect(session.tokenType).toBe("bearer");
    expect(session.expiresAt).toBeGreaterThan(Date.now());
  });

  it("reports invalid credentials without exposing backend details", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ detail: "invalid_credentials" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(
      loginWithApi(
        { subdomain: "greenvalley", email: "owner@example.com", password: "wrong" },
        request,
      ),
    ).rejects.toThrow("The subdomain, email, or password is incorrect.");
  });
});
