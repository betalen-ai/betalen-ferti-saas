import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Sprout } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/reset-password")({
  head: () => ({ meta: [
    { title: "Set a new password — Betalen Backoffice" },
    { name: "description", content: "Choose a new password for your Betalen administrator account." },
    { property: "og:title", content: "Set a new password — Betalen Backoffice" },
    { property: "og:description", content: "Choose a new password for your Betalen administrator account." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
  ] }),
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const { data } = supabase.auth.onAuthStateChange((event) => { if (event === "PASSWORD_RECOVERY") setReady(true); });
    if (window.location.hash.includes("type=recovery")) setReady(true);
    supabase.auth.getSession().then(({ data: s }) => { if (s.session) setReady(true); });
    return () => data.subscription.unsubscribe();
  }, []);
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password"));
    if (password.length < 8) { toast.error("Use at least 8 characters."); return; }
    if (password !== String(form.get("confirm"))) { toast.error("Passwords do not match."); return; }
    setLoading(true);
    const { error } = await supabase.auth.updateUser({ password });
    setLoading(false);
    if (error) { toast.error(error.message); return; }
    toast.success("Password updated.");
    await navigate({ to: "/dashboard" });
  };
  return (
    <main className="auth-screen grid min-h-screen place-items-center bg-background p-4">
      <section className="auth-panel w-full max-w-md rounded-xl border bg-card p-7 shadow-sm">
        <div className="mb-7 flex items-center gap-3"><span className="auth-brand-mark grid size-11 place-items-center rounded-lg bg-primary text-primary-foreground"><Sprout className="auth-brand-sprout" /></span><div><p className="font-display text-xl font-bold">Betalen</p><p className="text-xs text-muted-foreground">Ferti backoffice</p></div></div>
        <h1 className="auth-title text-2xl font-bold">Set a new password</h1>
        {ready ? (
          <form onSubmit={submit} className="auth-form mt-6 grid gap-4">
            <div className="grid gap-1.5"><Label htmlFor="password">New password</Label><Input id="password" name="password" type="password" autoComplete="new-password" required /></div>
            <div className="grid gap-1.5"><Label htmlFor="confirm">Confirm password</Label><Input id="confirm" name="confirm" type="password" autoComplete="new-password" required /></div>
            <Button disabled={loading} className="w-full">{loading ? "Saving…" : "Update password"}</Button>
          </form>
        ) : (
          <p className="auth-form mt-2 text-sm text-muted-foreground">Open this page from the reset link in your email. Links expire, so request a new one if needed.</p>
        )}
      </section>
    </main>
  );
}
