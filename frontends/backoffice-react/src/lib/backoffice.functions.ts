import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import type { TableName } from "@/lib/backoffice-data";
import type { Database, Json } from "@/integrations/supabase/types";

const tables: Record<TableName, keyof Database["public"]["Tables"]> = {
  tenants: "tenants", org_users: "org_users", backoffice_roles: "backoffice_roles", subscriptions: "subscriptions",
  products: "products", stock_batches: "stock_batches", warehouses: "warehouses", invoices: "invoices",
  payments: "payments", credit_ledger: "credit_ledger", content_items: "content_items", platform_settings: "platform_settings",
};
const columns: Record<TableName, string[]> = {
  tenants: ["name", "subdomain", "subscription_plan", "status"],
  org_users: ["tenant_id", "auth_user_id", "email", "full_name", "role_id", "status"],
  backoffice_roles: ["name", "description", "permissions"],
  subscriptions: ["tenant_id", "tenant_name", "plan", "status", "valid_from", "valid_to"],
  products: ["name", "category", "price", "gst", "status"],
  stock_batches: ["product_id", "product_name", "warehouse_id", "warehouse_name", "batch", "quantity", "expiry"],
  warehouses: ["name", "location", "capacity", "status"],
  invoices: ["invoice_number", "customer", "tenant_id", "tenant_name", "amount", "type", "status", "date"],
  payments: ["invoice_id", "invoice_number", "method", "amount", "status", "date"],
  credit_ledger: ["farmer", "tenant_id", "tenant_name", "credit_limit", "balance", "status"],
  content_items: ["title", "slug", "type", "body", "status", "updated"],
  platform_settings: ["setting_key", "setting_value"],
};

export const getCurrentAdmin = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
  const { data: allowed, error: roleError } = await context.supabase.rpc("has_role", { _user_id: context.userId, _role: "platform_admin" });
    if (roleError) throw new Error(roleError.message);
    if (!allowed) throw new Error("Administrator access required");
    const { data, error } = await context.supabase.from("profiles").select("display_name, email").eq("id", context.userId).maybeSingle();
    if (error) throw new Error(error.message);
    return { userId: context.userId, displayName: data?.display_name ?? null, email: data?.email ?? null };
  });

export const listBackofficeTable = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: { table: TableName }) => input)
  .handler(async ({ data, context }) => {
    const { data: allowed, error: roleError } = await context.supabase.rpc("has_role", { _user_id: context.userId, _role: "platform_admin" });
    if (roleError) throw new Error(roleError.message);
    if (!allowed) throw new Error("Administrator access required");
    const table = tables[data.table];
    const result = await context.supabase.from(table).select("*").order("created_at", { ascending: false });
    if (result.error) throw new Error(result.error.message);
    return (result.data ?? []) as unknown as Json[];
  });

export const saveBackofficeRow = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: { table: TableName; values: Record<string, Json>; id?: string }) => input)
  .handler(async ({ data, context }) => {
    const { data: allowed, error: roleError } = await context.supabase.rpc("has_role", { _user_id: context.userId, _role: "platform_admin" });
    if (roleError) throw new Error(roleError.message);
    if (!allowed) throw new Error("Administrator access required");
    const safeValues = Object.fromEntries(Object.entries(data.values).filter(([key]) => columns[data.table].includes(key)));
    const table = tables[data.table];
    let result: { data: unknown; error: { message: string } | null };
    if (data.id) {
      const query = context.supabase.from(table) as unknown as { update: (values: Record<string, Json>) => { eq: (column: string, id: string) => { select: (columns: string) => { single: () => Promise<{ data: unknown; error: { message: string } | null }> } } } };
      result = await query.update(safeValues).eq("id", data.id).select("*").single();
    } else {
      const query = context.supabase.from(table) as unknown as { insert: (values: Record<string, Json>) => { select: (columns: string) => { single: () => Promise<{ data: unknown; error: { message: string } | null }> } } };
      result = await query.insert(safeValues).select("*").single();
    }
    if (result.error) throw new Error(result.error.message);
    return result.data as Json;
  });

export const deleteBackofficeRow = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: { table: TableName; id: string }) => input)
  .handler(async ({ data, context }) => {
    const { data: allowed, error: roleError } = await context.supabase.rpc("has_role", { _user_id: context.userId, _role: "platform_admin" });
    if (roleError) throw new Error(roleError.message);
    if (!allowed) throw new Error("Administrator access required");
    const table = tables[data.table];
    const query = context.supabase.from(table) as unknown as { delete: () => { eq: (column: string, id: string) => Promise<{ error: { message: string } | null }> } };
    const { error } = await query.delete().eq("id", data.id);
    if (error) throw new Error(error.message);
    return { success: true };
  });

export const getDashboardSummary = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { data: allowed, error: roleError } = await context.supabase.rpc("has_role", { _user_id: context.userId, _role: "platform_admin" });
    if (roleError) throw new Error(roleError.message);
    if (!allowed) throw new Error("Administrator access required");
    const [tenants, staff, invoices, recentTenants, recentInvoices] = await Promise.all([
      context.supabase.from("tenants").select("id,status", { count: "exact" }),
      context.supabase.from("org_users").select("id", { count: "exact", head: true }),
      context.supabase.from("invoices").select("id,amount,status,date", { count: "exact" }),
      context.supabase.from("tenants").select("id,name,subdomain,status,subscription_plan").order("created_at", { ascending: false }).limit(4),
      context.supabase.from("invoices").select("id,invoice_number,customer,tenant_name,amount,status,date").order("date", { ascending: false }).limit(5),
    ]);
    for (const result of [tenants, staff, invoices, recentTenants, recentInvoices]) {
      if (result.error) throw new Error(result.error.message);
    }
    const tenantRows = tenants.data ?? [];
    const invoiceRows = invoices.data ?? [];
    return {
      activeTenants: tenantRows.filter((row) => row.status === "active").length,
      tenantCount: tenants.count ?? 0,
      staffCount: staff.count ?? 0,
      invoiceCount: invoices.count ?? 0,
      grossSales: invoiceRows.reduce((sum, row) => sum + Number(row.amount ?? 0), 0),
      collectionsDue: invoiceRows.filter((row) => row.status === "overdue" || row.status === "credit").reduce((sum, row) => sum + Number(row.amount ?? 0), 0),
      recentTenants: recentTenants.data ?? [],
      recentInvoices: recentInvoices.data ?? [],
    };
  });
