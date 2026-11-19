# Betalen Ferti Backoffice

Standalone React app for the Betalen Ferti management backoffice.

## Run locally

1. Copy `.env.example` to `.env.local` and set the Lovable Cloud project URL and publishable key.
2. Start the local authentication service at `http://localhost:8001` and the API gateway at `http://localhost:8000`.
3. From this folder, run `npm install`, then `npm run dev`.
4. Use **Local API test** to check credentials against `POST /auth/login` (JSON: `subdomain`, `email`, `password`). **Workspace sign-in** still requires an administrator account provisioned in Lovable Cloud; public account creation is disabled.

## Build and deploy

Run `npm run build`; Docker builds the application and serves `dist` through Nginx. When running the container, provide `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` as environment variables; they are written to browser runtime configuration on startup, not committed into the code. The existing `/api/` reverse proxy is retained.

The app checks the `platform_admin` role before rendering and relies on database row-level security for all stored reads and changes. The local login endpoint currently verifies credentials only; its token does not grant access to CMS records, which still use the Cloud workspace session.