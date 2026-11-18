import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/products")({
  head: () => ({
    meta: [
      { title: "Products — Betalen Backoffice" },
      { name: "description", content: "Fertilizer catalogue with pricing and GST." },
      { property: "og:title", content: "Products — Betalen Backoffice" },
      { property: "og:description", content: "Fertilizer catalogue with pricing and GST." },
    ],
  }),
  component: () => <CrudPage title="Products" description="Fertilizer catalogue with pricing and GST." entity="Product" table="products" initial={{id:"", name:"", category:"", price:0, gst:"5%", status:"active"}} />,
});
