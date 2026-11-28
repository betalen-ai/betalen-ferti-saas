import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/roles")({
  head: () => ({
    meta: [
      { title: "Roles & permissions — Betalen Backoffice" },
      { name: "description", content: "Resource and action based access for each role." },
      { property: "og:title", content: "Roles & permissions — Betalen Backoffice" },
      { property: "og:description", content: "Resource and action based access for each role." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Roles & permissions" description="Resource and action based access for each role." entity="Role" table="backoffice_roles" initial={{id:"", name:"", description:"", permissions:0}} />,
});
