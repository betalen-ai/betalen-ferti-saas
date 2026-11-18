import { Link, useRouterState } from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";
import { getCurrentAdmin } from "@/lib/backoffice.functions";
import { BarChart3, Bell, Boxes, Building2, CreditCard, FileText, LayoutDashboard, Menu, Package, ReceiptText, Search, Settings, ShieldCheck, Sprout, Users, Wallet, Warehouse, BadgeIndianRupee, X } from "lucide-react";

const groups = [
  { label: "Overview", items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }] },
  { label: "Organization", items: [
    { to: "/tenants", label: "Tenants", icon: Building2 },
    { to: "/users", label: "Users", icon: Users },
    { to: "/roles", label: "Roles & permissions", icon: ShieldCheck },
    { to: "/subscriptions", label: "Subscriptions", icon: BadgeIndianRupee },
  ] },
  { label: "Inventory", items: [
    { to: "/products", label: "Products", icon: Package },
    { to: "/stock", label: "Stock & batches", icon: Boxes },
    { to: "/warehouses", label: "Warehouses", icon: Warehouse },
  ] },
  { label: "Billing", items: [
    { to: "/invoices", label: "Invoices", icon: ReceiptText },
    { to: "/payments", label: "Payments", icon: CreditCard },
    { to: "/credit-ledger", label: "Credit ledger", icon: Wallet },
  ] },
  { label: "Content & insights", items: [
    { to: "/content", label: "Content", icon: FileText },
    { to: "/reports", label: "Reports", icon: BarChart3 },
    { to: "/settings", label: "Settings", icon: Settings },
  ] },
] as const;

export function AdminShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [account, setAccount] = useState<{ displayName: string | null; email: string | null } | null>(null);
  const navigate = useNavigate();
  useEffect(() => { void getCurrentAdmin().then(setAccount).catch(() => setAccount(null)); }, []);
  const path = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="flex min-h-screen bg-background">
      <aside className={`fixed inset-y-0 left-0 z-40 w-64 overflow-y-auto bg-sidebar text-sidebar-foreground transition-transform lg:static lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="grid size-9 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"><Sprout className="size-5" /></div>
          <div><p className="font-display text-lg font-bold leading-none">Betalen</p><p className="text-xs opacity-70">Ferti backoffice</p></div>
          <button className="ml-auto lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu"><X className="size-5" /></button>
        </div>
        <nav className="space-y-5 px-3 pb-6">
          {groups.map((g) => (
            <div key={g.label}>
              <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider opacity-50">{g.label}</p>
              {g.items.map((it) => {
                const active = path === it.to || path.startsWith(`${it.to}/`);
                return (
                  <Link key={it.to} to={it.to} onClick={() => setOpen(false)} className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${active ? "bg-sidebar-primary font-semibold text-sidebar-primary-foreground" : "hover:bg-sidebar-accent"}`}>
                    <it.icon className="size-4" />{it.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
      {open && <div className="fixed inset-0 z-30 bg-foreground/40 lg:hidden" onClick={() => setOpen(false)} />}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-card/90 px-4 backdrop-blur md:px-8">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu className="size-5" /></button>
          <div className="relative hidden max-w-sm flex-1 md:block">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input placeholder="Search tenants, invoices, products…" className="h-9 w-full rounded-lg border bg-muted pl-9 pr-3 text-sm outline-none focus:ring-1 focus:ring-ring" />
          </div>
          <div className="ml-auto flex items-center gap-4">
            <button aria-label="Notifications" className="relative"><Bell className="size-5 text-muted-foreground" /><span className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-destructive" /></button>
            <div className="flex items-center gap-2"><div className="grid size-8 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{(account?.displayName ?? account?.email ?? "A").slice(0, 2).toUpperCase()}</div><div className="hidden text-sm sm:block"><p className="font-semibold leading-none">{account?.displayName ?? "Administrator"}</p><p className="text-xs text-muted-foreground">{account?.email ?? "Signed in"}</p></div><button aria-label="Sign out" title="Sign out" className="ml-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted" onClick={async () => { await supabase.auth.signOut(); await navigate({ to: "/auth", replace: true }); }}>Sign out</button></div>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
