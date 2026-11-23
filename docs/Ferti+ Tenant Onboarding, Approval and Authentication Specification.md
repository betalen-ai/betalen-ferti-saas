# Ferti+ Tenant Onboarding, Approval and Authentication Specification

Nov 22, 2026 · @Prasad

Today a shop owner can sign up and sign in at once. In the real world a new shop must be **reviewed and approved by the Ferti+ Super Admin** before it can use the system. This document specifies the approval-based onboarding flow, richer tenant details, Google (Gmail) sign-in with registration, phone OTP sign-in, token handling, and the new tables for refresh tokens, authentication events, password history and the audit log. It **replaces** the self-activation behaviour in the earlier specifications (Corporate Website 6.6 to 6.8, Shop Owner Application section 2, Backend API section 3.1) and the "tenant states" in the SaaS Platform Expectations document.

## 1. Roles and Principles

| Role | Who | Access |
| --- | --- | --- |
| **Super Admin** | Ferti+ team members | Operations Console only: review onboarding requests, manage tenants, view platform metrics |
| **Tenant Owner** | Fertilizer shop owner | The shop application, only after the shop is approved |

- Registration creates a **request**, not a working account. No tokens are issued until the shop is approved
- The Super Admin sign-in is separate from the shop sign-in (own endpoints, own user table, mandatory two-step verification)
- Every important action is written to the audit log and every sign-in event to the authentication log
- Passwords are never emailed or shown to anyone, including the Super Admin

**About sending login credentials:** the owner chooses their own password at registration, so approval only needs to send an **approval message with the sign-in link**. If the Super Admin ever creates an account for a shop (assisted onboarding), the system sends a **single-use set-password link** valid for 24 hours, never a plain password.

## 2. Tenant Lifecycle

```
Submitted -> PENDING_REVIEW --approve--> ACTIVE <--reactivate-- SUSPENDED
                 |  ^                      |
                 |  +--owner resubmits-----+--suspend--> SUSPENDED
                 +--request more info--> NEEDS_INFO
                 +--reject--> REJECTED         ACTIVE --owner closes--> CLOSED
```

| Status | Meaning | Can sign in to the app |
| --- | --- | --- |
| PENDING\_REVIEW | Submitted, waiting for the Super Admin | No |
| NEEDS\_INFO | Admin asked for more details or documents | No (owner uses the link in the message to update) |
| REJECTED | Not approved, reason recorded | No |
| ACTIVE | Approved and working, Free plan | Yes |
| SUSPENDED | Blocked by Super Admin (abuse, non-payment, legal) | No |
| CLOSED | Owner closed the account; data retained for the retention period | No |

## 3. Onboarding Request: Details to Collect

Sign up is a short multi-step form (big buttons, progress bar, can go back).

### 3.1 Step 1: Owner

| Field | Rule |
| --- | --- |
| Owner full name | Required, 2 to 80 characters |
| Email address | Required, valid format, unique across the platform, lower-cased |
| Mobile number | Required, fixed prefix **+91**, 10 digits starting 6 to 9, unique; verified by OTP before the form can be submitted |
| Password | Required, min 8 characters with upper case, lower case, number and symbol; strength meter; show or hide; blocked if in a common or breached password list; not equal to email or name |
| Confirm password | Must match |
| Alternate mobile | Optional |
| Preferred language | English, Telugu, Hindi (more later) |

### 3.2 Step 2: Shop

| Field | Rule |
| --- | --- |
| Shop name | Required, 2 to 100 characters; shown top-right in the app |
| Shop type | Multi-select: Fertilizers, Pesticides, Seeds, Machinery and equipment |
| Address | Door or street, village or town, mandal or taluk, district, state (dropdown), PIN code (6 digits) |
| Location | Optional map pin or "use my location" |
| GSTIN | Optional, 15-character format check; mandatory later if turnover requires |
| PAN of owner or shop | Optional |
| Years in business | Optional number |
| Approximate farmers served | Optional range (under 100, 100 to 500, 500 to 2000, over 2000) |
| Current way of keeping accounts | Paper, Excel, other software |
| How did you hear about Ferti+ | Optional, plus referral code |

### 3.3 Step 3: Licences and documents

Fertilizer, pesticide and seed trade is licensed, so the Super Admin needs proof.

| Item | Rule |
| --- | --- |
| Fertilizer licence number and expiry | Required if Fertilizers selected |
| Pesticide licence number and expiry | Required if Pesticides selected |
| Seed licence number and expiry | Required if Seeds selected |
| Upload: licence copies, GST certificate (if any), shop board photo | PDF, JPG or PNG, max 5 MB each, max 6 files; virus scan; stored privately and opened only through short-lived signed links |

Exact licence requirements differ by state; the compliance advisor confirms which items are mandatory.

### 3.4 Step 4: Verify and submit

- Phone verification by OTP (if not already done)
- Review screen with edit links
- Consent checkboxes: Terms of Service and Privacy Policy, and consent to Ferti+ contacting the owner by SMS, email and WhatsApp about the application; consent text version and time are stored
- CAPTCHA, then **Submit request**

### 3.5 After submission

- Screen: **"Thank you. Your request is under review. We will let you know by SMS and email once it is approved."** with the reference number and expected time (for example, within 2 working days)
- Email and SMS confirmation of receipt
- The Super Admin gets a notification of a new request

## 4. Super Admin Review

- **Queue:** list with status filter, search by shop, owner, mobile, district; oldest first; shows age and a red badge if waiting longer than the target
- **Detail page:** all submitted data, documents viewer, duplicate checks (same mobile, GSTIN, licence number or address already registered), history of previous reviews
- **Actions (big buttons):**
  - **Approve:** tenant becomes ACTIVE on the Free plan, default categories and settings are seeded, owner is notified with the sign-in link
  - **Request more info:** choose items or write a note; status NEEDS\_INFO; owner receives a link to update and resubmit
  - **Reject:** reason required (dropdown plus note); owner is notified; owner may submit a fresh request after 7 days
- **Rules:** two admins cannot act on one request at the same time (lock for 10 minutes); every decision stores admin, time, reason and the exact data version reviewed; target decision time 2 working days
- **Other admin tools:** suspend or reactivate a tenant, resend approval message, view tenant list and sign-in history

### Notification messages

| Event | Message (short form) |
| --- | --- |
| Request received | "Ferti+: We received your request for \[Shop\]. Reference \[ID\]. We will inform you after review." |
| Approved | "Ferti+: Your shop \[Shop\] is approved. Sign in at \[link\] with your registered email, phone or Google account." |
| Needs info | "Ferti+: We need more details for \[Shop\]. Please update here: \[link\]." |
| Rejected | "Ferti+: We could not approve \[Shop\]. Reason: \[reason\]. Contact \[support\]." |
| Suspended | "Ferti+: Your account is suspended. Contact \[support\]." |

SMS templates must be registered on the telecom DLT platform before use in India.

## 5. Sign-In Behaviour by Tenant Status

The status message is shown **only after the person proves who they are** (correct password, verified OTP, or verified Google identity). A wrong password always gives the same generic error, so nobody can discover which emails or shops are registered.

| Tenant status | What the owner sees after proving identity |
| --- | --- |
| PENDING\_REVIEW | **"Your request is under review. We will let you know once it is approved."** (with reference number and submitted date) |
| NEEDS\_INFO | "We need more details to approve your shop." with an **Update details** button |
| REJECTED | "Your request was not approved." with the reason and support contact |
| SUSPENDED | "Your account is suspended. Please contact support." |
| CLOSED | "This account is closed." with a link to start a new request |
| ACTIVE | Access token and refresh token issued; app opens |

No access or refresh token is issued for any status other than ACTIVE.

## 6. Sign-In Methods

### 6.1 Email and password

POST `/auth/login` with email and password. Check order: rate limit, user exists, password matches, tenant status, then issue tokens. Five wrong attempts lock the account for 15 minutes and add CAPTCHA.

### 6.2 Phone number with OTP

This was missing and is now fully specified.

- **Send:** POST `/auth/otp/send` with `{ phone, purpose }` where purpose is `LOGIN`, `REGISTER_VERIFY` or `RESET_PASSWORD`
- **Verify:** POST `/auth/otp/verify` with `{ phone, otp, purpose }`
- Rules: 6 digits, generated with a secure random source, stored only as a hash, valid 5 minutes, single use; resend after 30 seconds; at most 5 sends per phone per hour and 20 per IP per hour; at most 5 wrong tries, then the OTP is cancelled
- For `LOGIN` the same response ("If this number is registered, an OTP has been sent") is returned whether or not the number exists
- After a correct OTP for `LOGIN`: apply the status table in section 5, then issue tokens only if ACTIVE
- For `REGISTER_VERIFY` a successful OTP returns a short-lived `phoneVerifiedToken` (15 minutes) that the sign-up submission must include
- In development the OTP is printed in the service log; in production it is sent by a registered SMS provider

### 6.3 Google (Gmail) sign-in and registration

The Angular app uses Google Identity Services and sends the Google **ID token** to the API. The API never trusts the browser's claims: it verifies the token's signature, audience (our client ID), issuer, expiry and `email_verified`.

```
Angular: user clicks "Continue with Google" -> gets Google ID token
   |
   v  POST /auth/google { idToken }
API: verify token -> read sub, email, name, picture, email_verified
   |
   +-- email found in our users table?
   |      |
   |      +-- YES -> check tenant status
   |      |            ACTIVE        -> link Google identity if new, issue access + refresh tokens
   |      |            other status  -> return status error (section 5), no tokens
   |      |
   |      +-- NO  -> 200 { registrationRequired: true, registrationToken,
   |                       prefill: { email, name } }   (token valid 15 minutes)
   |
   v
Angular shows registration screen (email and name from Google are read-only)
   asks: shop name, mobile (+91, OTP verified), password, shop details, documents, consent
   |
   v  POST /auth/google/register { registrationToken, phoneVerifiedToken, ...fields }
API: creates tenant in PENDING_REVIEW, owner user with verified email, Google identity,
     password hash -> returns "request under review"; no tokens
```

- Claims used from Google: `sub` (stable Google id), `email`, `email_verified`, `name`, `given_name`, `picture`. Only a verified Google email is accepted
- The password is still collected so the owner can also sign in with email and password or reset it later
- If the email exists with a password account but without a Google link, Google sign-in links the identity automatically because Google has verified the same email
- Registered mobile still needs OTP verification during Google registration

## 7. Tokens and Sessions

| Token | Format | Life | Storage and handling |
| --- | --- | --- | --- |
| Access token | Signed JWT with `sub` (user id), `tenantId`, `role`, `jti`, `iat`, `exp` | 15 minutes | Sent as a bearer token or secure cookie; the gateway checks signature and expiry; tenant status is rechecked on every refresh |
| Refresh token | Random 256-bit opaque string (not a JWT) | 30 days, sliding up to 90 days | httpOnly, secure, SameSite cookie; only its SHA-256 hash is stored in `refresh_tokens` |

- **Rotation:** every use of a refresh token issues a new one and marks the old one as replaced. Each login starts a **token family**
- **Reuse detection:** if an already-used refresh token is presented again, the whole family is revoked, the user must sign in again, and a `REFRESH_REUSE_DETECTED` event is logged
- **Refresh endpoint** returns 401 and revokes the family when the tenant is no longer ACTIVE, the user is disabled, or the password was changed after the token was issued
- **Logout** revokes the current token; **Sign out all devices** revokes every family for the user
- Change or reset of password revokes all refresh tokens
- Angular keeps the access token in memory only and never in localStorage

## 8. Database Tables

Naming follows the earlier design (`org` schema for tenants and users). All ids are UUIDs, timestamps are UTC (`timestamptz`).

### 8.1 `org.tenants` (extended)

| Column | Notes |
| --- | --- |
| id, name (shop name), status, plan | Status values in section 2 |
| shop\_types text\[\], gstin, pan | Optional tax fields |
| address\_line, village\_town, mandal\_taluk, district, state, pincode, latitude, longitude | Address |
| years\_in\_business, farmers\_served\_range, current\_system, referral\_code, heard\_from | Optional profile |
| fertilizer\_licence\_no, fertilizer\_licence\_expiry, pesticide\_licence\_no, pesticide\_licence\_expiry, seed\_licence\_no, seed\_licence\_expiry | Licences |
| language, alternate\_mobile | Preferences |
| submitted\_at, reviewed\_at, reviewed\_by, review\_reason, approved\_at, suspended\_at, closed\_at | Lifecycle |
| reference\_no | Human-friendly request number, for example FRT-2026-000123 |
| consent\_terms\_version, consent\_at, consent\_ip | Consent record |
| created\_at, updated\_at, version | Standard |

### 8.2 `org.tenant_documents`

id, tenant\_id, doc\_type (FERTILIZER\_LICENCE, PESTICIDE\_LICENCE, SEED\_LICENCE, GST\_CERT, SHOP\_PHOTO, OTHER), file\_name, storage\_key, mime\_type, size\_bytes, scan\_status, uploaded\_at, verified (bool), verified\_by.

### 8.3 `org.tenant_reviews`

id, tenant\_id, action (SUBMITTED, APPROVED, REJECTED, INFO\_REQUESTED, RESUBMITTED, SUSPENDED, REACTIVATED), admin\_id, reason\_code, note, data\_snapshot jsonb, created\_at.

### 8.4 `org.users` (shop owners)

id, tenant\_id, name, email (unique, lower-case), email\_verified, phone (unique, stored as +91XXXXXXXXXX), phone\_verified, password\_hash (nullable until set), status (ACTIVE, DISABLED), failed\_login\_count, locked\_until, last\_login\_at, password\_changed\_at, created\_at.

### 8.5 `org.auth_identities`

id, user\_id, provider (PASSWORD, GOOGLE, PHONE\_OTP), provider\_user\_id (Google `sub`), email\_at\_link, linked\_at, last\_used\_at. Unique on (provider, provider\_user\_id).

### 8.6 `org.platform_admins` (Super Admins)

id, name, email, password\_hash, totp\_secret\_encrypted, role (SUPER\_ADMIN, SUPPORT, REVIEWER), status, last\_login\_at. Separate from `users`.

### 8.7 `org.refresh_tokens`

| Column | Notes |
| --- | --- |
| id, user\_id, tenant\_id | Owner of the token |
| family\_id | Groups tokens from one login |
| token\_hash | SHA-256 of the token; the token itself is never stored |
| issued\_at, expires\_at, last\_used\_at | Timing |
| revoked\_at, revoked\_reason | LOGOUT, ROTATED, REUSE\_DETECTED, PASSWORD\_CHANGED, ADMIN, TENANT\_SUSPENDED |
| replaced\_by\_id | Next token in the chain |
| ip, user\_agent, device\_label | Shown in "active sessions" |

Indexes: unique (token\_hash), (user\_id, revoked\_at), (family\_id). A nightly job deletes rows expired for more than 30 days.

### 8.8 `org.auth_events` (login log)

| Column | Notes |
| --- | --- |
| id, created\_at | Event id and time |
| tenant\_id, user\_id | Null when unknown (for example wrong email) |
| identifier | Email or phone as typed, masked (`ra***@gmail.com`, `+91 98*****210`) |
| method | PASSWORD, OTP, GOOGLE, REFRESH, ADMIN |
| event\_type | LOGIN\_SUCCESS, LOGIN\_FAILED, LOGIN\_BLOCKED\_PENDING, LOGIN\_BLOCKED\_REJECTED, LOGIN\_BLOCKED\_SUSPENDED, ACCOUNT\_LOCKED, OTP\_SENT, OTP\_VERIFIED, OTP\_FAILED, GOOGLE\_LOGIN, GOOGLE\_REGISTRATION\_STARTED, REGISTRATION\_SUBMITTED, TOKEN\_REFRESHED, REFRESH\_REUSE\_DETECTED, LOGOUT, LOGOUT\_ALL, PASSWORD\_RESET\_REQUESTED, PASSWORD\_RESET\_COMPLETED |
| success, failure\_reason | Reason code such as BAD\_PASSWORD, OTP\_EXPIRED, TENANT\_PENDING |
| ip, user\_agent, device, approx\_location | Context |
| request\_id | Correlates with logs |

Shop owners see their own recent sign-ins (date, device, place, result) under Settings > Security; the Super Admin sees them per tenant.

### 8.9 `org.password_history`

id, user\_id, password\_hash, change\_type (REGISTER, CHANGE, RESET, ADMIN\_RESET), changed\_at, changed\_by (user or admin), ip, user\_agent. Rules: a new password cannot equal any of the last 5; keep history for 2 years; hashes use Argon2id (or bcrypt cost 12 or more).

### 8.10 `org.otp_requests`

id, phone, purpose, otp\_hash, expires\_at, attempts, verified\_at, cancelled\_at, ip, created\_at. The code is never stored in plain text.

### 8.11 `org.audit_log`

One append-only table that records what every tenant does.

| Column | Type | Notes |
| --- | --- | --- |
| audit\_log\_id | uuid, primary key | Event id |
| tenant\_id | uuid, not null | Shop the event belongs to (also set for admin actions on that shop) |
| actor\_user\_id | uuid | Owner (or later staff) who did it; null for system |
| actor\_type | text | OWNER, STAFF, SUPER\_ADMIN, SYSTEM |
| action | text | CREATE, UPDATE, DELETE, CANCEL, PAYMENT, APPROVE, LOGIN and so on |
| entity\_name | text | Table name, for example `inventory.brands` |
| entity\_id | uuid | Id of the specific record |
| json\_payload | jsonb | Full event detail, structure below |
| request\_id, ip | text | Traceability |
| created\_at | timestamptz | Event time |

Indexes: (tenant\_id, created\_at desc), (tenant\_id, entity\_name, entity\_id), and a GIN index on `json_payload` if searching inside it is needed. Partition by month once volume grows.

**`json_payload` structure (what the owner can see)**

```json
{
  "entityName": "inventory.products",
  "entityId": "7c1b2c0e-...",
  "action": "CREATE",
  "summary": "Added product DAP (IFFCO) with 2 packs",
  "actor": { "id": "u_12", "name": "Ramesh", "role": "OWNER" },
  "before": null,
  "after": {
    "name": "DAP", "brand": "IFFCO", "category": "Chemical fertilizer",
    "packs": [ { "label": "50 kg bag", "mrp": "1350.00" } ]
  },
  "changes": [],
  "related": [ { "entityName": "inventory.brands", "entityId": "b1..." } ],
  "source": "WEB"
}
```

For an update, `before` and `after` hold the old and new values and `changes` lists the changed fields, for example `[{ "field": "mrp", "from": "1300.00", "to": "1350.00" }]`.

**Events that must be written (every business action)**

| Area | Events |
| --- | --- |
| Brands and categories | Added, edited, deactivated |
| Products and packs | Added, edited, price changed, deactivated, pack added |
| Stock | Stock in, adjustment, damage or loss, batch added |
| Farmers | Added, edited, credit limit changed, deactivated |
| Seasons and settings | Season added or edited, interest or discount defaults changed, tax mode changed |
| Sales | Bill created (spot, credit or part), bill edited before saving, bill cancelled with reason, bill printed or shared |
| Credit and khata | Credit given, interest added, payment received, adjustment or write-off, reminder sent |
| Account | Shop profile changed, password changed, sign-in methods linked, sessions revoked, data exported |
| Platform (Super Admin) | Request approved, rejected, info requested, tenant suspended or reactivated, support viewing started or ended |

**Rules**

- Written by the backend **inside the same database transaction** as the change; if the audit write fails, the change fails
- Append-only: the application database user has INSERT and SELECT only on this table; no update or delete
- Never store passwords, password hashes, tokens, OTPs or full document contents in `json_payload`
- Money values as decimal strings; names and ids included so the record is readable even if the entity changes later
- The owner sees an **Activity Log** screen: filter by date, user, entity (brand, product, bill, farmer, khata) and open any event to see the full payload as a readable before-and-after view; export to Excel
- Retention: at least 5 years or the period legal advice requires

## 9. API Endpoints

Base path `/api/v1`. All errors use the common problem format with a stable `code`.

### 9.1 Onboarding and shop authentication

| Method and path | Purpose | Success | Error codes |
| --- | --- | --- | --- |
| POST `/onboarding/requests` | Submit a registration request with all fields, documents and `phoneVerifiedToken` | 201 with `referenceNo`, status PENDING\_REVIEW | 409 EMAIL\_EXISTS, 409 PHONE\_EXISTS, 422 validation |
| POST `/onboarding/documents` | Upload a document before submit (returns document id) | 201 | 413, 415 |
| POST `/onboarding/requests/{id}/resubmit` | Owner updates details after NEEDS\_INFO using the emailed token | 200 | 401 invalid or expired link |
| POST `/auth/otp/send`, POST `/auth/otp/verify` | Phone OTP for LOGIN, REGISTER\_VERIFY, RESET\_PASSWORD | 200 | 429 too many requests, 400 OTP\_INVALID or OTP\_EXPIRED |
| POST `/auth/login` | Email and password | 200 with tokens (ACTIVE only) | 401 INVALID\_CREDENTIALS, 403 status codes below |
| POST `/auth/google` | Verify Google ID token and sign in, or return `registrationRequired` | 200 | 401 GOOGLE\_TOKEN\_INVALID, 403 status codes below |
| POST `/auth/google/register` | Create a PENDING\_REVIEW request from Google data plus form fields | 201 | 409, 422, 401 registrationToken expired |
| POST `/auth/refresh` | Rotate refresh token and return a new access token | 200 | 401 REFRESH\_INVALID, REFRESH\_REUSED, TENANT\_NOT\_ACTIVE |
| POST `/auth/logout`, POST `/auth/logout-all` | Revoke current or all sessions | 204 | None |
| POST `/auth/forgot-password`, POST `/auth/reset-password` | Reset by emailed link or phone OTP | 200 | 400 token expired |
| POST `/auth/change-password` | Signed-in change; needs current password | 204 | 400 PASSWORD\_REUSED, 401 |
| GET `/auth/sessions`, DELETE `/auth/sessions/{id}` | Active devices and revoke one | 200 or 204 | None |
| GET `/auth/events` | Owner's own sign-in history | 200 | None |
| GET `/audit-logs` | Tenant activity log with filters `from`, `to`, `entityName`, `entityId`, `action`, `actor` | 200 | None |
| GET `/audit-logs/{id}` | One event with full payload | 200 | 404 |

Status error codes for sign-in (HTTP 403, returned only after identity is proven): `TENANT_PENDING_REVIEW` (message: "Your request is under review. We will let you know once it is approved."), `TENANT_NEEDS_INFO`, `TENANT_REJECTED`, `TENANT_SUSPENDED`, `TENANT_CLOSED`. The body also carries `referenceNo` and `submittedAt` when relevant.

### 9.2 Super Admin (Operations Console)

| Method and path | Purpose |
| --- | --- |
| POST `/admin/auth/login`, `/admin/auth/verify-2fa`, `/admin/auth/refresh`, `/admin/auth/logout` | Separate admin sign-in with mandatory two-step verification |
| GET `/admin/onboarding-requests` | Queue with filters (status, district, date) and pagination |
| GET `/admin/onboarding-requests/{id}` | Details, signed document links, duplicate-check results, review history |
| POST `/admin/onboarding-requests/{id}/lock` | Take the request for review (10-minute lock) |
| POST `/admin/onboarding-requests/{id}/approve` | Approve; activates tenant, seeds defaults, sends approval message |
| POST `/admin/onboarding-requests/{id}/request-info` | Ask for more details with a note |
| POST `/admin/onboarding-requests/{id}/reject` | Reject with reason code and note |
| GET `/admin/tenants` and GET `/admin/tenants/{id}` | Tenant list and profile with sign-in history |
| POST `/admin/tenants/{id}/suspend` and `/reactivate` | Change status with reason |
| POST `/admin/tenants/{id}/resend-approval` | Resend the approval message |
| GET `/admin/audit-logs?tenantId=` | Audit trail for a tenant, including admin actions |

Every admin write needs a reason where stated and creates `tenant_reviews`, `audit_log` and `auth_events` rows as applicable.

## 10. Screens

**Shop website and app (Angular)**

- **Sign in:** tabs Email and Phone, **Continue with Google**; status banners from section 5; link to sign up
- **Sign up (multi-step):** Owner, Shop, Licences and documents, Verify and submit; progress indicator; save draft in the browser until submit
- **Google registration screen:** email and name read-only from Google; asks mobile with OTP, password, shop name and shop details; same steps as sign up with those fields prefilled
- **Request received:** reference number, what happens next, support contact
- **Under review page** (after sign-in while pending): status timeline (Submitted, Under review, Decision), submitted date, contact link
- **Update details:** for NEEDS\_INFO; shows the admin's note and the fields to fix
- **Settings > Security:** change password, active sessions with revoke, recent sign-ins
- **Activity Log:** filters, table with large rows, detail drawer showing before and after

**Operations Console (Super Admin)**

- Sign in with two-step verification
- Onboarding queue, request detail with document viewer, Approve, Request info and Reject dialogs
- Tenant list and profile, sign-in history, suspend and reactivate

All screens follow the POS-style design rules: controls at least 48 px high, bordered sections, plain language.

## 11. Security and Privacy

- Rate limits and CAPTCHA on registration, login, OTP and Google endpoints; per-IP and per-identifier
- Generic responses for unknown emails and phones; status messages only after identity is proven
- Verify Google ID tokens server side (signature, `aud`, `iss`, `exp`, `email_verified`); keep the Google client secret out of the Angular app
- Registration, phone-verified and resubmit tokens are signed, single purpose, short lived and single use
- Document uploads: type and size checks, malware scan, random storage names, private bucket, signed URLs that expire in 5 minutes, access logged
- Admin console: separate host or path, allow-listed access if possible, mandatory TOTP, shorter sessions
- DPDP readiness: collect only what review needs; no Aadhaar numbers; store consent version and time; delete rejected or abandoned requests and their documents after 90 days; the owner can ask for correction or erasure
- Passwords and OTPs never appear in logs, emails, audit payloads or error messages

## 12. Impact on Other Specifications

| Document | Change |
| --- | --- |
| Corporate Website 6.6 to 6.8 | Sign up becomes a multi-step request form; add Under review and Google registration screens; sign-in shows status messages |
| Shop Owner Application section 2 | Replace instant activation with this flow; add Settings > Security and Activity Log |
| Backend API section 3.1 | Replace the auth list with section 9 |
| SaaS Platform Expectations section 3 | Tenant states replaced by section 2; section 13 (Operations Console) becomes a **Must** for launch |
| README roadmap step 3 | `beta_organization` now includes onboarding review, admin auth, token tables, auth events, password history and audit log |

## 13. Acceptance Criteria

1. Submitting the sign-up form creates a tenant in PENDING\_REVIEW and an owner user, and **never** issues tokens.
2. Signing in with correct credentials while PENDING\_REVIEW returns 403 `TENANT_PENDING_REVIEW` and the screen says the request is under review; wrong credentials return the generic invalid-credentials error.
3. After the Super Admin approves, the same owner can sign in with email, phone OTP or Google and receives an access token (15 minutes) and a refresh token (30 days).
4. Approval, rejection and info-request each send the owner an SMS and an email and are recorded in `tenant_reviews` and `audit_log`; no message contains a password.
5. Google sign-in with a known email and ACTIVE tenant signs in; with a known email and non-ACTIVE tenant shows the status message; with an unknown email returns `registrationRequired` and the registration screen collects shop name, mobile (OTP verified), password and details.
6. Google registration creates a PENDING\_REVIEW request and no tokens.
7. Phone OTP: 6 digits, 5-minute expiry, 30-second resend, 5 attempts, hashed storage, rate limits; unknown numbers receive the same response as known ones.
8. Refresh tokens rotate on every use; replaying a used token revokes the family and logs `REFRESH_REUSE_DETECTED`; password change revokes all refresh tokens.
9. Every sign-in attempt, success or failure, creates an `auth_events` row with method, result, IP and device.
10. Changing a password writes a `password_history` row and rejects reuse of the last 5 passwords.
11. Adding a brand, product, stock receipt, farmer, season, bill, credit, payment or cancellation each writes one `audit_log` row in the same transaction, with `entity_name`, `entity_id` and a `json_payload` containing the summary, actor and the before and after values.
12. The application database user cannot update or delete `audit_log` rows (verified by a test).
13. The owner can open the Activity Log, filter it and view the full detail of any event; no other tenant's events are ever visible.
14. Super Admin endpoints reject shop owner tokens, and shop endpoints reject admin tokens.

## 14. Ready-to-Paste Prompt for GitHub Copilot

Attach this document and the README.

```
Implement the Ferti+ tenant onboarding and authentication changes in the attached specification across beta_organization, api-gateway and the Angular app.

Backend (FastAPI, PostgreSQL, SQLAlchemy, Alembic): 1) migrations for extended org.tenants, tenant_documents, tenant_reviews, users, auth_identities, platform_admins, refresh_tokens, auth_events, password_history, otp_requests and audit_log (append-only: grant INSERT and SELECT only, add a trigger that blocks UPDATE and DELETE); 2) onboarding endpoints and the Super Admin review endpoints in section 9; 3) auth: email+password, phone OTP (6 digits, hashed, 5 min expiry, 5 attempts, rate limits), Google ID token verification (google-auth library) with registrationRequired and registration endpoints; 4) JWT access token (15 min) and opaque refresh token (30 days, SHA-256 hashed in DB, rotation with family reuse detection, httpOnly cookie); 5) only tenants with status ACTIVE receive tokens; for other statuses return 403 with codes TENANT_PENDING_REVIEW, TENANT_NEEDS_INFO, TENANT_REJECTED, TENANT_SUSPENDED, TENANT_CLOSED only after identity is proven; 6) an audit service that writes audit_log rows inside the same DB transaction as every create, update, cancel and payment, with json_payload containing entityName, entityId, action, summary, actor, before, after; 7) never log or email passwords, tokens or OTPs.

Frontend (Angular standalone components, Bootstrap 5.3, ng-bootstrap, Reactive Forms): multi-step sign up with +91 phone OTP verification, Google sign-in with registration screen, sign-in status banners including 'Your request is under review. We will let you know once it is approved.', Under review page, Update details page, Settings > Security (sessions and sign-in history) and an Activity Log screen. Super Admin console: queue, detail with documents, Approve, Request info, Reject.

Add unit tests for token rotation and reuse detection, OTP rules, status gating on every sign-in method and audit-log writes, plus an API test that proves a pending tenant can never obtain tokens. Work step by step and run the tests after each step.
```
