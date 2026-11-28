# Ferti+ Backend API Specification (High Level)

Nov 20, 2026 · @Prasad

This document lists the APIs the Ferti+ backend must provide for the Angular shop owner application, at a high level: conventions, modules, endpoints, key request and response shapes, business rules and an implementation order. It complements "Ferti+ Shop Owner Application: Functional Specification" (screens and business rules) and "Ferti+ Corporate Website: Build Specification" (public site). Field-level detail is finalised in an OpenAPI file during development.

## 1. Principles

- **Style:** REST over HTTPS, JSON bodies, base path `/api/v1`
- **Contract first:** write an OpenAPI 3.1 file (`openapi.yaml`) in the repo; generate the Angular client and mock server from it
- **Multi-tenant:** every business row belongs to a tenant (shop). The tenant comes from the signed-in session, never from the request body or URL
- **Single user type:** shop owner. No admin, farmer or distributor APIs
- **Backend stack:** open choice (for example Node.js with NestJS, or .NET, or Spring Boot) with **PostgreSQL**; the design below does not depend on the framework
- **Money:** decimal strings with 2 places (`"1000.00"`), currency INR, calculated only on the server; the UI shows server results
- **Dates:** ISO 8601 (`2026-11-20`, timestamps in UTC)
- **Units:** stock is stored in the product's base unit (kg, litre or piece); packs carry a `sizeInBaseUnit` factor

## 2. Cross-Cutting Conventions

| Topic | Rule |
| --- | --- |
| Auth | httpOnly, secure, SameSite session cookie (or short-lived access token + refresh); all endpoints except `/auth/*` and `/health` need a session |
| Tenant isolation | Every query filtered by `tenantId`; enforced in a data-access layer and covered by tests |
| Pagination | `?page=1&pageSize=25` returns `{ items, page, pageSize, total }` |
| Search and filter | `?q=`, `?sort=name:asc`, and field filters such as `?brandId=`, `?active=true` |
| Errors | RFC 7807 style: `{ type, title, status, detail, errors:[{field, message}] }`; plain-language messages |
| Idempotency | `Idempotency-Key` header on `POST /bills`, `/payments`, `/stock/receipts` so a retry never double-posts |
| Concurrency | `version` field (or ETag) on editable records; stale update returns 409 |
| Soft delete | Master data is deactivated (`active=false`), never hard-deleted when referenced |
| Audit | Every create, update and cancel records who, when, and old and new values |
| Rate limits | Strict on `/auth/login`, `/auth/otp/*`, `/auth/forgot-password`; moderate elsewhere |
| Files | PDFs generated server side; returned as `application/pdf` |
| Health | `GET /health` and `GET /version` |

## 3. API Modules and Endpoints

### 3.1 Authentication

| Method and path | Purpose |
| --- | --- |
| POST `/auth/register` | Create owner account and shop (tenant) with email or phone |
| POST `/auth/login` | Email + password sign in |
| POST `/auth/otp/send` | Send a 6-digit OTP to a phone (sign in, sign up or reset) |
| POST `/auth/otp/verify` | Verify OTP; signs in or completes sign-up |
| GET `/auth/oauth/google` | Start Google sign in; callback `/auth/oauth/google/callback` |
| POST `/auth/verify-email` | Confirm email link token |
| POST `/auth/forgot-password` | Send reset link (same response whether or not the account exists) |
| POST `/auth/reset-password` | Set a new password with a single-use token |
| POST `/auth/refresh` | Refresh the session |
| POST `/auth/logout` | End the session |

Rules: password min 8 characters (hashed with Argon2id or bcrypt); OTP valid 5 minutes, 5 attempts, resend after 30 seconds; reset token valid 30 minutes and single use; the same verified email or phone links accounts rather than duplicating them.

### 3.2 Shop (tenant), profile and settings

| Method and path | Purpose |
| --- | --- |
| GET `/tenant/me` | Shop name, plan, logo, GSTIN (shown top-right in the app) |
| PATCH `/tenant/me` | Update shop name, address, GSTIN, phone, logo |
| GET `/me` and PATCH `/me` | Owner profile, language, password change |
| GET `/settings` and PUT `/settings` | Tax mode (inclusive or exclusive), default GST by category, bill number prefix, invoice footer, default interest and discount, rounding |

### 3.3 Brands and categories

| Method and path | Purpose |
| --- | --- |
| GET, POST `/brands` | List with product count; create |
| GET, PATCH `/brands/{id}` | Read; update; deactivate with `active=false` |
| GET, POST `/categories` | List and create categories (name, product type solid, liquid or item) |
| PATCH `/categories/{id}` | Update or deactivate |

A brand or category that has products cannot be deleted, only deactivated. On first login the backend seeds suggested categories.

### 3.4 Products and packs

| Method and path | Purpose |
| --- | --- |
| GET `/products` | Search, filter by brand, category, low stock, active; includes packs and stock |
| POST `/products` | Create a product with its packs in one request |
| GET, PATCH `/products/{id}` | Read and update product fields (name, grade, HSN, GST, low-stock level) |
| POST `/products/{id}/packs` | Add a pack (size, unit, MRP, cash price, credit price, barcode, loose sale flag) |
| PATCH `/packs/{id}` | Update prices and details; price changes are logged |
| GET `/packs/lookup?barcode=` | Fast lookup for POS scanning |

Validation: duplicate check on brand + name + pack size; unit must match the product type (solid: g or kg; liquid: ml or L; item: piece); `sizeInBaseUnit` is computed (500 ml = 0.5 L).

### 3.5 Stock

| Method and path | Purpose |
| --- | --- |
| POST `/stock/receipts` | Stock in: supplier, date, lines (packId, qty, cost price, batch, expiry) |
| POST `/stock/adjustments` | Damage, loss or correction with reason |
| GET `/stock` | Current stock per pack, in packs and base units |
| GET `/stock/ledger?packId=` | Movements: in, sale, adjustment, return, with running balance |
| GET `/stock/alerts` | Low-stock and near-expiry (30 days) lists |

Rules: sales and returns change stock automatically inside the same database transaction as the bill; negative stock is rejected unless the request has `allowNegative=true`; loose sales convert quantity to base units.

### 3.6 Farmers

| Method and path | Purpose |
| --- | --- |
| GET, POST `/farmers` | List (filters: has dues, overdue, village) and create |
| GET, PATCH `/farmers/{id}` | Read, update, deactivate |
| GET `/farmers/{id}/summary` | Total billed, paid, outstanding, overdue, last bill and payment dates |

Mobile number is unique within the shop. Opening balance creates an opening khata entry.

### 3.7 Seasons

| Method and path | Purpose |
| --- | --- |
| GET, POST `/seasons` | List and create (name, dates, default cash discount, default credit interest per month, due date, grace days, late interest) |
| GET, PATCH `/seasons/{id}` | Read and update |
| GET `/seasons/current` | Season whose dates include today |

### 3.8 Billing

| Method and path | Purpose |
| --- | --- |
| POST `/bills/preview` | Calculate totals without saving (discount, interest, GST, balance) |
| POST `/bills` | Save a bill: reduces stock, creates khata entries and payment records |
| GET `/bills` | List, filter by date, farmer, season, payment type, status |
| GET `/bills/{id}` | Bill with lines, terms and calculation breakdown |
| POST `/bills/{id}/cancel` | Void with reason; reverses stock and khata with reversing entries |
| GET \`/bills/{id}/pdf?format=a4 | thermal\` |
| POST `/bills/{id}/share` | Returns a WhatsApp share link and a public, expiring PDF URL |
| POST `/bills/drafts` and GET `/bills/drafts` | Hold and resume parked bills |

Payment types: `SPOT`, `CREDIT`, `PART`. The server recomputes totals on every preview and save; any client-sent total is ignored.

### 3.9 Payments and khata (ledger)

| Method and path | Purpose |
| --- | --- |
| POST `/payments` | Receive payment from a farmer (amount, mode cash, UPI or bank, date, optional bill to settle) |
| GET `/farmers/{id}/khata` | Ledger entries with debit, credit and running balance; filter by date, season, bill |
| GET \`/farmers/{id}/khata/export?format=pdf | xlsx\` |
| POST `/farmers/{id}/adjustments` | Discount, write-off or correction with reason |
| GET `/khata/dues` | All farmers with outstanding amount, overdue days, last payment |
| POST `/farmers/{id}/reminders` | Create a reminder message (SMS or WhatsApp link) |

Entries are append-only; corrections are reversing entries. Payments are allocated oldest bill first; interest already added to a bill is cleared before principal, unless the request names a bill.

### 3.10 Cashbook, dashboard and reports

| Method and path | Purpose |
| --- | --- |
| GET `/dashboard/summary` | Today's sales, cash in hand, credit outstanding, low-stock count, dues this week, recent bills |
| GET, POST `/cashbook` | Daily money in and out; add expenses and supplier payments |
| GET `/reports/sales?from=&to=` | Sales by day, product, brand, category |
| GET `/reports/stock-valuation` | Stock value at cost and at MRP |
| GET `/reports/dues` | Outstanding and overdue by farmer |
| GET `/reports/profit` | Revenue minus cost, with interest earned |
| GET `/reports/*?format=xlsx` | Excel export on every report |

## 4. Billing Calculation Contract

The server is the only source of truth for amounts. The same formulas are mirrored in the Angular app as unit-tested helper functions so the screen can show instant totals, but the saved value is always the server's.

- **Subtotal** = sum of quantity × unit price (MRP or the owner's selling price)
- **SPOT:** Total = Subtotal − Discount (discount is a rupee amount or a percentage)
- **CREDIT:** Interest = Credit amount × rate % per month ÷ 100 × months; Total due = Credit amount + Interest
- **PART:** Credit amount = Total − paid now; interest only on the credit amount
- **Months:** supplied by the owner, or computed as days from bill date to due date ÷ 30, one decimal
- **Late interest:** after due date plus grace days, a daily job (or a calculation at read time) adds interest at the late rate on the unpaid principal
- Rounded to the nearest ₹1 with a separate `roundOff` field

Example request to `POST /bills/preview` and `POST /bills`:

```json
{
  "farmerId": "f_123",
  "seasonId": "s_kharif26",
  "paymentType": "CREDIT",
  "items": [
    { "packId": "p_dap_50kg", "qty": 1, "unitPrice": "1000.00" }
  ],
  "discount": { "type": "NONE" },
  "interest": { "ratePerMonth": "1.00", "months": "6" },
  "dueDate": "2027-05-20",
  "paidNow": "0.00"
}
```

Example response (preview):

```json
{
  "subtotal": "1000.00",
  "discount": "0.00",
  "interestAmount": "60.00",
  "gst": { "mode": "INCLUSIVE", "taxable": "952.38", "cgst": "23.81", "sgst": "23.81" },
  "roundOff": "0.00",
  "total": "1060.00",
  "paidNow": "0.00",
  "balance": "1060.00",
  "terms": "Interest: 1% per month for 6 months = 60.00"
}
```

A SPOT bill of the same ₹1,000 with a ₹50 discount returns `total` ₹950. Both match the examples in the functional specification.

## 5. Data Entities (Summary)

Tenant, User, AuthIdentity (email, phone, google), Brand, Category, Product, Pack, StockLot, StockMovement, Farmer, Season, Bill, BillItem, KhataEntry, Payment, PaymentAllocation, CashbookEntry, Setting, AuditLog. Every table except `User` identity records carries `tenantId` and is indexed on it. Field lists are in the functional specification, section 11.

## 6. Non-Functional Requirements

- **Security:** HTTPS only; OWASP ASVS basics; input validation; parameterised queries; secrets in environment variables; CORS limited to the Ferti+ web origins; CSRF protection for cookie sessions
- **Privacy:** farmer mobile and address are personal data; never logged; export and delete on request
- **Performance:** list endpoints under 300 ms for 10,000 products; POS barcode lookup under 100 ms
- **Reliability:** nightly database backups, point-in-time recovery, daily job monitoring
- **Observability:** structured logs with request id and tenant id, metrics, error tracking
- **Testing:** unit tests for all calculation and allocation functions; API tests per module; a tenant-isolation test that fails if any query lacks a tenant filter
- **Docs:** OpenAPI served at `/api/docs` in non-production

## 7. Implementation Order

| Phase | Deliverable | Depends on |
| --- | --- | --- |
| 0 | Repo, OpenAPI skeleton, mock server for Angular (generated from OpenAPI), CI | None |
| 1 | Auth (email, phone OTP, Google, reset), tenant, settings | Phase 0 |
| 2 | Brands, categories, products and packs | Phase 1 |
| 3 | Stock in, adjustments, ledger, alerts | Phase 2 |
| 4 | Farmers and seasons | Phase 1 |
| 5 | Billing preview and save, stock deduction, PDF | Phases 3 and 4 |
| 6 | Payments, khata ledger, dues, exports, reminders | Phase 5 |
| 7 | Dashboard, cashbook, reports | Phase 6 |
| 8 | Hardening: security review, performance, backups, docs | All |

The Angular team works against the mock server from Phase 0, so UI and backend proceed in parallel.

## 8. Acceptance Criteria

1. An `openapi.yaml` covering every endpoint in section 3 exists in the repo and the Angular client builds from it.
2. A signed-in shop owner can never read or change another shop's data (verified by automated tests).
3. `POST /bills/preview` returns ₹950 for a ₹1,000 spot bill with ₹50 discount and ₹1,060 for the credit example in section 4.
4. Saving a bill reduces stock, creates khata entries and is safe to retry with the same `Idempotency-Key`.
5. Cancelling a bill restores stock and adds reversing khata entries; nothing is deleted.
6. Payments are allocated oldest bill first and the farmer's ledger balance always equals total debits minus total credits.
7. Login, OTP and forgot-password endpoints are rate limited; reset tokens and OTPs expire and are single use.
8. All list endpoints support pagination, search and sorting.

## 9. Ready-to-Paste Prompt for GitHub Copilot

Attach this document, the functional specification and the OpenAPI file once it exists.

```
You are a senior backend engineer. Build the Ferti+ REST API as described in the attached API specification and functional specification. Use PostgreSQL, a layered architecture (controllers, services, repositories), and base path /api/v1.

Start by creating openapi.yaml for every endpoint in section 3, then implement phase by phase from section 7, running tests after each phase.

Rules: every table has tenantId and every query is scoped by the tenant from the session, never from client input; money as decimal strings, calculated on the server; POST /bills, /payments and /stock/receipts accept an Idempotency-Key; khata entries are append-only with reversing entries for corrections; stock changes happen in the same transaction as the bill.

Billing: SPOT total = subtotal - discount (1000 with 50 discount -> 950). CREDIT interest = credit amount x ratePerMonth/100 x months (1000, 1% per month, 6 months -> 60, total 1060). PART charges interest only on the credit portion. Payments are allocated oldest bill first, interest before principal.

Auth: email+password, phone OTP (5 min, 5 attempts), Google OAuth, forgot/reset with single-use 30 minute tokens, rate limits on all auth routes.

Add unit tests for calculation and allocation functions, API tests per module, and a tenant isolation test. Serve OpenAPI at /api/docs in development and write a README with setup and environment variables.
```
