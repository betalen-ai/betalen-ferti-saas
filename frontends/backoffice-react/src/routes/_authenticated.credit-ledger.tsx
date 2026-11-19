import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/credit-ledger")({
  head: () => ({
    meta: [
      { title: "Credit ledger — Betalen Backoffice" },
      { name: "description", content: "Udhaar balances and credit limits per farmer." },
      { property: "og:title", content: "Credit ledger — Betalen Backoffice" },
      { property: "og:description", content: "Udhaar balances and credit limits per farmer." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Credit ledger" description="Udhaar balances and credit limits per farmer." entity="Ledger entry" table="credit_ledger" initial={{id:"", farmer:"", tenant_name:"", credit_limit:0, balance:0, status:"within limit"}} />,
});
