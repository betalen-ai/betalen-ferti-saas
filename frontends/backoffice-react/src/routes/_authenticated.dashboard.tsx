import { createFileRoute } from "@tanstack/react-router";
import { DashboardPage } from "@/components/admin/DashboardPage";
export const Route = createFileRoute("/_authenticated/dashboard")({
  head: () => ({ meta: [
    { title: "Dashboard — Betalen Backoffice" },
    { name: "description", content: "Organization backoffice for the Betalen Ferti SaaS platform." },
    { property: "og:title", content: "Dashboard — Betalen Backoffice" },
    { property: "og:description", content: "Organization backoffice for the Betalen Ferti SaaS platform." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
  ] }),
  component: DashboardPage,
});
