import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
export const Route = createFileRoute("/_authenticated/settings")({
  head: () => ({ meta: [{ title: "Settings — Betalen Backoffice" }, { name: "description", content: "Configure organization and platform settings." }, { property: "og:title", content: "Settings — Betalen Backoffice" }, { property: "og:description", content: "Configure organization and platform settings." }] }),
  component: SettingsPage,
});
function SettingsPage() {
  const [alerts, setAlerts] = useState(true);
  const [maintenance, setMaintenance] = useState(false);
  return <div className="mx-auto max-w-3xl space-y-6"><div><h1 className="text-3xl font-bold">Settings</h1><p className="text-sm text-muted-foreground">Platform defaults and administrator preferences.</p></div><section className="space-y-5 rounded-xl border bg-card p-6"><div><h2 className="text-lg font-bold">Organization</h2><p className="text-sm text-muted-foreground">Platform identity and default locale.</p></div><div className="grid gap-4 sm:grid-cols-2"><div className="grid gap-1.5"><Label htmlFor="org-name">Organization name</Label><Input id="org-name" defaultValue="Betalen Ferti SaaS" /></div><div className="grid gap-1.5"><Label htmlFor="org-email">Support email</Label><Input id="org-email" defaultValue="support@betalen.ai" /></div><div className="grid gap-1.5"><Label htmlFor="org-currency">Currency</Label><Input id="org-currency" defaultValue="INR (₹)" /></div><div className="grid gap-1.5"><Label htmlFor="org-timezone">Timezone</Label><Input id="org-timezone" defaultValue="Asia/Kolkata" /></div></div><Button onClick={() => toast.success("Organization settings saved")}>Save changes</Button></section><section className="space-y-5 rounded-xl border bg-card p-6"><div><h2 className="text-lg font-bold">Platform controls</h2><p className="text-sm text-muted-foreground">Manage platform-wide notifications and availability.</p></div><div className="flex items-center justify-between"><div><p className="font-medium">Admin alerts</p><p className="text-sm text-muted-foreground">Receive notifications for tenant activity.</p></div><Switch checked={alerts} onCheckedChange={setAlerts} aria-label="Admin alerts" /></div><div className="flex items-center justify-between"><div><p className="font-medium">Maintenance mode</p><p className="text-sm text-muted-foreground">Temporarily pause shop access.</p></div><Switch checked={maintenance} onCheckedChange={setMaintenance} aria-label="Maintenance mode" /></div></section></div>;
}
