# Ferti+ API

The organization service owns tenant identity and the transactional Ferti+ domain API. Keeping billing, stock, and khata writes in the same PostgreSQL transaction allows a bill to update all three atomically.

## Run and migrate

From the repository root:

```powershell
docker compose up --build beta_organization api-gateway
docker compose exec beta_organization alembic upgrade head
```

The service is available on port `8001`; the gateway exposes it under `/api/v1` on port `8000`. In non-production environments, interactive documentation is at `/api/docs`, the JSON schema at `/api/openapi.json`, and the checked-in OpenAPI contract is [openapi.yaml](./openapi.yaml).

## Authentication and tenant isolation

Use the bearer access token returned by registration/login or the `HttpOnly` `access_token` cookie. Cookie-authenticated writes require the `X-CSRF-Token` header matching the readable `csrf_token` cookie. Public expiring bill-share links are the only unauthenticated business-resource route. Tenant IDs are read from the signed token, never from request bodies; queries include the tenant predicate. Set `JWT_SECRET` to a unique secret and `ENVIRONMENT=production` in production.

## Implemented domain

The Alembic revision adds tenant-scoped brands, categories, products, packs, stock lots and movements, farmers, seasons, bills and lines, khata entries, payments and allocations, cashbook entries, settings, audit logs, drafts, and idempotency records. The API includes master-data CRUD, stock receipts/adjustments/ledger/alerts, farmer and season endpoints, billing preview/save/cancel/drafts/PDF/share, payments and khata, dashboard, cashbook, and sales/dues/profit/stock-valuation reports with XLSX exports.

All money values are serialized as decimal strings. Writes use the tenant ID from the token; edits require a matching `version`; bill saves and stock receipts/payments accept `Idempotency-Key`. Master data is deactivated through `active=false`; ledger corrections append reversal entries.

## Configuration and integrations

The service uses the shared `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `ENVIRONMENT`, and `PUBLIC_API_URL` settings. Set `ORG_SERVICE_URL` for the gateway if the organization service is not reachable at its Compose service name. Use the externally reachable gateway URL for `PUBLIC_API_URL`.

Phone OTP, email verification, password reset, refresh-token rotation, logout, and Google OAuth routes are implemented. Configure `OTP_PROVIDER_URL` and optionally `OTP_PROVIDER_API_KEY` for a JSON POST adapter receiving `{ "to", "message" }`; configure `EMAIL_PROVIDER_URL` and optionally `EMAIL_PROVIDER_API_KEY` for a JSON POST adapter receiving `{ "to", "subject", "text" }`. Missing providers return an explicit `503`. Configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` to enable Google OAuth; `FRONTEND_URL` is used for email links. Authentication rate limits and OTP/token expiry are enforced in PostgreSQL.
