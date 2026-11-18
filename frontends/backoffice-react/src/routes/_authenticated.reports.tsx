import { createFileRoute } from "@tanstack/react-router";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { revenue } from "@/lib/backoffice-data";
export const Route = createFileRoute("/_authenticated/reports")({
  head: () => ({ meta: [{ title: "Reports — Betalen Backoffice" }, { name: "description", content: "Sales and platform activity reports for Betalen." }, { property: "og:title", content: "Reports — Betalen Backoffice" }, { property: "og:description", content: "Sales and platform activity reports for Betalen." }] }),
  component: Reports,
});
function Reports() {
  const download = () => {
    const rows = ["month,revenue,credit", ...revenue.map((r) => `${r.month},${r.revenue},${r.credit}`)].join("\n");
    const url = URL.createObjectURL(new Blob([rows], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "betalen-reports.csv"; a.click(); URL.revokeObjectURL(url);
  };
  return <div className="space-y-6"><div className="flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-3xl font-bold">Reports</h1><p className="text-sm text-muted-foreground">A clear view of activity across the platform.</p></div><Button variant="outline" onClick={download}><Download /> Export CSV</Button></div><div className="grid gap-4 sm:grid-cols-3">{[{ label: "Gross sales", value: `₹${revenue.reduce((a, x) => a + x.revenue, 0).toLocaleString("en-IN")}` }, { label: "Organizations", value: "Saved records" }, { label: "Invoices", value: "Saved records" }].map((x) => <div className="rounded-xl border bg-card p-5" key={x.label}><p className="text-sm text-muted-foreground">{x.label}</p><p className="mt-2 text-2xl font-bold">{x.value}</p></div>)}</div><section className="rounded-xl border bg-card p-5"><h2 className="text-lg font-bold">Sales and recorded credit</h2><p className="mb-4 text-sm text-muted-foreground">Monthly totals · June – November 2026</p><div className="h-[360px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={revenue}><CartesianGrid stroke="var(--border)" strokeDasharray="4 5" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} /><YAxis axisLine={false} tickLine={false} /><Tooltip formatter={(v) => `₹${Number(v).toLocaleString("en-IN")}`} /><Area dataKey="revenue" name="Sales" stroke="var(--primary)" fill="var(--secondary)" /><Area dataKey="credit" name="Credit" stroke="var(--chart-2)" fill="transparent" /></AreaChart></ResponsiveContainer></div></section></div>;
}
