import { describe, expect, it, vi } from "vitest";
import { loginToLocalApi } from "./local-auth";

describe("local API sign-in", () => {
  it("posts the tenant, email, and password and returns a timed profile session", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      access_token: "local-test-token",
      token_type: "bearer",
      expires_in: 7200,
    }), { status: 200, headers: { "content-type": "application/json" } }));

    const session = await loginToLocalApi({ subdomain: " greenvalley ", email: " owner@example.com ", password: "private" }, request);

    expect(request).toHaveBeenCalledWith("/auth/login", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ subdomain: "greenvalley", email: "owner@example.com", password: "private" }),
    }));
    expect(session.profile).toEqual({ subdomain: "greenvalley", email: "owner@example.com" });
    expect(session.expiresAt).toBeGreaterThan(Date.now());
  });

  it("does not accept or expose invalid credentials", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({ detail: "invalid_credentials" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    }));

    await expect(loginToLocalApi({ subdomain: "greenvalley", email: "owner@example.com", password: "wrong" }, request))
      .rejects.toThrow("The subdomain, email, or password is incorrect.");
  });

  it("keeps only the derived profile and expiry, not the returned bearer token", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      access_token: "local-test-token",
      token_type: "bearer",
      expires_in: 7200,
    }), { status: 200, headers: { "content-type": "application/json" } }));
    const session = await loginToLocalApi({ subdomain: "greenvalley", email: "owner@example.com", password: "private" }, request);

    expect(session).not.toHaveProperty("accessToken");
    expect(session.profile).toEqual({ subdomain: "greenvalley", email: "owner@example.com" });
    expect(session.expiresAt).toBeGreaterThan(Date.now());
  });
});