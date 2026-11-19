import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { createClient, type User } from "@supabase/supabase-js";
import {
  Activity, ArrowUpRight, BadgeIndianRupee, BarChart3, Bell, Boxes, Building2,
  Check, ChevronDown, CircleHelp, CreditCard, FileText, LayoutDashboard, LogOut, Menu, Package,
  Plus, Search, Settings, ShieldCheck, Sprout, TrendingUp, Users, Wallet, Warehouse, X,
} from "lucide-react";
import { canEnterBackoffice } from "../access";
import { loginToLocalApi, type LocalAuthSession } from "../auth/local-auth";
import { formatMoney, headingCase, navigationGroups, pageConfigs, type Field, type TableName } from "./data";

const databaseUrl = window.__BETALEN_CONFIG__?.supabaseUrl;
const publishableKey = window.__BETALEN_CONFIG__?.supabasePublishableKey;
const supabase = databaseUrl && publishableKey ? createClient(databaseUrl, publishableKey) : null;
type Row = Record<string, unknown>;
type PageName = "dashboard" | "reports" | keyof typeof pageConfigs;
const nullableColumns: Partial<Record<TableName, string[]>> = {
  tenants: ["subdomain"], org_users: ["full_name", "role_id"], stock_batches: ["expiry"],
};

const iconMap: Record<string, typeof LayoutDashboard> = {
  dashboard: LayoutDashboard, tenants: Building2, users: Users, roles: ShieldCheck,
  subscriptions: BadgeIndianRupee, products: Package, stock: Boxes, warehouses: Warehouse,
  invoices: FileText, payments: CreditCard, "credit-ledger": Wallet, content: FileText,
  settings: Settings, reports: BarChart3,
};

function readableError(error: unknown) {
  if (!(error instanceof Error)) return "Something went wrong. Please try again.";
  if (error.message.includes("Invalid login credentials")) return "The email or password is incorrect.";
  if (error.message.includes("Failed to fetch")) return "The database could not be reached. Check your connection settings.";
  return error.message;
}

function pathToPage(): PageName {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, "");
  if (path === "" || path === "index.html") return "dashboard";
  if (path === "credit-ledger") return "credit-ledger";
  if (path in pageConfigs || path === "reports" || path === "dashboard") return path as PageName;
  return "dashboard";
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [checking, setChecking] = useState(true);
  const [configError, setConfigError] = useState("");
  const [authError, setAuthError] = useState("");
  const [localSession, setLocalSession] = useState<LocalAuthSession | null>(null);
  const [mobileNav, setMobileNav] = useState(false);
  const [page, setPage] = useState<PageName>(pathToPage);

  const verify = useCallback(async (currentUser: User | null) => {
    setUser(currentUser);
    if (!currentUser || !supabase) {
      setIsAdmin(false);
      setChecking(false);
      return;
    }
    try {
      const { data, error } = await supabase.rpc("has_role", {
        _user_id: currentUser.id,
        _role: "platform_admin",
      });
      if (error) throw error;
      setIsAdmin(canEnterBackoffice(data === true ? ["platform_admin"] : []));
    } catch {
      setIsAdmin(false);
      setAuthError("Administrator access could not be confirmed. Please contact your platform administrator.");
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    if (!supabase) {
      setConfigError("Set the Lovable Cloud project URL and publishable key in this app’s environment before signing in.");
      setChecking(false);
      return;
    }
    void supabase.auth.getSession().then(({ data, error }) => {
      if (error) setAuthError(readableError(error));
      return verify(data.session?.user ?? null);
    }).catch((error: unknown) => {
      setAuthError(readableError(error));
      setChecking(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setChecking(true);
      void verify(session?.user ?? null);
    });
    const onPop = () => setPage(pathToPage());
    window.addEventListener("popstate", onPop);
    return () => {
      data.subscription.unsubscribe();
      window.removeEventListener("popstate", onPop);
    };
  }, [verify]);

  useEffect(() => {
    if (!localSession) return;
    const remaining = localSession.expiresAt - Date.now();
    if (remaining <= 0) {
      setLocalSession(null);
      return;
    }
    const timeout = window.setTimeout(() => setLocalSession(null), remaining);
    return () => window.clearTimeout(timeout);
  }, [localSession]);

  const navigate = (next: PageName) => {
    window.history.pushState({}, "", next === "dashboard" ? "/" : `/${next}`);
    setPage(next);
    setMobileNav(false);
  };

  const signOut = async () => {
    await supabase?.auth.signOut();
    setUser(null);
    setIsAdmin(false);
    setAuthError("");
  };

  const endLocalTest = () => setLocalSession(null);

  if (checking) return <LoadingScreen />;
  if (!user && localSession) return <LocalApiVerified session={localSession} onSignOut={endLocalTest} />;
  if (!user) return <SignInPage error={authError || configError} onClearError={() => setAuthError("")} onLocalAuthenticated={setLocalSession} />;
  if (!isAdmin) return <AccessDenied email={user.email ?? ""} error={authError} onSignOut={() => void signOut()} />;

  return (
    <div className="app-shell">
      {mobileNav && <button className="nav-scrim" aria-label="Close menu" onClick={() => setMobileNav(false)} />}
      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark"><Sprout size={19} strokeWidth={2.2} /></div>
          <div className="brand-name">Betalen<span>Ferti platform</span></div>
          <button className="icon-button sidebar-close" title="Close menu" aria-label="Close menu" onClick={() => setMobileNav(false)}><X size={18} /></button>
        </div>
        <div className="workspace-picker"><div className="workspace-avatar">BF</div><div className="workspace-copy"><strong>Betalen Ferti</strong><span>Platform workspace</span></div><ChevronDown size={15} /></div>
        <nav className="nav-groups" aria-label="Backoffice">
          {navigationGroups.map((group) => <section className="nav-group" key={group.label}>
            <p className="nav-heading">{group.label}</p>
            {group.items.map((item) => {
              const ItemIcon = iconMap[item.icon] ?? LayoutDashboard;
              const active = page === item.key;
              return <button key={item.key} onClick={() => navigate(item.key as PageName)} className={`nav-link ${active ? "nav-link-active" : ""}`} aria-current={active ? "page" : undefined}>
                <ItemIcon size={17} strokeWidth={1.8} /><span>{item.label}</span>
              </button>;
            })}
          </section>)}
        </nav>
        <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><CircleHelp size={17} /></div><div><strong>Need a hand?</strong><span>Contact your workspace admin</span></div></div>
          <button className="profile-row" onClick={() => void signOut()} title="Sign out"><span className="profile-avatar">{(user.email ?? "A").slice(0, 1).toUpperCase()}</span><span className="profile-copy"><strong>{user.email?.split("@")[0] ?? "Administrator"}</strong><span>Platform administrator</span></span><LogOut size={16} /></button>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <button className="icon-button mobile-menu" title="Open menu" aria-label="Open menu" onClick={() => setMobileNav(true)}><Menu size={19} /></button>
          <div className="breadcrumbs"><span>Workspace</span><span className="breadcrumb-divider">/</span><strong>{page === "dashboard" ? "Overview" : pageConfigs[page]?.label ?? headingCase(page)}</strong></div>
          <div className="topbar-actions"><span className="today-date">{new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date())}</span><button className="icon-button notification-button" title="Notifications" aria-label="Notifications"><Bell size={18} /><i /></button><span className="topbar-divider" /><span className="topbar-avatar">{(user.email ?? "A").slice(0, 1).toUpperCase()}</span></div>
        </header>
        <main className="content-area">
          {page === "dashboard" ? <Dashboard onNavigate={navigate} /> : page === "reports" ? <ReportsPage /> : <CrudPage key={page} page={page} />}
        </main>
      </div>
    </div>
  );
}

function LoadingScreen() {
  return <main className="auth-page"><div className="auth-panel"><div className="brand-mark auth-mark"><Sprout size={21} /></div><p className="eyebrow">BETALEN FERTI</p><h1>Securing your workspace</h1><p className="auth-subtitle">Checking your administrator access…</p><span className="spinner" /></div></main>;
}

function SignInPage({ error, onClearError, onLocalAuthenticated }: { error: string; onClearError: () => void; onLocalAuthenticated: (session: LocalAuthSession) => void }) {
  const [mode, setMode] = useState<"workspace" | "local">("workspace");
  const [loading, setLoading] = useState(false);
  const [subdomain, setSubdomain] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState("");

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (mode === "local") {
      setLoading(true);
      setLocalError("");
      onClearError();
      try {
        const session = await loginToLocalApi({ subdomain, email, password });
        onLocalAuthenticated(session);
      } catch (loginError) {
        setLocalError(loginError instanceof Error ? loginError.message : "The local login could not be verified.");
      } finally {
        setLoading(false);
      }
      return;
    }
    if (!supabase) return;
    setLoading(true);
    setLocalError("");
    onClearError();
    const { data, error: signInError } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (signInError) {
      setLocalError(readableError(signInError));
      setLoading(false);
      return;
    }
    if (!data.user) {
      setLocalError("Sign in did not return an account.");
      setLoading(false);
    }
  };

  return <main className="auth-page">
    <div className="auth-decoration"><div className="auth-circle circle-one" /><div className="auth-circle circle-two" /><div className="field-line field-one" /><div className="field-line field-two" /><div className="field-line field-three" /><div className="field-label"><Sprout size={16} /> GROWING TOGETHER</div></div>
    <section className="auth-panel">
      <div className="auth-brand"><div className="brand-mark auth-mark"><Sprout size={20} /></div><span>Betalen <b>Ferti</b></span></div>
      <div className="auth-heading"><p className="eyebrow">{mode === "local" ? "LOCAL API TEST" : "PLATFORM MANAGEMENT"}</p><h1>{mode === "local" ? "Test your API login" : "Welcome back"}</h1><p className="auth-subtitle">{mode === "local" ? "Check credentials against the authentication service running on your computer." : "Sign in to your workspace to continue."}</p></div>
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        {mode === "local" && <><label className="field-label-text" htmlFor="signin-subdomain">Workspace subdomain</label><input id="signin-subdomain" type="text" autoComplete="organization" placeholder="greenvalley" value={subdomain} onChange={(event) => setSubdomain(event.target.value)} required /></>}
        <label className="field-label-text" htmlFor="signin-email">Email address</label>
        <input id="signin-email" type="email" autoComplete="username" placeholder="you@company.com" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <div className="password-label-row"><label className="field-label-text" htmlFor="signin-password">Password</label></div>
        <div className="password-field"><input id="signin-password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} required /><button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "Hide" : "Show"}</button></div>
        {(localError || error) && <p className="form-error" role="alert">{localError || error}</p>}
        <button className="primary-button sign-in-button" type="submit" disabled={loading || (mode === "workspace" && !supabase)}>{loading ? (mode === "local" ? "Checking credentials…" : "Signing in…") : mode === "local" ? "Check local API login" : "Sign in to workspace"}<span>→</span></button>
      </form>
      {mode === "local" ? <><p className="auth-note"><ShieldCheck size={15} /> Local credential check only; workspace data still requires workspace sign-in.</p><button className="auth-mode-toggle" type="button" onClick={() => { setMode("workspace"); setLocalError(""); }}>Back to workspace sign-in</button></> : <><p className="auth-note"><ShieldCheck size={15} /> Private workspace · administrator access only</p><p className="auth-footer">Need access? Contact your platform administrator.</p><button className="auth-mode-toggle" type="button" onClick={() => { setMode("local"); setLocalError(""); }}>Test local API login</button></>}
    </section>
  </main>;
}

function LocalApiVerified({ session, onSignOut }: { session: LocalAuthSession; onSignOut: () => void }) {
  return <main className="auth-page"><section className="auth-panel denied-panel"><div className="brand-mark auth-mark"><ShieldCheck size={20} /></div><p className="eyebrow">LOCAL API TEST</p><h1>Credentials verified</h1><p className="auth-subtitle">{session.profile.email} · {session.profile.subdomain}</p><p className="auth-note">This confirms the local login endpoint accepted the credentials. It does not grant access to workspace records; use workspace sign-in for the CMS.</p><button className="primary-button sign-in-button" onClick={onSignOut}>Return to sign in</button></section></main>;
}

function AccessDenied({ email, error, onSignOut }: { email: string; error: string; onSignOut: () => void }) {
  return <main className="auth-page"><section className="auth-panel denied-panel"><div className="brand-mark auth-mark"><ShieldCheck size={20} /></div><p className="eyebrow">RESTRICTED WORKSPACE</p><h1>Administrator access required</h1><p className="auth-subtitle">{error || `${email} is signed in, but does not have platform administrator access.`}</p><button className="primary-button sign-in-button" onClick={onSignOut}>Sign out and return to sign in</button><p className="auth-footer">Ask a platform administrator to review your access.</p></section></main>;
}

type Stats = { tenants: Row[]; org_users: Row[]; subscriptions: Row[]; invoices: Row[]; payments: Row[]; products: Row[]; stock_batches: Row[] };
const emptyStats: Stats = { tenants: [], org_users: [], subscriptions: [], invoices: [], payments: [], products: [], stock_batches: [] };

function Dashboard({ onNavigate }: { onNavigate: (page: PageName) => void }) {
  const [records, setRecords] = useState<Stats>(emptyStats);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!supabase) return;
    setLoading(true);
    const tables: Array<keyof Stats> = ["tenants", "org_users", "subscriptions", "invoices", "payments", "products", "stock_batches"];
    const results = await Promise.all(tables.map((table) => supabase.from(table).select("*").order("created_at", { ascending: false }).limit(100)));
    const failed = results.find((result) => result.error);
    if (failed?.error) setError(failed.error.message);
    else {
      setError("");
      const values = Object.fromEntries(tables.map((table, index) => [table, results[index].data ?? []])) as Stats;
      setRecords(values);
    }
    setLoading(false);
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  const activeTenants = records.tenants.filter((row) => row.status === "active").length;
  const activeSubs = records.subscriptions.filter((row) => row.status === "active").length;
  const paidRevenue = records.payments.filter((row) => row.status === "settled" || row.status === "paid").reduce((sum, row) => sum + Number(row.amount ?? 0), 0);
  const stats = [
    { label: "Active tenants", value: activeTenants.toLocaleString("en-IN"), change: `${records.tenants.length} total on platform`, icon: Building2, color: "sage", trend: "up" },
    { label: "Registered users", value: records.org_users.length.toLocaleString("en-IN"), change: "Across all tenants", icon: Users, color: "blue", trend: "up" },
    { label: "Active subscriptions", value: activeSubs.toLocaleString("en-IN"), change: `${records.subscriptions.length} total plans`, icon: BadgeIndianRupee, color: "amber", trend: "up" },
    { label: "Payments collected", value: formatMoney(paidRevenue), change: `${records.payments.length} recorded payments`, icon: Wallet, color: "rose", trend: "up" },
  ];
  const monthly = useMemo(() => {
    const now = new Date();
    return Array.from({ length: 6 }, (_, index) => {
      const month = new Date(now.getFullYear(), now.getMonth() - 5 + index, 1);
      const revenue = records.payments.filter((row) => {
        const date = new Date(String(row.date ?? ""));
        return date.getFullYear() === month.getFullYear() && date.getMonth() === month.getMonth() && (row.status === "settled" || row.status === "paid");
      }).reduce((sum, row) => sum + Number(row.amount ?? 0), 0);
      return { month: new Intl.DateTimeFormat("en", { month: "short" }).format(month), revenue };
    });
  }, [records.payments]);
  const maxRevenue = Math.max(1, ...monthly.map((item) => item.revenue));
  const latest = [...records.invoices].sort((a, b) => String(b.date ?? "").localeCompare(String(a.date ?? ""))).slice(0, 5);
  const invoicesByStatus = records.invoices.reduce<Record<string, number>>((all, row) => {
    const status = String(row.status ?? "unknown"); all[status] = (all[status] ?? 0) + 1; return all;
  }, {});

  return <div className="page-content">
    <div className="page-intro"><div><p className="eyebrow">{new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "2-digit", month: "long", year: "numeric" }).format(new Date()).toUpperCase()}</p><h1>Good morning, team <span className="sun-mark">✳</span></h1><p className="subtitle">Here’s what’s happening across your Ferti network today.</p></div><button className="secondary-button date-select" aria-label="Current reporting period">Last 6 months <ChevronDown size={15} /></button></div>
    {error && <div className="inline-error" role="alert">Could not load dashboard records: {error} <button onClick={() => void refresh()}>Try again</button></div>}
    <div className="stats-grid">{stats.map((stat) => <article className="stat-card" key={stat.label}><div className="stat-top"><span>{stat.label}</span><span className={`stat-icon ${stat.color}`}><stat.icon size={18} /></span></div><p className="stat-value">{loading ? <span className="loading-bar" /> : stat.value}</p><p className="stat-foot"><span className="trend-chip"><ArrowUpRight size={13} /> Live</span><span>{stat.change}</span></p></article>)}</div>
    <div className="dashboard-grid">
      <section className="panel revenue-panel"><div className="panel-heading"><div><h2>Revenue overview</h2><p>Settled payments · last 6 months</p></div><button className="icon-button panel-more" title="Open reports" aria-label="Open reports" onClick={() => onNavigate("reports")}><BarChart3 size={18} /></button></div>
        <div className="revenue-total"><strong>{loading ? "—" : formatMoney(paidRevenue)}</strong><span><TrendingUp size={14} /> All time</span></div>
        <div className="chart-wrap"><div className="chart-y-labels"><span>₹{Math.round(maxRevenue / 1000)}k</span><span>₹{Math.round(maxRevenue / 2000)}k</span><span>₹0</span></div><div className="bar-chart" role="img" aria-label="Settled revenue by month">{monthly.map((item) => <div className="bar-item" key={`${item.month}-${item.revenue}`}><span className="bar-tooltip">{formatMoney(item.revenue)}</span><div className="bar-track"><div className="bar-fill" style={{ height: `${Math.max(5, (item.revenue / maxRevenue) * 100)}%` }} /></div><span className="bar-label">{item.month}</span></div>)}</div></div>
      </section>
      <section className="panel quick-panel"><div className="panel-heading"><div><h2>Quick actions</h2><p>Jump into your work</p></div><span className="panel-dot" /></div>
        <div className="quick-list">{[
          { label: "Add a new tenant", detail: "Register a fertilizer shop", icon: Building2, page: "tenants" as PageName, color: "sage" },
          { label: "Invite a user", detail: "Manage team access", icon: Users, page: "users" as PageName, color: "blue" },
          { label: "Add a product", detail: "Update your catalogue", icon: Package, page: "products" as PageName, color: "amber" },
          { label: "View invoices", detail: "Check recent billing", icon: FileText, page: "invoices" as PageName, color: "rose" },
        ].map((action) => <button className="quick-action" key={action.label} onClick={() => onNavigate(action.page)}><span className={`quick-icon ${action.color}`}><action.icon size={17} /></span><span className="quick-text"><strong>{action.label}</strong><span>{action.detail}</span></span><span className="quick-arrow">→</span></button>)}</div>
      </section>
      <section className="panel invoices-panel"><div className="panel-heading"><div><h2>Recent invoices</h2><p>Most recently issued</p></div><button className="text-action" onClick={() => onNavigate("invoices")}>View all <span>→</span></button></div>
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Invoice</th><th>Customer</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead><tbody>{loading ? <tr><td colSpan={5} className="empty-cell">Loading records…</td></tr> : latest.length ? latest.map((row) => <tr key={String(row.id)}><td className="primary-cell">{String(row.invoice_number ?? "—")}</td><td>{String(row.customer ?? "—")}</td><td>{formatMoney(row.amount)}</td><td><StatusPill value={String(row.status ?? "unknown")} /></td><td>{dateLabel(row.date)}</td></tr>) : <tr><td colSpan={5} className="empty-cell">No invoices yet</td></tr>}</tbody></table></div>
      </section>
      <section className="panel distribution-panel"><div className="panel-heading"><div><h2>Invoice status</h2><p>Current billing overview</p></div><button className="icon-button panel-more" title="Open invoices" aria-label="Open invoices" onClick={() => onNavigate("invoices")}><ArrowUpRight size={18} /></button></div>
        <div className="invoice-number"><strong>{loading ? "—" : records.invoices.length}</strong><span>total invoices</span></div>
        <div className="status-bars">{[["Paid", "paid", "green"], ["Pending", "draft", "yellow"], ["Overdue", "overdue", "red"], ["Partial", "partial", "blue"]].map(([label, key, color]) => { const count = invoicesByStatus[key] ?? 0; const percentage = records.invoices.length ? (count / records.invoices.length) * 100 : 0; return <div className="status-row" key={key}><div><span>{label}</span><strong>{loading ? "—" : count}</strong></div><div className="status-track"><span className={`status-fill ${color}`} style={{ width: `${percentage}%` }} /></div></div>; })}</div>
      </section>
    </div>
    <div className="bottom-note"><span className="live-indicator" /> Data is live from your workspace <span className="note-divider">·</span> Last checked just now</div>
  </div>;
}

function dateLabel(value: unknown) {
  if (!value) return "—";
  const parsed = new Date(String(value));
  return Number.isNaN(parsed.valueOf()) ? String(value) : new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(parsed);
}

function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const state = ["active", "paid", "settled", "published", "within limit"].includes(normalized) ? "success" : ["overdue", "suspended", "inactive", "failed"].includes(normalized) ? "danger" : ["trial", "draft", "pending", "partial", "credit"].includes(normalized) ? "warning" : "neutral";
  return <span className={`status-pill status-${state}`}><span />{value.replace(/_/g, " ")}</span>;
}

function CrudPage({ page }: { page: keyof typeof pageConfigs }) {
  const config = pageConfigs[page];
  const [rows, setRows] = useState<Row[]>([]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Row | null>(null);
  const [saving, setSaving] = useState(false);
  const relatedRows = page === "users" || page === "subscriptions" ? "tenants" : null;
  const [tenants, setTenants] = useState<Row[]>([]);
  const [roles, setRoles] = useState<Row[]>([]);
  const load = useCallback(async () => {
    if (!supabase) return;
    setBusy(true);
    const request = supabase.from(config.table).select("*");
    const { data, error: queryError } = config.table === "platform_settings"
      ? await request.order("updated_at", { ascending: false })
      : await request.order("created_at", { ascending: false });
    if (queryError) setError(queryError.message);
    else { setRows((data ?? []) as Row[]); setError(""); }
    setBusy(false);
  }, [config.table]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!supabase || !relatedRows) return;
    void supabase.from(relatedRows).select("id,name").order("name").then(({ data, error: tenantError }) => {
      if (!tenantError) setTenants((data ?? []) as Row[]);
    });
  }, [relatedRows]);
  useEffect(() => {
    if (!supabase || page !== "users") return;
    void supabase.from("backoffice_roles").select("id,name").order("name").then(({ data, error: roleError }) => {
      if (!roleError) setRoles((data ?? []) as Row[]);
    });
  }, [page]);
  const visibleRows = rows.filter((row) => Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(query.toLowerCase())));
  const columns = config.fields.map((field) => field.key);

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!supabase || !editing) return;
    setSaving(true);
    const form = new FormData(event.currentTarget);
    const values: Row = {};
    for (const field of config.fields) {
      const raw = String(form.get(field.key) ?? "").trim();
      if (raw === "" && !field.required) {
        if (nullableColumns[config.table]?.includes(field.key)) values[field.key] = null;
        else values[field.key] = "";
        continue;
      }
      if (field.type === "number") values[field.key] = Number(raw);
      else if (["permissions", "setting_value"].includes(field.key)) {
        try { values[field.key] = JSON.parse(raw || (field.key === "permissions" ? "[]" : "{}")) as unknown; }
        catch { setError(`${field.label} must be valid JSON.`); setSaving(false); return; }
      } else values[field.key] = raw;
    }
    if (config.table === "org_users" && values.role_id === "") values.role_id = null;
    if (config.table === "subscriptions" && !values.status) values.status = "active";
    if (config.table === "stock_batches") {
      values.product_id = null;
      values.warehouse_id = null;
    }
    const id = typeof editing.id === "string" && editing.id ? editing.id : null;
    const result = id
      ? await supabase.from(config.table).update(values).eq("id", id).select("*").single()
      : await supabase.from(config.table).insert(values).select("*").single();
    if (result.error) setError(result.error.message);
    else { setEditing(null); setError(""); await load(); }
    setSaving(false);
  };

  const remove = async (row: Row) => {
    if (!supabase || typeof row.id !== "string" || !window.confirm(`Delete this ${config.singular.toLowerCase()}? This cannot be undone.`)) return;
    const { error: deleteError } = await supabase.from(config.table).delete().eq("id", row.id);
    if (deleteError) setError(deleteError.message);
    else { setRows((existing) => existing.filter((item) => item.id !== row.id)); setError(""); }
  };

  return <div className="page-content records-page">
    <div className="page-intro records-intro"><div><p className="eyebrow">PLATFORM MANAGEMENT</p><h1>{config.label}</h1><p className="subtitle">{config.description}</p></div><button className="primary-button" onClick={() => setEditing({})}><Plus size={16} /> Add {config.singular}</button></div>
    {page === "users" && <div className="info-note"><ShieldCheck size={15} /><span>This directory manages staff records. Login accounts and passwords are created separately through the organization service.</span></div>}
    {error && <div className="inline-error" role="alert">{error}<button onClick={() => void load()}>Refresh</button></div>}
    <section className="panel records-panel"><div className="records-toolbar"><div className="records-search"><Search size={16} /><input aria-label={`Search ${config.label}`} placeholder={`Search ${config.label.toLowerCase()}…`} value={query} onChange={(event) => setQuery(event.target.value)} /></div><span className="records-count">{busy ? "Loading…" : `${visibleRows.length} ${visibleRows.length === 1 ? "record" : "records"}`}</span></div>
      <div className="table-scroll"><table className="data-table records-table"><thead><tr>{columns.map((column) => <th key={column}>{headingCase(column)}</th>)}<th className="action-heading">Actions</th></tr></thead><tbody>
        {busy ? <tr><td colSpan={columns.length + 1} className="empty-cell">Loading records…</td></tr> : visibleRows.length ? visibleRows.map((row) => <tr key={String(row.id)}>{columns.map((column) => <td key={column}>{column === "status" ? <StatusPill value={String(row[column] ?? "—")} /> : renderCell(column, row[column])}</td>)}<td className="row-actions"><button className="table-action" onClick={() => setEditing(row)} aria-label={`Edit ${config.singular.toLowerCase()}`} title="Edit"><Settings size={15} /></button><button className="table-action delete-action" onClick={() => void remove(row)} aria-label={`Delete ${config.singular.toLowerCase()}`} title="Delete"><X size={16} /></button></td></tr>) : <tr><td colSpan={columns.length + 1} className="empty-cell">{query ? "No matching records" : `No ${config.label.toLowerCase()} yet`}</td></tr>}
      </tbody></table></div>
    </section>
    {editing && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !saving) setEditing(null); }}><section className="edit-modal" role="dialog" aria-modal="true" aria-labelledby="edit-title"><div className="modal-heading"><div><p className="eyebrow">{editing.id ? "UPDATE RECORD" : "NEW RECORD"}</p><h2 id="edit-title">{editing.id ? "Edit" : "Add"} {config.singular}</h2></div><button className="icon-button" title="Close" aria-label="Close" onClick={() => setEditing(null)}><X size={18} /></button></div><form onSubmit={(event) => void save(event)}><div className="form-grid">{config.fields.map((field) => <FieldInput key={field.key} field={field} initial={editing[field.key] ?? (field.key === "permissions" ? [] : field.key === "setting_value" ? {} : undefined)} relatedRows={tenants} roleRows={roles} />)}{page === "subscriptions" && <FieldInput field={{ key: "status", label: "Status", type: "select", options: ["active", "trial", "expired"], required: true }} initial={editing.status ?? "active"} relatedRows={tenants} />}</div><div className="modal-actions"><button className="secondary-button" type="button" onClick={() => setEditing(null)} disabled={saving}>Cancel</button><button className="primary-button" type="submit" disabled={saving}><Check size={15} />{saving ? "Saving…" : "Save record"}</button></div></form></section></div>}
  </div>;
}

function renderCell(column: string, value: unknown) {
  if (value == null || value === "") return <span className="empty-value">—</span>;
  if (["price", "amount", "balance", "credit_limit"].includes(column)) return formatMoney(value);
  if (typeof value === "object") return <span className="json-preview">{JSON.stringify(value)}</span>;
  if (column === "id" || column.endsWith("_id")) return <span className="id-preview" title={String(value)}>{String(value).slice(0, 8)}…</span>;
  if (column.includes("date") || column === "updated" || column === "valid_from" || column === "valid_to" || column === "expiry") return dateLabel(value);
  return String(value);
}

function FieldInput({ field, initial, relatedRows = [], roleRows = [] }: { field: Field; initial: unknown; relatedRows?: Row[]; roleRows?: Row[] }) {
  const [value, setValue] = useState(() => {
    if (initial == null) return "";
    if (typeof initial === "object") return JSON.stringify(initial, null, 2);
    return field.type === "date" ? String(initial).slice(0, 10) : String(initial);
  });
  const shared = { id: field.key, name: field.key, value, onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setValue(event.target.value), required: field.required };
  return <label className={`form-field ${field.wide ? "field-wide" : ""}`}><span>{field.label}{field.required && <i> *</i>}</span>
    {field.key === "tenant_id" ? <select {...shared}><option value="">Select tenant</option>{relatedRows.map((row) => <option key={String(row.id)} value={String(row.id)}>{String(row.name)} · {String(row.id).slice(0, 8)}</option>)}</select> : field.key === "role_id" ? <select {...shared}><option value="">No role assigned</option>{roleRows.map((row) => <option key={String(row.id)} value={String(row.id)}>{String(row.name)}</option>)}</select> : field.type === "textarea" || field.key === "permissions" || field.key === "setting_value" ? <textarea {...shared} rows={field.key === "body" || field.key === "setting_value" ? 5 : 3} placeholder={field.key === "permissions" ? '["products:read"]' : field.key === "setting_value" ? '{"value": true}' : ""} /> : field.type === "select" ? <select {...shared}><option value="">Select {field.label.toLowerCase()}</option>{(field.options ?? []).map((option) => <option key={option} value={option}>{headingCase(option)}</option>)}</select> : <input {...shared} type={field.type ?? "text"} step={field.type === "number" ? "0.01" : undefined} placeholder={field.type === "number" ? "0" : field.label} />}
  </label>;
}

function ReportsPage() {
  const [summary, setSummary] = useState({ invoices: 0, revenue: 0, payments: 0, overdue: 0 });
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!supabase) return;
    void Promise.all([supabase.from("invoices").select("amount,status,date"), supabase.from("payments").select("amount,status,date")]).then(([invoices, payments]) => {
      if (invoices.error || payments.error) { setLoading(false); return; }
      const invoiceRows = invoices.data ?? []; const paymentRows = payments.data ?? [];
      setSummary({ invoices: invoiceRows.length, revenue: paymentRows.filter((row) => row.status === "settled" || row.status === "paid").reduce((sum, row) => sum + Number(row.amount), 0), payments: paymentRows.length, overdue: invoiceRows.filter((row) => row.status === "overdue").length });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);
  const metrics = [{ label: "Invoice volume", value: summary.invoices.toLocaleString("en-IN"), icon: FileText }, { label: "Payments received", value: summary.payments.toLocaleString("en-IN"), icon: CreditCard }, { label: "Settled revenue", value: formatMoney(summary.revenue), icon: TrendingUp }, { label: "Overdue invoices", value: summary.overdue.toLocaleString("en-IN"), icon: Activity }];
  return <div className="page-content"><div className="page-intro"><div><p className="eyebrow">PLATFORM MANAGEMENT</p><h1>Reports</h1><p className="subtitle">A live view of billing and collection activity.</p></div></div><div className="stats-grid report-stats">{metrics.map((metric) => <article className="stat-card" key={metric.label}><div className="stat-top"><span>{metric.label}</span><span className="stat-icon sage"><metric.icon size={18} /></span></div><p className="stat-value">{loading ? <span className="loading-bar" /> : metric.value}</p><p className="stat-foot">Current workspace totals</p></article>)}</div><section className="panel report-callout"><div className="report-badge"><BarChart3 size={20} /></div><div><h2>Reports use your saved workspace records</h2><p>Totals update from invoices and settled payments in your Cloud database.</p></div><span className="report-live"><i /> Live</span></section></div>;
}