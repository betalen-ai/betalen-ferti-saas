import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/stock")({
  head: () => ({
    meta: [
      { title: "Stock & batches — Betalen Backoffice" },
      { name: "description", content: "Batch numbers, quantities and expiry dates." },
      { property: "og:title", content: "Stock & batches — Betalen Backoffice" },
      { property: "og:description", content: "Batch numbers, quantities and expiry dates." },
    ],
  }),
  component: () => <CrudPage title="Stock & batches" description="Batch numbers, quantities and expiry dates." entity="Batch" table="stock_batches" initial={{id:"", product_name:"", warehouse_name:"", batch:"", quantity:0, expiry:""}} />,
});
