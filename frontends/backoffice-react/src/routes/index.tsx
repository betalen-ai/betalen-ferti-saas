import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Betalen Backoffice" },
    { name: "description", content: "Organization backoffice for the Betalen Ferti SaaS platform." },
    { property: "og:title", content: "Betalen Backoffice" },
    { property: "og:description", content: "Organization backoffice for the Betalen Ferti SaaS platform." },
  ] }),
  beforeLoad: () => { throw redirect({ to: "/auth" }); },
});
