import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { AdminShell } from "@/components/admin/AdminShell";
import { getCurrentAdmin } from "@/lib/backoffice.functions";

export const Route = createFileRoute("/_authenticated")({
  ssr: false,
  beforeLoad: async () => {
    try {
      await getCurrentAdmin();
    } catch {
      throw redirect({ to: "/auth" });
    }
  },
  component: () => <AdminShell><Outlet /></AdminShell>,
});
