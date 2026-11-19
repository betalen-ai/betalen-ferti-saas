export type TableName =
  | "tenants" | "org_users" | "backoffice_roles" | "subscriptions"
  | "products" | "stock_batches" | "warehouses" | "invoices"
  | "payments" | "credit_ledger" | "content_items" | "platform_settings";

export type Field = {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "email" | "select" | "textarea";
  options?: string[];
  required?: boolean;
  wide?: boolean;
};

export type PageConfig = {
  label: string;
  singular: string;
  description: string;
  table: TableName;
  fields: Field[];
};

const activeStatus = ["active", "inactive", "suspended"];
const planChoices = ["free", "starter", "growth", "enterprise"];

export const pageConfigs: Record<string, PageConfig> = {
  tenants: { label: "Tenants", singular: "Tenant", description: "Fertilizer shops registered on the platform.", table: "tenants", fields: [
    { key: "name", label: "Shop name", required: true }, { key: "subdomain", label: "Subdomain" },
    { key: "subscription_plan", label: "Plan", type: "select", options: planChoices, required: true }, { key: "status", label: "Status", type: "select", options: activeStatus, required: true },
  ] },
  users: { label: "Users", singular: "User", description: "Team members and staff accounts across tenants.", table: "org_users", fields: [
    { key: "tenant_id", label: "Tenant ID", required: true }, { key: "email", label: "Email", type: "email", required: true },
    { key: "full_name", label: "Full name" }, { key: "role_id", label: "Role", type: "select" }, { key: "status", label: "Status", type: "select", options: activeStatus, required: true },
  ] },
  roles: { label: "Roles & permissions", singular: "Role", description: "Platform roles and resource permissions.", table: "backoffice_roles", fields: [
    { key: "name", label: "Role name", required: true }, { key: "description", label: "Description", wide: true },
    { key: "permissions", label: "Permissions (JSON)", type: "textarea", wide: true, required: true },
  ] },
  subscriptions: { label: "Subscriptions", singular: "Subscription", description: "Plans and validity periods by tenant.", table: "subscriptions", fields: [
    { key: "tenant_id", label: "Tenant ID", required: true }, { key: "plan", label: "Plan", type: "select", options: planChoices, required: true },
    { key: "valid_from", label: "Valid from", type: "date", required: true }, { key: "valid_to", label: "Valid to", type: "date", required: true },
  ] },
  products: { label: "Products", singular: "Product", description: "Fertilizer catalogue and pricing.", table: "products", fields: [
    { key: "name", label: "Product name", required: true }, { key: "category", label: "Category" },
    { key: "price", label: "Price (₹)", type: "number", required: true }, { key: "gst", label: "GST rate", required: true },
    { key: "status", label: "Status", type: "select", options: activeStatus, required: true },
  ] },
  stock: { label: "Stock & batches", singular: "Batch", description: "Batch quantities and expiry tracking.", table: "stock_batches", fields: [
    { key: "product_name", label: "Product", required: true }, { key: "warehouse_name", label: "Warehouse", required: true },
    { key: "batch", label: "Batch number", required: true }, { key: "quantity", label: "Quantity", type: "number", required: true },
    { key: "expiry", label: "Expiry", type: "date" },
  ] },
  warehouses: { label: "Warehouses", singular: "Warehouse", description: "Godowns and shop storage locations.", table: "warehouses", fields: [
    { key: "name", label: "Warehouse name", required: true }, { key: "location", label: "Location", required: true },
    { key: "capacity", label: "Capacity", type: "number", required: true }, { key: "status", label: "Status", type: "select", options: activeStatus, required: true },
  ] },
  invoices: { label: "Invoices", singular: "Invoice", description: "Shop and farmer billing records.", table: "invoices", fields: [
    { key: "invoice_number", label: "Invoice number", required: true }, { key: "customer", label: "Customer", required: true },
    { key: "tenant_name", label: "Tenant", required: true }, { key: "amount", label: "Amount (₹)", type: "number", required: true },
    { key: "type", label: "Tax type", type: "select", options: ["GST", "non-GST"], required: true },
    { key: "status", label: "Status", type: "select", options: ["paid", "draft", "partial", "overdue"], required: true },
    { key: "date", label: "Invoice date", type: "date", required: true },
  ] },
  payments: { label: "Payments", singular: "Payment", description: "Recorded payment settlements.", table: "payments", fields: [
    { key: "invoice_number", label: "Invoice number", required: true }, { key: "method", label: "Method", type: "select", options: ["Cash", "UPI", "Bank transfer", "Card"], required: true },
    { key: "amount", label: "Amount (₹)", type: "number", required: true }, { key: "status", label: "Status", type: "select", options: ["settled", "pending", "failed"], required: true },
    { key: "date", label: "Payment date", type: "date", required: true },
  ] },
  "credit-ledger": { label: "Credit ledger", singular: "Ledger entry", description: "Credit limits and balances by farmer.", table: "credit_ledger", fields: [
    { key: "farmer", label: "Farmer", required: true }, { key: "tenant_name", label: "Tenant", required: true },
    { key: "credit_limit", label: "Credit limit (₹)", type: "number", required: true }, { key: "balance", label: "Balance (₹)", type: "number", required: true },
    { key: "status", label: "Status", type: "select", options: ["within limit", "credit", "overdue"], required: true },
  ] },
  content: { label: "Content", singular: "Content item", description: "Pages, announcements and help articles.", table: "content_items", fields: [
    { key: "title", label: "Title", required: true }, { key: "slug", label: "Slug", required: true },
    { key: "type", label: "Type", type: "select", options: ["Page", "Announcement", "Help article"], required: true },
    { key: "body", label: "Body", type: "textarea", wide: true }, { key: "status", label: "Status", type: "select", options: ["draft", "published"], required: true },
    { key: "updated", label: "Updated", type: "date", required: true },
  ] },
  settings: { label: "Settings", singular: "Setting", description: "Platform-level key and value settings.", table: "platform_settings", fields: [
    { key: "setting_key", label: "Setting key", required: true }, { key: "setting_value", label: "Setting value", type: "textarea", wide: true, required: true },
  ] },
};

export const navigationGroups = [
  { label: "Overview", items: [{ key: "dashboard", label: "Dashboard", icon: "dashboard" }] },
  { label: "Organization", items: ["tenants", "users", "roles", "subscriptions"].map((key) => ({ key, label: pageConfigs[key].label, icon: key })) },
  { label: "Inventory", items: ["products", "stock", "warehouses"].map((key) => ({ key, label: pageConfigs[key].label, icon: key })) },
  { label: "Billing", items: ["invoices", "payments", "credit-ledger"].map((key) => ({ key, label: pageConfigs[key].label, icon: key })) },
  { label: "Platform", items: ["content", "settings", "reports"].map((key) => ({ key, label: key === "reports" ? "Reports" : pageConfigs[key].label, icon: key })) },
];

export const headingCase = (value: string) => value.replace(/_/g, " ").replace(/^./, (letter) => letter.toUpperCase());
export const formatMoney = (value: unknown) => `₹${Number(value ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;