import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Sprout } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/auth")({
  head: () => ({ meta: [
    { title: "Administrator sign in — Betalen Backoffice" },
    { name: "description", content: "Sign in to the private Betalen organization backoffice." },
    { property: "og:title", content: "Administrator sign in — Betalen Backoffice" },
    { property: "og:description", content: "Sign in to the private Betalen organization backoffice." },
  ] }),
  component: AuthPage,
});

function AuthPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const { error } = await supabase.auth.signInWithPassword({
      email: String(form.get("email")),
      password: String(form.get("password")),
    });
    setLoading(false);
    if (error) { toast.error(error.message); return; }
    await navigate({ to: "/dashboard" });
  };
  return (
    <main className="grid min-h-screen place-items-center bg-background p-4">
      <section className="w-full max-w-md rounded-xl border bg-card p-7 shadow-sm">
        <div className="mb-7 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-lg bg-primary text-primary-foreground"><Sprout /></span><div><p className="font-display text-xl font-bold">Betalen</p><p className="text-xs text-muted-foreground">Ferti backoffice</p></div></div>
        <h1 className="text-2xl font-bold">Administrator sign in</h1>
        <p className="mt-1 text-sm text-muted-foreground">Use your invited administrator account to continue.</p>
        <form onSubmit={submit} className="mt-6 grid gap-4">
          <div className="grid gap-1.5"><Label htmlFor="email">Email</Label><Input id="email" name="email" type="email" autoComplete="username" required /></div>
          <div className="grid gap-1.5"><Label htmlFor="password">Password</Label><Input id="password" name="password" type="password" autoComplete="current-password" required /></div>
          <Button disabled={loading} className="mt-1 w-full">{loading ? "Signing in…" : "Sign in"}</Button>
        </form>
      </section>
    </main>
  );
}
