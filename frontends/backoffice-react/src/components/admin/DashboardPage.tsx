import { ArrowDownRight, ArrowUpRight, Building2, CircleAlert, IndianRupee, Sprout, Users, ArrowRight, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { revenue } from "@/lib/backoffice-data";
import { getDashboardSummary } from "@/lib/backoffice.functions";
import { useServerFn } from "@tanstack/react-start";
import { StatusPill } from "./CrudPage";

const cards = [
  { label: "Platform sales", value: "Track sales", change: "Last 6 months", icon: IndianRupee, direction: "up" },
  { label: "Organizations", value: "Manage shops", change: "Tenant accounts", icon: Building2, direction: "up" },
  { label: "Team members", value: "Manage users", change: "Staff access", icon: Users, direction: "up" },
  { label: "Billing", value: "View records", change: "Invoices & collections", icon: CircleAlert, direction: "down" },
];

export function DashboardPage() {
  const summaryFn = useServerFn(getDashboardSummary);
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof getDashboardSummary>> | null>(null);
  useEffect(() => {
    let active = true;
    void summaryFn().then((data) => { if (active) setSummary(data); }).catch(() => undefined);
    return () => { active = false; };
  }, [summaryFn]);
  const cardIcons = [Building2, Users, IndianRupee, CircleAlert];
  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="mb-1 text-sm font-semibold text-primary">Organization overview</p><h1 className="text-3xl font-bold">Good afternoon, Admin</h1><p className="mt-1 text-sm text-muted-foreground">Here’s what’s happening across Betalen today.</p></div>
        <Link to="/tenants"><Button><Plus /> Add a tenant</Button></Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c, i) => { const Icon = cardIcons[i]; const actual = i === 0 ? (summary?.activeTenants ?? 0).toLocaleString() : i === 1 ? (summary?.staffCount ?? 0).toLocaleString() : i === 2 ? `₹${(summary?.grossSales ?? 0).toLocaleString("en-IN")}` : `₹${(summary?.collectionsDue ?? 0).toLocaleString("en-IN")}`; return <section key={c.label} className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">{c.label}</span><span className="grid size-9 place-items-center rounded-lg bg-secondary text-primary">{Icon && <Icon className="size-4" />}</span></div>
          <p className="mt-3 text-2xl font-bold">{actual}</p><p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">{c.direction === "up" ? <ArrowUpRight className="size-3 text-success" /> : <ArrowDownRight className="size-3 text-destructive" />}{c.change}</p>
        </section>; })}
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
        <section className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-start justify-between"><div><h2 className="text-lg font-bold">Sales overview</h2><p className="text-sm text-muted-foreground">Platform-wide shop sales · last 6 months</p></div><Badge variant="secondary">Jun – Nov 2026</Badge></div>
          <div className="h-64"><ResponsiveContainer width="100%" height="100%"><AreaChart data={revenue} margin={{ left: -18, right: 8, top: 10 }}>
            <defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--primary)" stopOpacity={0.24} /><stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02} /></linearGradient></defs>
            <CartesianGrid stroke="var(--border)" strokeDasharray="4 5" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v / 1000}k`} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} /><Tooltip formatter={(v) => `₹${Number(v).toLocaleString("en-IN")}`} contentStyle={{ borderRadius: 10, borderColor: "var(--border)", background: "var(--card)" }} /><Area type="monotone" dataKey="revenue" name="Sales" stroke="var(--primary)" strokeWidth={2.5} fill="url(#salesFill)" /><Area type="monotone" dataKey="credit" name="Credit" stroke="var(--chart-2)" strokeWidth={2} fill="transparent" />
          </AreaChart></ResponsiveContainer></div>
          <div className="flex gap-5 text-xs text-muted-foreground"><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-primary" />Sales</span><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-chart-2" />Credit recorded</span></div>
        </section>
        <section className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="mb-5 flex items-center justify-between"><div><h2 className="text-lg font-bold">Tenant health</h2><p className="text-sm text-muted-foreground">Current shop accounts</p></div><Sprout className="size-5 text-primary" /></div>
          <div className="space-y-4">{summary?.recentTenants.map((t) => <div className="flex items-center gap-3" key={t.id}><div className="grid size-9 shrink-0 place-items-center rounded-lg bg-secondary text-xs font-bold text-secondary-foreground">{t.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}</div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{t.name}</p><p className="text-xs text-muted-foreground">{t.subdomain || "No subdomain"}</p></div><StatusPill value={t.status} /></div>)}{summary?.recentTenants.length === 0 && <p className="text-sm text-muted-foreground">No shops have been added yet.</p>}</div>
          <Link to="/tenants" className="mt-5 flex items-center gap-1 border-t pt-4 text-sm font-semibold text-primary">Manage tenants <ArrowRight className="size-4" /></Link>
        </section>
      </div>
      <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-5"><div><h2 className="text-lg font-bold">Recent invoices</h2><p className="text-sm text-muted-foreground">Latest billing activity across shops</p></div><Link to="/invoices" className="flex items-center gap-1 text-sm font-semibold text-primary">All invoices <ArrowRight className="size-4" /></Link></div>
        <div className="overflow-x-auto"><table className="w-full min-w-[680px] text-sm"><thead><tr className="text-left text-xs uppercase text-muted-foreground">{["Invoice", "Farmer", "Shop", "Amount", "Status", "Date"].map((x) => <th className="px-5 py-3 font-semibold" key={x}>{x}</th>)}</tr></thead><tbody>{summary?.recentInvoices.map((inv) => <tr key={inv.id} className="border-t"><td className="px-5 py-3 font-mono text-xs">{inv.invoice_number}</td><td className="px-5 py-3 font-semibold">{inv.customer}</td><td className="px-5 py-3">{inv.tenant_name}</td><td className="px-5 py-3">₹{Number(inv.amount).toLocaleString("en-IN")}</td><td className="px-5 py-3"><StatusPill value={inv.status} /></td><td className="px-5 py-3 text-muted-foreground">{inv.date}</td></tr>)}</tbody></table>{summary?.recentInvoices.length === 0 && <p className="p-6 text-sm text-muted-foreground">No invoices have been added yet.</p>}</div>
      </section>
    </div>
  );
}
