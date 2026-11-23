import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react(), {
    name: "backoffice-local-runtime-config",
    apply: "serve",
    transformIndexHtml(html) {
      const environment = loadEnv(mode, process.cwd(), "VITE_");
      const configuration = JSON.stringify({
        supabaseUrl: environment.VITE_SUPABASE_URL || "",
        supabasePublishableKey: environment.VITE_SUPABASE_PUBLISHABLE_KEY || "",
      });
      return html.replace("<body>", `<body><script>window.__BETALEN_CONFIG__=${configuration};</script>`);
    },
  }],
  server: { host: "0.0.0.0", proxy: {
    "/api": "http://localhost:8000",
    "/api/v1/auth": { target: "http://localhost:8001", changeOrigin: true },
  } },
}));