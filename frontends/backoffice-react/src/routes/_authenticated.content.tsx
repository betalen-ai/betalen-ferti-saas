import { createFileRoute } from "@tanstack/react-router";
import { CrudPage } from "@/components/admin/CrudPage";


export const Route = createFileRoute("/_authenticated/content")({
  head: () => ({
    meta: [
      { title: "Content — Betalen Backoffice" },
      { name: "description", content: "Pages, announcements and help articles." },
      { property: "og:title", content: "Content — Betalen Backoffice" },
      { property: "og:description", content: "Pages, announcements and help articles." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <CrudPage title="Content" description="Pages, announcements and help articles." entity="Content item" table="content_items" initial={{id:"", title:"", slug:"", type:"Page", body:"", status:"draft", updated:""}} />,
});
