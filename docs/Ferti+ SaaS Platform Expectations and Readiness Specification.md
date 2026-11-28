# Ferti+ SaaS Platform Expectations and Readiness Specification

Nov 21, 2026 · @Prasad

Beyond screens and APIs, a SaaS product used daily by shop owners must meet a set of platform, security, legal and operational expectations. This document lists them for Ferti+ so the team plans for them early. It complements the Corporate Website, Shop Owner Application and Backend API specifications. Legal items are planning guidance, not legal advice; confirm them with a lawyer or compliance advisor before launch.

## 1. How to Use This Document

- Each section states the **expectation**, the **minimum for launch (MVP)** and what can wait for **later**
- Priority labels: **Must** (before public launch), **Should** (within 3 months of launch), **Later** (growth stage)
- Share it with the developers, the designer and whoever handles legal and support

## 2. Product and Business Model

| Expectation | Detail | Priority |
| --- | --- | --- |
| Free plan for shop owners | All features in the functional spec are free at launch | Must |
| Plans and entitlements built in from day one | A `plan` on every tenant and a feature-flag layer (`canUse('multiUser')`) so paid plans can be added without rewrites | Must |
| Usage limits (soft) | Track bills, products, farmers, storage per tenant; warn, never silently block at launch | Should |
| Future paid plans | Multi-user staff, WhatsApp and SMS credits, multi-branch, advanced reports | Later |
| Subscription billing | Payment gateway (UPI autopay, cards), GST invoices for Ferti+ subscriptions, trial and grace periods | Later |
| Revenue ideas to keep options open | Paid SMS/WhatsApp credits, supplier or brand promotions (clearly marked), payment and credit-scoring partners | Later |

## 3. Multi-Tenancy and Tenant Lifecycle

- **Isolation:** shared database with `tenantId` on every row, enforced in a data layer, plus automated tests that prove one shop can never see another's data. Consider PostgreSQL row-level security as a second guard
- **Tenant states:** `ACTIVE`, `SUSPENDED` (non-payment or abuse, read-only), `CLOSED` (owner left; data kept for the retention period), `DELETED` (permanently erased)
- **Owner self-service:** export all data, close account, request deletion (Must)
- **Noisy neighbour control:** rate limits per tenant and slow-query monitoring (Should)
- **Tenant-aware everything:** logs, metrics, backups and support tools can all be filtered by tenant (Must)
- **Large-tenant path:** ability to move one tenant to its own database or schema later (Later)

## 4. Onboarding and Activation

A shop owner who cannot get the first bill out in a day will leave. Plan the first-run experience carefully.

- **Setup wizard (Must):** shop name, GSTIN, address, logo, bill number prefix, language, default tax mode
- **Starter catalogue (Must):** suggested categories and common product names (Urea, DAP, NPK, pesticides, seeds) the owner can accept in one click
- **Bulk import (Must):** Excel or CSV templates for products, packs, opening stock and farmers, with row-by-row error reports
- **Opening balances (Must):** guided entry of existing farmer dues from the paper khata
- **Sample data mode (Should):** try the app with demo data, then clear it
- **Guided tour and checklists (Should):** "Add 5 products", "Add a farmer", "Make your first bill"
- **Activation metric:** first bill created within 3 days of signing up

## 5. Reliability and Operations

| Topic | Target |
| --- | --- |
| Availability | 99.5% monthly at launch, 99.9% later; maintenance in off-peak hours (late night) with notice |
| Backups | Automated daily full backup plus continuous log backup; retained 30 days; stored in a different location |
| Recovery | RPO 15 minutes, RTO 4 hours; a restore drill every quarter |
| Monitoring | Uptime checks, error tracking, slow query alerts, disk and memory alerts, on-call phone alert to the team |
| Status page | Public status page and an in-app banner during incidents (Should) |
| Incident process | Severity levels, owner, update every 30 minutes for major incidents, written post-mortem within 5 days |
| Hosting | India region data centres (customer data stays in India); managed PostgreSQL; separate dev, staging and production |

## 6. Security Expectations

| Area | Expectation | Priority |
| --- | --- | --- |
| Transport and storage | HTTPS everywhere with HSTS; encryption at rest for database, backups and files | Must |
| Passwords | Argon2id or bcrypt; breached-password check; lockout and CAPTCHA after repeated failures | Must |
| Sessions | httpOnly secure cookies, short sessions with refresh, "sign out all devices", list of active sessions | Must |
| Two-step verification | Optional OTP or authenticator for owners (strongly suggested for shops with large dues) | Should |
| Web protections | CSRF, XSS, SQL injection, CORS, Content Security Policy, security headers | Must |
| Secrets | Environment or vault storage, key rotation, never in the repo | Must |
| Dependencies | Automated vulnerability scans in CI, weekly updates | Must |
| Access control | Least privilege for staff and servers; production access logged and reviewed | Must |
| Audit trail | Who changed prices, stock, bills and khata and when; visible to the owner | Must |
| Testing | Independent penetration test before public launch and yearly after | Should |
| Abuse | Rate limits on OTP and SMS to avoid cost abuse and spam | Must |

## 7. Privacy, Legal and Regulatory (India)

### 7.1 Data protection

India's Digital Personal Data Protection (DPDP) Act, 2023 applies. The DPDP Rules, 2025 were notified on 13 November 2025. Only the enabling provisions took effect then; most obligations, including notice, consent, security, breach reporting and retention (Rules 3 and 5 to 16, 22 and 23), apply from **13 May 2027**, and the rule on consent managers from 13 November 2026. Ferti+ should be built to meet them at launch.

- **Roles:** Ferti+ is likely the data fiduciary for shop owners' own data and a processor for the farmers' data the owners enter. Confirm this with a lawyer and reflect it in the Terms and a data processing agreement (Must)
- **Notice and consent:** clear, plain-language notice at sign-up in English and local languages; recorded consent with timestamp and version (Must)
- **Data minimisation:** collect only what billing and khata need; Aadhaar numbers are not collected (Must)
- **Rights:** access, correction and erasure requests handled from inside the app and by a named grievance contact (Must)
- **Breach response:** written plan to detect, contain and report personal data breaches, with owner notification (Must)
- **Retention:** keep records as long as the owner's legal and tax needs require, then erase; notify before erasure (Must)
- **Children's data:** do not collect (Must)
- **Vendors:** SMS, WhatsApp, hosting and email providers are processors; sign contracts covering security and compliance (Should)

### 7.2 Tax, invoicing and trade rules

- GST-ready tax invoices (GSTIN, HSN, tax split, invoice number series) and records kept for the period the law requires (Must)
- Check whether the shop's turnover makes **e-invoicing** or e-way bill rules apply and plan an integration if so (Should)
- Fertilizer, pesticide and seed sales are regulated (licences, approved products, stock registers, maximum retail prices, restricted or banned items). Have a compliance advisor confirm which records and fields the app must capture, such as licence numbers on invoices and stock registers, and support printing those reports (Must)
- Credit with interest: confirm that charging interest to farmers on credit sales is lawful and how it must be disclosed on the bill in the owner's state; keep the interest terms visible on every invoice (Must)

### 7.3 Legal documents

Terms of Service, Privacy Policy, Cookie notice, Data Processing Agreement, Acceptable Use, Refund and Cancellation (for paid plans), Grievance Officer details, all linked in the website footer and the sign-up screen (Must).

## 8. Offline and Low-Connectivity Support

Rural shops often have weak or intermittent internet; this is a deciding factor for adoption.

- **Progressive Web App (Must):** installable, fast, works as an icon on Android home screens
- **Offline billing (Should):** create bills and receive payments without a connection; queue them locally (IndexedDB) and sync later
- **Sync rules:** each queued action carries a client-generated id and the idempotency key; the server rejects duplicates; stock conflicts are shown to the owner for resolution
- **Light pages:** works on low-end Android phones, small bundles, lazy loading, compressed images
- **Clear status:** always show Online, Offline or Syncing in the status bar

## 9. Language and Localisation

- Languages: English at launch; Telugu and Hindi next, then other regional languages (Must for English, Should for others)
- All text in translation files (ngx-translate); no hard-coded strings
- Indian number format (1,00,000), rupee symbol, amount in words on invoices, date format DD MMM YYYY
- Fonts that support Telugu and Devanagari; test layouts with long translated text
- Invoice and khata statement printable in the owner's chosen language

## 10. Devices and Hardware

| Item | Expectation |
| --- | --- |
| Screens | Tablet landscape, desktop, and 360 px Android phones |
| Barcode scanners | USB and Bluetooth keyboard-style scanners; phone camera scanning (Should) |
| Printers | 58 mm and 80 mm thermal receipts and A4 invoices; browser print with correct CSS; Bluetooth printing later |
| Cash drawer | Opened on print through the printer (Later) |
| Browsers | Latest Chrome, Edge, Firefox, Safari; Android Chrome |
| Native app | A mobile app (Capacitor wrapper or Flutter) only after the PWA proves demand (Later) |

## 11. Notifications and Integrations

| Integration | Use | Notes | Priority |
| --- | --- | --- | --- |
| SMS | OTP, payment reminders, receipts | India requires sender and template registration on telecom DLT platforms; plan lead time | Must |
| WhatsApp | Share bills, statements and reminders | Start with share links; Business API later | Should |
| Email | Verification, reset, statements | Transactional provider with SPF, DKIM, DMARC | Must |
| UPI | Dynamic QR on bills, payment links, payment status | Via a payment gateway; reconcile to khata | Should |
| Accounting export | Tally and Excel formats | Sales, purchase, ledger | Later |
| GST portal | Return-ready data, e-invoice | Through a GSP | Later |
| Push and in-app | Low stock, dues, expiry alerts | Web push on PWA | Should |

## 12. Staff Roles and Permissions (Roadmap)

Launch has only the owner. Design the database now so staff can be added without rewrites.

- Tables already carry `createdBy`; permissions are checked through a central `can(user, action)` function
- Later roles: **Owner**, **Manager**, **Cashier**, **Stock keeper**, **Accountant (read-only)**
- Later controls: per-role hide cost price, block discounts above a limit, block bill cancel, device approval, activity log per user

## 13. Internal Ferti+ Operations Console

The team running Ferti+ needs a private back-office tool. It is **not** a customer login and is built separately, behind company SSO or VPN.

- Tenant list and search, plan, status, sign-up source, last activity
- Support view of a tenant only with the owner's consent and a time limit; every action audited
- Feature flags and plan changes per tenant, announcements and maintenance banners
- Metrics: sign-ups, activation, active shops, bills per day, errors, SMS usage and cost
- Abuse and fraud tools: block numbers, review suspicious sign-ups
- Data requests: handle export, deletion and correction with an audit log

## 14. Support and Customer Success

- In-app help centre and short videos in local languages (Must)
- Support channels: WhatsApp number, phone and email with published hours; first response target under 4 working hours (Must)
- In-app feedback button and bug report with screenshot and tenant id (Should)
- Ticketing tool and a canned-answers library (Should)
- Pilot shops with a direct line to the team, a field visit program and training sessions at fertilizer dealer meets (Should)
- Public changelog and release notes for each update (Should)

## 15. Analytics and Product Metrics

| Metric | Why it matters |
| --- | --- |
| Sign-up to first bill within 3 days | Activation |
| Weekly active shops and bills per shop per week | Real usage |
| Share of bills on credit and average credit days | Understand the khata use case |
| Feature adoption (stock in, reports, reminders) | Prioritise the roadmap |
| 30-day and 90-day retention | Product-market fit |
| Support tickets per 100 shops, top reasons | Find UX problems |
| Error rate and page load by region | Quality |

Use privacy-respecting analytics, no farmer personal data in analytics events, and honour the consent choices.

## 16. Engineering Practices

- **Environments:** local, development, staging, production; production data never copied to lower environments without masking
- **CI/CD:** every pull request runs lint, unit tests, API tests, security scan and build; staging deploys automatically; production deploys with approval and quick rollback
- **Infrastructure as code** for servers, database and networking
- **Database migrations** versioned and reversible; no manual changes in production
- **Feature flags** for risky or paid features and gradual rollout to pilot shops
- **Testing pyramid:** many unit tests (all money formulas), API tests per module, a small set of end-to-end tests for sign-in, bill, payment and khata; tenant-isolation tests
- **Performance budgets:** Angular initial bundle under 250 KB gzipped, first load under 3 seconds on 4G, Lighthouse 90+
- **Accessibility:** WCAG 2.1 AA checks in CI
- **API versioning:** `/api/v1`, deprecation notice for at least 6 months before removing a version
- **Observability:** structured logs with request id and tenant id, metrics, tracing, dashboards, error tracking
- **Documentation:** README, architecture decision records, OpenAPI, runbooks for deploy, restore and incident response
- **Code quality:** code review required, ESLint and Prettier, conventional commits, semantic versioning
- **Cost control:** budget alerts for hosting, SMS and WhatsApp; cost per active shop tracked monthly

## 17. Data Import, Export and Portability

- Export all data (products, stock, farmers, bills, khata) as Excel or CSV and as PDF statements, any time, free (Must)
- Import templates with validation and a dry-run preview (Must)
- Migration help for shops moving from paper ledgers, Excel or other billing software (Should)
- API keys and public API for partners (Later)

## 18. Go-to-Market Readiness

- Website with SEO pages in English and Telugu, WhatsApp click-to-chat, demo video and a sign-up conversion goal (Must)
- Pilot with 10 to 20 shops in one district, weekly feedback calls, then widen (Must)
- Referral program: shop owners invite other shops (Should)
- Partnerships: fertilizer dealer associations, input companies, agri extension groups (Later)
- Seasonal timing: aim to onboard before the next sowing season, because shops are busiest then and least willing to learn new tools
- Trust signals: privacy promise, "your data is yours" export, local support number

## 19. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Poor internet at shops | Billing stops, owners revert to paper | PWA with offline billing queue, light pages |
| Wrong interest or discount calculation | Disputes with farmers, loss of trust | Server-side formulas, unit tests, clear terms on every bill |
| Data leak between shops | Severe reputational and legal harm | Tenant filter tests, row-level security, pen test |
| Owners not comfortable with software | Low activation | Setup wizard, import, local-language help, field training |
| SMS cost or abuse | Unplanned spend | Rate limits, CAPTCHA, budgets, DLT-registered templates only |
| Regulatory change (fertilizer, tax, data protection) | Rework | Compliance advisor review each quarter, configurable fields |
| Single founder or developer dependency | Delivery and recovery risk | Documentation, runbooks, shared access via vault |
| Data loss | Loss of daily ledgers | Tested backups and restore drills |

## 20. Delivery Roadmap

| Stage | Focus | Exit criteria |
| --- | --- | --- |
| MVP (pilot) | Auth, products, stock, farmers, billing, khata, English UI, PWA, backups, legal pages | 10 pilot shops billing daily without major issues |
| Beta | Offline billing, Telugu and Hindi, bulk import, reminders, reports, support channels, pen test | 100 active shops, 30-day retention above 60% |
| General availability | Public launch, referral, status page, 2-step verification, Operations Console | Meets all **Must** items in this document |
| Growth | Staff roles, paid plans, UPI and GST integrations, native app, multi-branch | Positive unit economics per shop |

## 21. Pre-Launch Checklist

1. Tenant isolation tests pass and an independent security review is done
2. Backups restored successfully in a drill
3. Terms, Privacy Policy, consent records and grievance contact are live
4. SMS sender and templates are approved on the telecom platform
5. Bulk import tested with real paper-ledger data from pilot shops
6. Interest and discount formulas verified by the owner of a pilot shop with real examples
7. Printing tested on A4 and 80 mm thermal printers
8. Load test with expected peak (festival season mornings)
9. Support number, help videos and training plan ready
10. Monitoring, alerts and an incident contact list are active

## 22. Open Questions for the Business

- Which states and languages come first?
- Who is the legal entity running Ferti+, and who is the grievance officer?
- Will interest on credit be shown as "interest" or "service charge" on invoices in the target states?
- Which hosting provider and region will be used, and what is the monthly budget?
- When is the target pilot start, and which shops will join?
