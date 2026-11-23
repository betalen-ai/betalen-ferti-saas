# Betalen Ferti Backoffice

Standalone React app for the Betalen Ferti management backoffice.

## Run locally

1. Copy `.env.example` to `.env.local` and set the Lovable Cloud project URL and publishable key.
2. Start the local authentication service at `http://localhost:8001` and the API gateway at `http://localhost:8000`.
3. From this folder, run `npm install`, then `npm run dev`.
4. Sign in with a shop subdomain, email, and password. The app posts these credentials to `POST /auth/login` through the Vite proxy.

## Build and deploy

Run `npm run build`; Docker builds the application and serves `dist` through Nginx. When running the container, provide `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` as environment variables; they are written to browser runtime configuration on startup, not committed into the code. The existing `/api/` reverse proxy is retained.

The owner login API verifies credentials but does not grant access to platform CMS records. Existing Cloud sessions and the `platform_admin` role check remain the authority for CMS reads and changes.