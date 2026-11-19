import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/payments")({
  head: () => ({
    meta: [
      { title: "Payments — Betalen Backoffice" },
      { name: "description", content: "Cash, UPI and credit settlements." },
      { property: "og:title", content: "Payments — Betalen Backoffice" },
      { property: "og:description", content: "Cash, UPI and credit settlements." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Payments" description="Cash, UPI and credit settlements." entity="Payment" table="payments" initial={{id:"", invoice_number:"", method:"Cash", amount:0, status:"settled", date:""}} />,
});
