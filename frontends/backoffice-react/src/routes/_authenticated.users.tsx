import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/users")({
  head: () => ({
    meta: [
      { title: "Users — Betalen Backoffice" },
      { name: "description", content: "Staff accounts across all tenants." },
      { property: "og:title", content: "Users — Betalen Backoffice" },
      { property: "og:description", content: "Staff accounts across all tenants." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Users" description="Staff accounts across all tenants." entity="User" table="org_users" initial={{id:"", tenant_id:"", email:"", full_name:"", status:"active"}} />,
});
