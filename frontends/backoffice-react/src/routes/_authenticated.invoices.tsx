import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/invoices")({
  head: () => ({
    meta: [
      { title: "Invoices — Betalen Backoffice" },
      { name: "description", content: "GST and non-GST bills issued to farmers." },
      { property: "og:title", content: "Invoices — Betalen Backoffice" },
      { property: "og:description", content: "GST and non-GST bills issued to farmers." },
    ],
  }),
  component: () => <CrudPage title="Invoices" description="GST and non-GST bills issued to farmers." entity="Invoice" table="invoices" initial={{id:"", invoice_number:"", customer:"", tenant_name:"", amount:0, type:"GST", status:"paid", date:""}} />,
});
