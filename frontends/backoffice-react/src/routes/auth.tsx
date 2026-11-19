import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Sprout } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
import greenhouseImage from "@/assets/betalen-greenhouse.jpg";

export const Route = createFileRoute("/auth")({
  head: () => ({ meta: [
    { title: "Administrator sign in — Betalen Backoffice" },
    { name: "description", content: "Sign in to the private Betalen organization backoffice." },
    { property: "og:title", content: "Administrator sign in — Betalen Backoffice" },
    { property: "og:description", content: "Sign in to the private Betalen organization backoffice." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
  ] }),
  component: AuthPage,
});

function AuthPage() {
  const [loading, setLoading] = useState(false);
  const [forgot, setForgot] = useState(false);
  const navigate = useNavigate();
  const sendReset = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    const email = String(new FormData(event.currentTarget).get("email"));
    const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/reset-password` });
    setLoading(false);
    if (error) { toast.error(error.message); return; }
    toast.success("If that email has an account, a reset link is on its way.");
    setForgot(false);
  };
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
    <main className="auth-screen min-h-screen bg-background">
      <div className="auth-layout min-h-screen">
        <aside className="auth-visual" aria-label="Greenhouse growing beds">
          <img className="auth-visual-image" src={greenhouseImage} alt="Rows of fresh produce growing in a bright greenhouse" width={1024} height={1408} />
          <div className="auth-visual-shade" />
          <div className="auth-visual-brand">
            <span className="auth-brand-mark grid size-10 place-items-center rounded-md bg-primary text-primary-foreground"><Sprout className="auth-brand-sprout size-5" /></span>
            <div><p className="font-display text-lg font-bold leading-none">Betalen</p><p className="mt-1 text-xs opacity-80">Ferti backoffice</p></div>
          </div>
          <div className="auth-visual-copy">
            <p className="auth-eyebrow">BETALEN · FERTI</p>
            <p className="font-display text-3xl font-semibold leading-tight">Growing better,<br />together.</p>
            <p className="mt-3 max-w-sm text-sm leading-6 opacity-85">A clearer view of the people, products, and work behind every growing season.</p>
          </div>
          <p className="auth-visual-footnote">A workspace for the people who help things grow.</p>
        </aside>

        <section className="auth-panel flex min-h-screen flex-col justify-center">
          <div className="auth-mobile-brand mb-12 flex items-center gap-3">
            <span className="auth-brand-mark grid size-10 place-items-center rounded-md bg-primary text-primary-foreground"><Sprout className="auth-brand-sprout size-5" /></span>
            <div><p className="font-display text-lg font-bold leading-none">Betalen</p><p className="mt-1 text-xs text-muted-foreground">Ferti backoffice</p></div>
          </div>
          <div className="auth-content w-full">
            <p className="auth-eyebrow text-primary">{forgot ? "ACCOUNT SUPPORT" : "WELCOME BACK"}</p>
            <h1 className="auth-title mt-3 text-3xl font-bold">{forgot ? "Reset your password" : "Administrator sign in"}</h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{forgot ? "Enter your administrator email and we’ll send you a secure reset link." : "Sign in with your invited administrator account to continue."}</p>
            {forgot ? (
              <form onSubmit={sendReset} className="auth-form mt-8 grid gap-5">
                <div className="grid gap-2"><Label htmlFor="reset-email">Email address</Label><Input id="reset-email" name="email" type="email" autoComplete="username" placeholder="name@company.com" required /></div>
                <Button disabled={loading} className="mt-1 h-11 w-full">{loading ? "Sending…" : <>Send reset link <ArrowRight /></>}</Button>
                <Button type="button" variant="ghost" onClick={() => setForgot(false)} className="mx-auto h-8 px-2 text-sm text-muted-foreground">Back to sign in</Button>
              </form>
            ) : (
              <form onSubmit={submit} className="auth-form mt-8 grid gap-5">
                <div className="grid gap-2"><Label htmlFor="email">Email address</Label><Input id="email" name="email" type="email" autoComplete="username" placeholder="name@company.com" required /></div>
                <div className="grid gap-2"><div className="flex items-center justify-between"><Label htmlFor="password">Password</Label><Button type="button" variant="link" onClick={() => setForgot(true)} className="h-auto p-0 text-xs font-medium">Forgot password?</Button></div><Input id="password" name="password" type="password" autoComplete="current-password" placeholder="Enter your password" required /></div>
                <Button disabled={loading} className="mt-1 h-11 w-full">{loading ? "Signing in…" : <>Sign in <ArrowRight /></>}</Button>
              </form>
            )}
          </div>
          <p className="auth-footer mt-12 text-xs text-muted-foreground">Private administrator access <span aria-hidden="true">·</span> Betalen Ferti</p>
        </section>
      </div>
    </main>
  );
}
