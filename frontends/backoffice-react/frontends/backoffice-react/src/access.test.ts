import { describe, expect, it } from "vitest";
import { canEnterBackoffice } from "./access";

describe("backoffice access", () => {
  it("allows platform administrators", () => {
    expect(canEnterBackoffice(["platform_admin"])).toBe(true);
  });

  it("does not allow other organization roles", () => {
    expect(canEnterBackoffice(["shop_owner", "manager", "cashier"])).toBe(false);
  });

  it("denies users without roles", () => {
    expect(canEnterBackoffice([])).toBe(false);
  });
});