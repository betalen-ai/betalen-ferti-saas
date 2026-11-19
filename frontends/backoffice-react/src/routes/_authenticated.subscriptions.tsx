import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/subscriptions")({
  head: () => ({
    meta: [
      { title: "Subscriptions — Betalen Backoffice" },
      { name: "description", content: "Free and paid plans per tenant." },
      { property: "og:title", content: "Subscriptions — Betalen Backoffice" },
      { property: "og:description", content: "Free and paid plans per tenant." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Subscriptions" description="Free and paid plans per tenant." entity="Subscription" table="subscriptions" initial={{id:"", tenant_name:"", plan:"free", status:"active", valid_from:"", valid_to:""}} />,
});
