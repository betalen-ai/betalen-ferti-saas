import { useEffect, useMemo, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TableName } from "@/lib/backoffice-data";
import { deleteBackofficeRow, listBackofficeTable, saveBackofficeRow } from "@/lib/backoffice.functions";
import { useServerFn } from "@tanstack/react-start";

const tone: Record<string, string> = {
  active: "bg-success/15 text-success", paid: "bg-success/15 text-success", published: "bg-success/15 text-success", settled: "bg-success/15 text-success", "within limit": "bg-success/15 text-success",
  trial: "bg-warning/20 text-accent-foreground", draft: "bg-warning/20 text-accent-foreground", credit: "bg-warning/20 text-accent-foreground", partial: "bg-warning/20 text-accent-foreground", free: "bg-muted text-muted-foreground",
  suspended: "bg-destructive/15 text-destructive", expired: "bg-destructive/15 text-destructive", overdue: "bg-destructive/15 text-destructive", inactive: "bg-destructive/15 text-destructive",
};
const money = new Set(["amount", "price", "balance", "credit_limit"]);
const title = (k: string) => k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export function StatusPill({ value }: { value: string }) {
  return <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${tone[value] ?? "bg-secondary text-secondary-foreground"}`}>{value}</span>;
}

export function CrudPage({ title: heading, description, entity, table, initial }: { title: string; description: string; entity: string; table: TableName; initial: Record<string, string | number> }) {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [loaded, setLoaded] = useState(false);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);
  const [saving, setSaving] = useState(false);
  const listFn = useServerFn(listBackofficeTable);
  const saveFn = useServerFn(saveBackofficeRow);
  const deleteFn = useServerFn(deleteBackofficeRow);
  const cols = Object.keys(initial);

  useEffect(() => {
    let active = true;
    void listFn({ data: { table } }).then((result) => {
      if (active) { setRows(result as Array<Record<string, unknown>>); setLoaded(true); }
    }).catch((error: unknown) => {
      if (active) { setLoaded(true); toast.error(error instanceof Error ? error.message : "Could not load records"); }
    });
    return () => { active = false; };
  }, [listFn, table]);
  const filtered = useMemo(() => rows.filter((r) => Object.values(r).join(" ").toLowerCase().includes(q.toLowerCase())), [rows, q]);
  const save = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editing) return;
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    const values = Object.fromEntries(cols.filter((c) => c !== "id").map((c) => {
      const raw = String(fd.get(c) ?? "");
      return [c, typeof initial[c] === "number" ? Number(raw) || 0 : raw];
    }));
    try {
      const id = typeof editing["id"] === "string" && editing["id"].length > 24 ? editing["id"] : undefined;
      const saved = await saveFn({ data: id ? { table, values, id } : { table, values } });
      setRows((prev) => id ? prev.map((r) => r["id"] === id ? saved as Record<string, unknown> : r) : [saved as Record<string, unknown>, ...prev]);
      toast.success(`${entity} ${id ? "updated" : "created"}`);
      setEditing(null);
    } catch (error) { toast.error(error instanceof Error ? error.message : `Could not save ${entity.toLowerCase()}`); }
    finally { setSaving(false); }
  };
  const remove = async (row: Record<string, unknown>) => {
    if (typeof row["id"] !== "string") return;
    const id = row["id"];
    try { await deleteFn({ data: { table, id } }); setRows((prev) => prev.filter((x) => x["id"] !== id)); toast.success(`${entity} deleted`); }
    catch (error) { toast.error(error instanceof Error ? error.message : `Could not delete ${entity.toLowerCase()}`); }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-2xl font-bold md:text-3xl">{heading}</h1><p className="text-sm text-muted-foreground">{description}</p></div><Button onClick={() => setEditing({})}><Plus /> New {entity.toLowerCase()}</Button></div>
      <div className="rounded-xl border bg-card shadow-sm"><div className="flex items-center justify-between gap-3 border-b p-4"><div className="relative w-full max-w-xs"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Search ${heading.toLowerCase()}…`} className="pl-9" /></div><p className="text-sm text-muted-foreground">{filtered.length} records</p></div>
        <Table><TableHeader><TableRow>{cols.map((c) => <TableHead key={c} className="px-4">{title(c)}</TableHead>)}<TableHead className="px-4 text-right">Actions</TableHead></TableRow></TableHeader><TableBody>
          {filtered.map((r) => <TableRow key={String(r["id"])}>{cols.map((c) => <TableCell key={c} className="px-4">{c === "status" ? <StatusPill value={String(r[c])} /> : money.has(c) ? `₹${Number(r[c]).toLocaleString("en-IN")}` : c === "id" ? <span className="font-mono text-xs text-muted-foreground">{String(r[c]).slice(0, 8)}</span> : String(r[c] ?? "")}</TableCell>)}<TableCell className="px-4 text-right"><Button size="icon" variant="ghost" aria-label="Edit" onClick={() => setEditing(r)}><Pencil /></Button><Button size="icon" variant="ghost" aria-label="Delete" onClick={() => void remove(r)}><Trash2 className="text-destructive" /></Button></TableCell></TableRow>)}
          {filtered.length === 0 && <TableRow><TableCell colSpan={cols.length + 1} className="py-10 text-center text-muted-foreground">{loaded ? "No records found" : "Loading records…"}</TableCell></TableRow>}
        </TableBody></Table></div>
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}><DialogContent><DialogHeader><DialogTitle>{editing?.["id"] ? "Edit" : "New"} {entity.toLowerCase()}</DialogTitle></DialogHeader><form onSubmit={save} className="grid max-h-[70vh] gap-4 overflow-y-auto">
        {cols.filter((c) => c !== "id" && c !== "created_at").map((c) => <div key={c} className="grid gap-1.5"><Label htmlFor={c}>{title(c)}</Label><Input id={c} name={c} type={typeof initial[c] === "number" ? "number" : c.includes("date") || c.startsWith("valid") || c === "expiry" || c === "updated" ? "date" : "text"} defaultValue={String(editing?.[c] ?? initial[c] ?? "")} required /></div>)}
        <DialogFooter><Button type="button" variant="outline" onClick={() => setEditing(null)}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save"}</Button></DialogFooter>
      </form></DialogContent></Dialog>
    </div>
  );
}
