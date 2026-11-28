import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/warehouses")({
  head: () => ({
    meta: [
      { title: "Warehouses — Betalen Backoffice" },
      { name: "description", content: "Godowns and shop storage locations." },
      { property: "og:title", content: "Warehouses — Betalen Backoffice" },
      { property: "og:description", content: "Godowns and shop storage locations." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Warehouses" description="Godowns and shop storage locations." entity="Warehouse" table="warehouses" initial={{id:"", name:"", location:"", capacity:0, status:"active"}} />,
});
