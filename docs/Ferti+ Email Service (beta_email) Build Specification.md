# Ferti+ Email Service (beta\_email): Build Specification

Nov 26, 2026 · @Prasad

`beta_email` is a new backend service in the `services/` folder, built like the other FastAPI services (`beta_organization`, `beta_billing`, `beta_inventory`, `beta_reports`). It sends the system's transactional emails through a **Gmail sender account**: password reset link, password changed confirmation, failed login alert, and successful onboarding (with the tenant id). Other services call it over HTTP; users never call it directly. This document is written so GitHub Copilot can build the whole project from it.

## 1. Goals and Scope

**Goals**

1. One place that renders and sends all system emails, so other services never touch mail credentials
2. Reliable delivery: queue, retries, status tracking, no lost emails when Gmail is slow or down
3. Secure handling of sensitive links (reset links are never logged or stored in plain text)
4. Branded, responsive, bilingual-ready emails (English first; Telugu and Hindi later)
5. Easy to replace Gmail with another provider later without changing callers

**In scope (Phase 1):** the four email types in section 4, Gmail SMTP sending, templates, queue and retries, status API, tests, Docker setup.

**Out of scope:** marketing or bulk email, newsletters, SMS and WhatsApp (separate service later), inbox reading, bounce processing from the mailbox.

## 2. Architecture

```
+-------------------+      HTTP (internal, service key)      +---------------------------+
| beta_organization | --------------------------------------> |  beta_email  :8005        |
| (auth, onboarding)|   POST /v1/emails  -> 202 Accepted      |                           |
+-------------------+                                         |  API  ->  DB queue        |
| beta_billing etc. |  (later: reminders, receipts)           |  Worker -> Provider       |
+-------------------+                                         +-------------+-------------+
                                                                            |
                                          +---------------------------------+----------+
                                          |                                            |
                                  +-------v--------+                           +-------v-------+
                                  | GmailSmtp      |  smtp.gmail.com:587       | Console / Mailpit |
                                  | Provider (prod)|  STARTTLS + App Password  | (development)     |
                                  +----------------+                           +-------------------+
                                          |
                                  PostgreSQL schema  email  (messages, attempts, suppressions)
```

- **Internal only:** port 8005 is reachable inside the Docker network; the API gateway does **not** route it to the internet
- **Asynchronous:** the API stores the request and returns **202 Accepted** immediately; a background worker inside the same service sends it
- **Queue:** PostgreSQL table with `SELECT ... FOR UPDATE SKIP LOCKED` (no extra broker needed); Redis is optional for rate limits
- **Provider interface:** `EmailProvider.send(message) -> ProviderResult`; implementations `GmailSmtpProvider`, `ConsoleProvider` (prints, for development), later `SesProvider` or `GmailApiProvider`. Selected by `EMAIL_PROVIDER`

## 3. Tech Stack and Folder Structure

- Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 (async) with asyncpg, Alembic
- `aiosmtplib` for SMTP, Jinja2 for templates, `css-inline` to inline CSS, `cryptography` (Fernet or AES-GCM) for payload encryption, `structlog` for logs, pytest and pytest-asyncio, `respx` or mocks for tests

```
services/beta_email/
  app/
    main.py                 # FastAPI app, /health, /ready, router includes, worker startup
    config.py               # pydantic-settings (env variables in section 9)
    db.py                   # async engine and session
    security.py             # service-key auth, payload encryption helpers
    routes/
      emails.py             # POST /v1/emails, GET /v1/emails/{id}, GET /v1/emails, retry
      templates.py          # list and preview templates (disabled in production)
      health.py
    schemas/
      emails.py             # request/response models
      template_data.py      # one Pydantic model per template (validated data)
    services/
      email_service.py      # validate, dedupe, encrypt, store, enqueue
      renderer.py           # Jinja2 + CSS inlining, HTML and text, locale fallback
      worker.py             # polling loop, retries, backoff, rate limiting
      suppression.py        # do-not-send list
    providers/
      base.py               # EmailProvider interface
      gmail_smtp.py
      console.py
    models/                 # SQLAlchemy models: EmailMessage, EmailAttempt, EmailSuppression
    templates/
      layout/base.html.j2   # brand header, footer, button styles
      en/
        password_reset_requested.html.j2   password_reset_requested.txt.j2   password_reset_requested.subject.j2
        password_changed.*   login_failed_alert.*   onboarding_approved.*
      te/  hi/              # added later, falls back to en
    static/ (logo.png is embedded as a CID image or hosted on the website)
  alembic/ (migrations)
  tests/
  Dockerfile  requirements.txt  README.md  .env.example
```

Add to `docker-compose.yml`: service `beta_email` on port 8005 (internal), and in development a `mailpit` container (SMTP 1025, web inbox on http://localhost:8025) so emails can be viewed without sending real mail.

## 4. Email Types (Phase 1)

Brand: forest green #0B6B3A button, cream background #F7F7F2, Ferti+ logo at the top, white card, 600 px wide, large tap-friendly button (minimum 48 px high), plain-text version for every email, no tracking pixels.

### 4.1 Password reset link (`PASSWORD_RESET_REQUESTED`)

- **Triggered by:** owner submits Forgot password
- **Subject:** Reset your Ferti+ password
- **Data:** ownerName, resetLink, expiresInMinutes (30), requestedAt, requestIp, deviceDescription
- **Content:** greeting; "We received a request to reset the password for your Ferti+ account"; big **Reset password** button; the same link as text; "This link works once and expires in 30 minutes"; "If you did not ask for this, ignore this email; your password will not change"; request time, approximate device and IP
- **Rules:** the link is created by `beta_organization` (single-use token); this service only delivers it. If `expiresAt` has passed before sending, the message is marked EXPIRED and not sent

### 4.2 Password changed confirmation (`PASSWORD_CHANGED`)

- **Triggered by:** successful password reset or change-password
- **Subject:** Your Ferti+ password was changed
- **Data:** ownerName, changedAt, changeType (RESET or CHANGE), ip, deviceDescription, location (approximate), secureAccountLink, supportEmail
- **Content:** confirmation with time and device; "If this was you, no action is needed"; "If it was not you, reset your password now" with a button and the support email; note that all other sessions were signed out

### 4.3 Failed login alert (`LOGIN_FAILED_ALERT`)

- **Triggered by:** 3 consecutive failed sign-ins on an existing account (email or OTP), and again when the account gets locked
- **Subject:** Unsuccessful sign-in attempts on your Ferti+ account
- **Data:** ownerName, attemptCount, lastAttemptAt, ip, deviceDescription, method (PASSWORD, OTP, GOOGLE), locked (true or false), lockedUntil, resetPasswordLink (the generic forgot-password page, not a token)
- **Content:** how many attempts, when, from where; whether the account is temporarily locked and until when; buttons **Reset password** and **This was me**; advice to use a strong password
- **Rules:** at most one alert per account per hour so attackers cannot flood the owner's inbox; never include the password that was tried
- *Optional later:* `LOGIN_NEW_DEVICE` (successful sign-in from a new device)

### 4.4 Successful onboarding (`ONBOARDING_APPROVED`)

- **Triggered by:** Super Admin approves the shop request
- **Subject:** Welcome to Ferti+: your shop is approved
- **Data:** ownerName, shopName, tenantId, referenceNo, approvedAt, signInUrl, loginEmail, supportEmail, helpCenterUrl
- **Content:** congratulations; summary box with **Shop name, Tenant ID, Registration reference, Approved on, Sign-in email**; big **Sign in to Ferti+** button; "Sign in with your email and the password you chose, with your mobile OTP, or with Google"; three quick-start steps (add products, add farmers, make your first bill); support contact
- **Rules:** **never include a password.** The Tenant ID is an identifier for support and reference, not a secret; it does not give access

### 4.5 Later templates (same pattern)

`ONBOARDING_RECEIVED`, `ONBOARDING_NEEDS_INFO`, `ONBOARDING_REJECTED`, `TENANT_SUSPENDED`, `EMAIL_VERIFICATION`, `FARMER_STATEMENT` (khata PDF attachment), `LOW_STOCK_DIGEST`.

## 5. API (internal)

Base path `/v1`. Every request needs the header `X-Service-Key` (one key per calling service, listed in `SERVICE_API_KEYS`), plus `X-Request-Id` for tracing. Calls without a valid key get 401.

| Method and path | Purpose |
| --- | --- |
| POST `/v1/emails` | Queue an email using a template; returns 202 with the message id |
| GET `/v1/emails/{id}` | Status, attempts, timestamps (no body content, no links) |
| GET `/v1/emails` | List with filters `tenantId`, `template`, `status`, `to`, `from`, `to_date`; paginated |
| POST `/v1/emails/{id}/retry` | Retry a FAILED or DEAD message (admin key only) |
| GET `/v1/templates` | List template names, required fields and locales |
| POST `/v1/templates/{name}/preview` | Render HTML and text with sample data (disabled when `ENV=production`) |
| GET `/health` | Liveness: `{"status":"ok","service":"beta_email"}` |
| GET `/ready` | Readiness: database reachable and provider configuration valid |

### 5.1 Send request

```json
POST /v1/emails
X-Service-Key: <key>
Idempotency-Key: pwd-reset:7f1c...

{
  "template": "ONBOARDING_APPROVED",
  "to": { "email": "ramesh@example.com", "name": "Ramesh Kumar" },
  "locale": "en",
  "tenantId": "c4f1e6a2-9d1b-4a52-8c3e-1f6a7b9d0e11",
  "userId": "u_123",
  "priority": "NORMAL",
  "expiresAt": null,
  "data": {
    "ownerName": "Ramesh Kumar",
    "shopName": "Sri Lakshmi Agro Centre",
    "tenantId": "c4f1e6a2-9d1b-4a52-8c3e-1f6a7b9d0e11",
    "referenceNo": "FRT-2026-000123",
    "approvedAt": "2026-11-26T10:15:00Z",
    "signInUrl": "https://app.ferti.example/signin",
    "loginEmail": "ramesh@example.com",
    "supportEmail": "support@ferti.example"
  }
}
```

Response **202**: `{ "messageId": "...", "status": "QUEUED" }`. A repeated request with the same `Idempotency-Key` returns the original message id and does not send a second email.

**Validation:** `data` is validated against the Pydantic model of that template; missing or extra fields return 422. Links must start with the configured `APP_BASE_URL` (blocks use of the service to send arbitrary links). Recipient must be a valid email and not on the suppression list (then status `SUPPRESSED`).

**Error codes:** 401 `UNAUTHORIZED`, 409 `IDEMPOTENCY_CONFLICT` (same key, different body), 422 `INVALID_TEMPLATE_DATA`, 429 `RATE_LIMITED`, 503 `QUEUE_UNAVAILABLE`.

## 6. Database (schema `email`)

### 6.1 `email.email_messages`

| Column | Notes |
| --- | --- |
| id (uuid) | Message id |
| tenant\_id, user\_id | Optional links to the caller's records |
| template | Template name (enum) |
| locale | en, te, hi |
| to\_email, to\_name | Recipient |
| subject | Rendered subject (no links or tokens in subjects) |
| status | QUEUED, SENDING, SENT, FAILED, DEAD, EXPIRED, SUPPRESSED, CANCELLED |
| priority | HIGH (reset, security), NORMAL |
| payload\_encrypted | Template data encrypted with `ENCRYPTION_KEY`; **set to null after SENT or when expired** so reset links are not kept |
| idempotency\_key | Unique per calling service |
| attempts, next\_attempt\_at, last\_error | Retry control |
| provider, provider\_message\_id | For example gmail\_smtp and the Message-ID header |
| expires\_at | Do not send after this time |
| request\_id, caller\_service | Tracing |
| created\_at, sent\_at | Timing |

Indexes: unique (caller\_service, idempotency\_key), (status, next\_attempt\_at), (tenant\_id, created\_at), (to\_email, template, created\_at).

### 6.2 `email.email_attempts`

id, message\_id, attempt\_no, started\_at, finished\_at, result (OK, TEMP\_FAIL, PERM\_FAIL), smtp\_code, error\_text (sanitised), duration\_ms.

### 6.3 `email.email_suppressions`

email, reason (HARD\_BOUNCE, COMPLAINT, MANUAL), created\_at, created\_by. Hard-bounce addresses (permanent SMTP 5xx for an unknown mailbox) are added automatically after a PERM\_FAIL with a mailbox error.

## 7. Sending Logic

1. **Accept:** authenticate, validate, check idempotency, check rate limits, encrypt the data, insert as QUEUED, return 202
2. **Worker loop** (every 2 seconds, batch of 10): pick due rows with `FOR UPDATE SKIP LOCKED`, order HIGH priority first, set SENDING
3. **Render:** decrypt data, render subject, HTML (CSS inlined) and text with Jinja2 autoescape on; fall back to English if the locale template is missing
4. **Send** through the provider with the headers From, To, Reply-To, Message-ID, Date, MIME multipart/alternative
5. **Success:** status SENT, `sent_at`, store provider message id, **null out `payload_encrypted`**
6. **Temporary failure** (timeouts, 4xx SMTP, connection errors): retry with backoff 1 min, 5 min, 15 min, 1 hour, 6 hours; after 5 attempts status DEAD and an error log
7. **Permanent failure** (5xx, invalid recipient): status FAILED, add suppression if the mailbox does not exist
8. **Expiry:** before each send check `expires_at`; if passed, status EXPIRED and nothing is sent
9. **Crash safety:** rows stuck in SENDING for more than 5 minutes return to QUEUED on startup and every minute
10. **Rate limits:** per recipient and template: at most 5 per hour (reset and alert emails); per calling service: 60 per minute; global daily counter checked against `DAILY_SEND_LIMIT`; when 80% is reached log a warning, at 100% delay NORMAL priority emails to the next day but still send HIGH priority

## 8. Gmail Sender Setup

Use a **dedicated Gmail or Google Workspace account** for sending, for example `ferti.noreply@gmail.com` or `noreply@yourdomain.com`; do not use a personal inbox.

**Steps**

1. Sign in to the sender account and turn on **2-Step Verification** (Google Account > Security)
2. Create an **App Password** (Google Account > Security > App passwords, name it "Ferti+ Email Service"); copy the 16-character password. If the App passwords option is missing, 2-Step Verification is off, or a Workspace administrator has blocked it
3. Put the values in `.env`: `GMAIL_USER` and `GMAIL_APP_PASSWORD` (never commit this file)
4. SMTP settings: host `smtp.gmail.com`, port **587** with STARTTLS (or 465 with SSL), username the full Gmail address, password the app password
5. The visible From address is the authenticated account; to show a different address, add it in Gmail under Settings > Accounts > Send mail as and verify it
6. Optional: set `MAIL_REPLY_TO` to the support mailbox

**Limits and cautions**

- Gmail caps how many emails an account may send per day: about 500 recipients for a free Gmail account and about 2,000 for Google Workspace (confirm the current limits in Google's documentation). Set `DAILY_SEND_LIMIT` below the cap
- Gmail is suitable for early pilots. Before going to many shops, plan to move to a transactional provider (for example Amazon SES, SendGrid or Brevo) by adding another provider class; callers will not change
- If you use a custom domain with Workspace, set up SPF, DKIM and DMARC for better inbox delivery
- If Google rejects the app password for a Workspace account, the alternative is the **Gmail API with OAuth 2** (`GmailApiProvider`); keep the same interface
- Never send from a user's address; always send from the system sender

## 9. Configuration (`.env.example`)

| Variable | Example and meaning |
| --- | --- |
| ENV | development, staging, production |
| EMAIL\_PROVIDER | `gmail_smtp`, `console` or `mailpit` |
| GMAIL\_SMTP\_HOST, GMAIL\_SMTP\_PORT | `smtp.gmail.com`, `587` |
| GMAIL\_USER, GMAIL\_APP\_PASSWORD | Sender account and app password |
| MAIL\_FROM\_NAME, MAIL\_FROM\_ADDRESS | `Ferti+` and the Gmail address |
| MAIL\_REPLY\_TO, SUPPORT\_EMAIL | Support mailbox |
| APP\_BASE\_URL | Allowed base URL for links, for example `https://app.ferti.example` |
| DATABASE\_URL | Async PostgreSQL URL, schema `email` |
| ENCRYPTION\_KEY | 32-byte key for payload encryption |
| SERVICE\_API\_KEYS | Comma-separated `service:key` pairs, for example `beta_organization:...` |
| ADMIN\_API\_KEY | For retry and listing endpoints |
| DAILY\_SEND\_LIMIT | `400` for free Gmail |
| WORKER\_POLL\_SECONDS, WORKER\_BATCH\_SIZE, MAX\_ATTEMPTS | `2`, `10`, `5` |
| MAILPIT\_HOST, MAILPIT\_PORT | `mailpit`, `1025` in development |
| LOG\_LEVEL | `INFO` |

The service refuses to start in production if `GMAIL_USER`, `GMAIL_APP_PASSWORD` or `ENCRYPTION_KEY` is missing.

## 10. How Other Services Call It

| Event | Caller | Template | Idempotency key |
| --- | --- | --- | --- |
| Forgot password requested | beta\_organization | PASSWORD\_RESET\_REQUESTED | `pwd-reset:<resetRequestId>` |
| Password reset or changed | beta\_organization | PASSWORD\_CHANGED | `pwd-changed:<passwordHistoryId>` |
| 3rd failed login, and account lock | beta\_organization | LOGIN\_FAILED\_ALERT | `login-failed:<userId>:<hourBucket>` |
| Super Admin approves a shop | beta\_organization | ONBOARDING\_APPROVED | `onboarding-approved:<tenantId>` |

- Callers use a small client class `EmailClient` (httpx async, timeout 5 seconds, 2 quick retries). If the email service is unreachable the user action still succeeds; the caller logs the failure and records an audit or auth event
- Callers create reset tokens and links; the email service never creates tokens
- Add `beta_email` to the README services table (port 8005, internal only) and to `docker-compose.test.yml`

## 11. Security and Privacy

- Service-to-service authentication with `X-Service-Key`; keys are per service and rotatable; compare in constant time
- Reset links and other sensitive fields live only in the encrypted payload and are removed after sending; they are never written to logs, attempts, errors or the status API
- Logs mask emails (`ra***@gmail.com`) and never print the body, links, tokens or app password
- Rate limits and per-recipient caps to stop the service being used to spam or to bombard a person's inbox
- Only links under `APP_BASE_URL` are accepted; HTML is escaped; no remote images or trackers
- Every email says why the person received it and how to contact support; security emails advise what to do if the action was not theirs
- Retention: delete message rows and attempts older than 90 days (keep metadata only); suppression list kept until removed
- Personal data minimised to what the email needs; handled in line with the DPDP requirements in the platform specification

## 12. Testing

- **Unit tests:** schema validation per template; link allow-list; renderer output contains required fields and no unescaped HTML; backoff schedule; rate limit and idempotency logic; encryption round trip
- **Provider tests:** `GmailSmtpProvider` with a mocked SMTP server (success, 4xx temporary, 5xx permanent, timeout)
- **Worker tests:** retry then DEAD after 5 attempts; stuck SENDING recovery; EXPIRED reset email is not sent; payload is nulled after SENT
- **API tests:** 401 without key, 202 on valid request, repeat with the same Idempotency-Key returns the same id, 422 on bad data
- **Integration test (docker-compose.test.yml):** start Mailpit, send each of the four emails, read them from the Mailpit API, check subject, button link and plain-text part
- Add `beta_email_tests` to `run-tests.ps1`; target coverage 85% or more

## 13. Acceptance Criteria

1. `services/beta_email` follows the same structure, Dockerfile, `/health` and `/docs` pattern as the other services and runs on port 8005 inside the Docker network only.
2. `POST /v1/emails` with each of the four templates returns 202, and the email appears in Mailpit in development with a correct HTML and plain-text version.
3. With `EMAIL_PROVIDER=gmail_smtp` and a valid app password, the same emails arrive in a real inbox from the configured sender name and address.
4. The onboarding email shows shop name, **Tenant ID**, reference number and a sign-in button, and contains no password.
5. The reset email contains a working link under `APP_BASE_URL` and is not sent after `expiresAt`.
6. A repeated request with the same `Idempotency-Key` never produces a second email.
7. Temporary Gmail failures are retried with backoff and end as DEAD after 5 attempts; nothing is lost on restart.
8. After sending, `payload_encrypted` is null; no log line or API response contains a reset link, token or the app password.
9. A request without a valid service key returns 401.
10. Failed-login alerts are limited to one per account per hour.
11. All tests pass with `.\run-tests.ps1`.

## 14. Implementation Order

| Step | Deliverable |
| --- | --- |
| 1 | Scaffold the service, config, Dockerfile, `/health`, add to docker-compose with Mailpit |
| 2 | Models and Alembic migration for the `email` schema |
| 3 | Provider interface, `ConsoleProvider`, SMTP provider (Mailpit first, then Gmail) |
| 4 | Templates and renderer for the four emails (HTML, text, subject) with preview endpoint |
| 5 | `POST /v1/emails`, validation, idempotency, encryption, service-key auth |
| 6 | Worker with retries, backoff, expiry, stuck-row recovery, rate limits |
| 7 | Status and list endpoints, suppression list |
| 8 | `EmailClient` in `beta_organization` and wiring to the four events |
| 9 | Tests, README with Gmail setup, update the main README and run scripts |

## 15. Ready-to-Paste Prompt for GitHub Copilot

Attach this document, the README and the Tenant Onboarding and Authentication specification.

```
Create a new FastAPI service named beta_email under services/ in the Ferti+ monorepo, using the same structure, Dockerfile, requirements.txt, /health, /docs and tests layout as the other services. Follow the attached specification exactly.

Key points: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, aiosmtplib, Jinja2, css-inline, cryptography. Internal service on port 8005 (not routed by the gateway). Send emails through Gmail SMTP (smtp.gmail.com:587 STARTTLS with an App Password from env GMAIL_USER and GMAIL_APP_PASSWORD) behind an EmailProvider interface; also ConsoleProvider and a Mailpit SMTP provider for development (add mailpit to docker-compose).

Implement POST /v1/emails (202 Accepted, Idempotency-Key, X-Service-Key auth, per-template Pydantic validation, link allow-list under APP_BASE_URL), GET /v1/emails/{id}, GET /v1/emails, POST /v1/emails/{id}/retry, template preview (disabled in production), /health and /ready.

Templates (HTML + text + subject, English first, responsive, brand green #0B6B3A, big button): PASSWORD_RESET_REQUESTED, PASSWORD_CHANGED, LOGIN_FAILED_ALERT, ONBOARDING_APPROVED (must show shop name, Tenant ID, reference number, sign-in button, and never a password).

Database schema email: email_messages (encrypted payload that is nulled after sending), email_attempts, email_suppressions. Worker: DB queue with FOR UPDATE SKIP LOCKED, priority, retries with backoff 1m/5m/15m/1h/6h, DEAD after 5 attempts, expiry check, stuck-row recovery, per-recipient and daily rate limits. Never log links, tokens, bodies or the app password; mask email addresses in logs.

Also add an EmailClient to beta_organization (httpx, 5 s timeout, 2 retries, failures do not break the user action) and call it for forgot password, password changed, failed login alert (3rd failure and lockout, max one per hour) and tenant approval.

Write unit, worker, API and Mailpit integration tests, add beta_email_tests to run-tests.ps1 and docker-compose.test.yml, and update the README. Work step by step and run tests after each step.
```
