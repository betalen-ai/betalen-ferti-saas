export type BackofficeRole = "platform_admin" | "shop_owner" | "manager" | "cashier";

export function canEnterBackoffice(roles: readonly string[]): boolean {
  return roles.includes("platform_admin");
}