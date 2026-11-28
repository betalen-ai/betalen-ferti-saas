import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/tenants")({
  head: () => ({
    meta: [
      { title: "Tenants — Betalen Backoffice" },
      { name: "description", content: "Fertilizer shops registered on the platform." },
      { property: "og:title", content: "Tenants — Betalen Backoffice" },
      { property: "og:description", content: "Fertilizer shops registered on the platform." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Tenants" description="Fertilizer shops registered on the platform." entity="Tenant" table="tenants" initial={{id:"", name:"", subdomain:"", subscription_plan:"free", status:"active", created_at:""}} />,
});
