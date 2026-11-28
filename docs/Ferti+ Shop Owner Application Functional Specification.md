# Ferti+ Shop Owner Application: Functional Specification

Nov 19, 2026 · @Prasad

This document specifies the Ferti+ business application used by fertilizer shop owners after they sign in: brands, products, stock, farmers, khata (ledger) and billing with cash discount or credit interest. The public website is specified separately in "Ferti+ Corporate Website: Build Specification". Stack: Angular (standalone components, Angular CLI), Bootstrap 5.3 + ng-bootstrap, Angular Reactive Forms. Do not use React.

## 1. Scope and Users

- **Only user type:** the fertilizer shop owner (one account = one shop = one tenant). There are no farmer, admin or distributor logins
- **Farmers are records, not users.** The owner adds them as customers and keeps their khata
- **Currency and units:** INR (₹), Indian number format; dates as DD MMM YYYY
- **Free for the shop owner.** All features in this document are available on the free plan
- Backend and database are out of scope; use mock data and placeholder API endpoints behind Angular services

## 2. Authentication

Sign in and Sign up support four methods.

| Method | Sign in | Sign up | Notes |
| --- | --- | --- | --- |
| Email + password | Yes | Yes | Password min 8 characters, strength meter, show/hide toggle |
| Phone number + OTP | Yes | Yes | +91, 10 digits, 6-digit OTP by SMS, valid 5 min, resend after 30 s, max 5 attempts |
| OAuth (Google; Microsoft optional) | Yes | Yes | First OAuth login asks for shop name and mobile number to finish sign-up |
| Reset password link | Yes | n/a | Emailed single-use link valid 30 min; phone-only accounts reset by OTP |

- **Sign in screen:** split layout as in the website spec; tabs **Email** and **Phone**; divider "or"; **Continue with Google**; link to Sign up
- **Sign up fields:** owner name, shop name (becomes the tenant name), mobile, email, password and confirm password; OAuth skips the password. Mobile is verified by OTP and email by a link. The same email or phone from another method links to the existing account after verification
- **Forgot password:** always show "If an account exists, we sent a link"; `/reset-password?token=...` sets a new password
- **Endpoints (placeholders):** POST `/api/auth/register`, `/login`, `/otp/send`, `/otp/verify`, `/forgot-password`, `/reset-password`, `/refresh`, `/logout`; GET `/api/auth/oauth/google` with callback at `/auth/callback`
- **Angular:** `AuthService` (signals), `authInterceptor` (credentials, 401 refresh), `authGuard` and `guestGuard`. Session in httpOnly, secure, SameSite cookies set by the backend; never localStorage
- **Security:** rate-limit login and OTP, CAPTCHA after repeated failures, lock OTP after 5 wrong tries, plain-language inline errors

## 3. App Shell: POS-Style UI/UX

After sign in the owner sees a point-of-sale style app: large controls, every area boxed by borders, brand on the left and shop name on the right.

```
+--------------------------------------------------------------+
| [logo] Ferti+            (search)        [Shop name] [Avatar] |  Top bar 64 px
+----------+---------------------------------------------------+
| Dashboard| Page title                    [Big action buttons] |  Page header 72 px
| New Sale +---------------------------------------------------+
| Products |                                                   |
| Stock    |   Content area: cards, tables, POS panes          |
| Farmers  |   (each block in its own bordered box)            |
| Khata    |                                                   |
| Bills    |                                                   |
| Settings |                                                   |
+----------+---------------------------------------------------+
| Online | Today: date | Cash drawer | Help                      |  Status bar 40 px
+--------------------------------------------------------------+
```

- **Top bar left:** Ferti+ logo and name. **Top bar right corner:** the shop (tenant) name in a bordered chip with a store icon and a Free plan badge, then the avatar menu (profile, language, sign out). Long names truncate with a tooltip. Tenant name comes from `GET /api/tenant/me`
- **Sidebar:** 240 px, collapsible to a 72 px icon-plus-label rail; off-canvas drawer on small screens
- **Borders:** 1.5 px solid #CBD5CE between top bar, sidebar, page header, content and status bar, and around every card, table and panel
- **Palette:** same tokens as the website (forest green #0B6B3A, lime #7BC043, soil brown #7A4E2D, gold #F2B632, cream #F7F7F2)

| Element | Minimum size and style |
| --- | --- |
| Primary action (Save, Bill, Pay) | 56 px high, 18 px bold, icon + label, solid green |
| Secondary button | 48 px high, 16 px, 1.5 px green outline, icon + label |
| Sidebar item | 56 px high, 24 px icon + 16 px label, never icon-only |
| Inputs and selects | 52 px high, 16 px, visible label above |
| Table row | 56 px high, sticky header, zebra rows |
| POS product tile | 120 x 96 px minimum with name, price, stock |

- Base font 16 px, no text below 14 px; no icon-only buttons; at least 8 px between tap targets
- Destructive actions (delete, void bill) are red outline buttons with a confirm dialog
- Tablet-first (1024 px landscape); also usable at 1440 px and 360 px; WCAG 2.1 AA
- Routes, all behind `authGuard` and lazy-loaded: `/app/dashboard`, `/app/pos`, `/app/products`, `/app/brands`, `/app/stock`, `/app/farmers`, `/app/khata`, `/app/bills`, `/app/seasons`, `/app/settings`

## 4. Dashboard

- Four large KPI cards: Today's sales, Cash in hand, Total credit outstanding, Low-stock items
- Large quick actions: **New Sale**, **Add Product**, **Add Farmer**, **Receive Payment**
- Three bordered panels: Recent bills, Low stock alerts, Dues this week

## 5. Brands, Categories and Products

The shop owner manages all master data; nothing is fixed by the system, but the app ships with starter suggestions.

### 5.1 Brands

- Create, edit, deactivate brands (name, logo optional, manufacturer, notes)
- Brand list shows product count; a brand with products cannot be deleted, only deactivated

### 5.2 Categories and product types

| Category | Typical products (examples, owner can add more) | Sold as |
| --- | --- | --- |
| Chemical fertilizer (solid) | Urea, DAP, MOP (potash), SSP, NPK 20-20-0-13, NPK 19-19-19, NPK 10-26-26, ammonium sulphate | kg, 5 kg, 10 kg, 25 kg, 50 kg bags |
| Liquid fertilizer and bio-stimulant | Nano urea, liquid NPK, seaweed extract, humic acid | ml, 250 ml, 500 ml, 1 L, 5 L, 20 L |
| Micronutrient | Zinc sulphate, boron, chelated mixes | 100 g, 500 g, 1 kg, 5 kg |
| Pesticide, insecticide, fungicide, herbicide | Liquid and powder formulations | ml, 100 ml, 250 ml, 500 ml, 1 L, 5 L; g, 100 g, 250 g, 1 kg |
| Seeds | Vegetable, paddy, cotton, maize seeds | 100 g, 250 g, 500 g, 1 kg, 5 kg, 10 kg packets or bags |
| Machinery and tools | Pumps, sprayers (hand, battery, power), nozzles, small tools | piece, set |

### 5.3 Product and pack (variant) model

A **product** (for example DAP) has one or more **packs**, each with its own size, price and stock. This allows the same product in 5 kg and 50 kg bags.

| Product field | Rule |
| --- | --- |
| Name, brand, category | Required; brand chosen from the shop's brands |
| Type | Solid, Liquid or Item (decides allowed units) |
| Composition / grade | Free text, such as "18-46-0" or "20-20-0-13" |
| HSN code, GST % | Optional; default GST by category editable in Settings |
| Base unit | Solid = kg, Liquid = litre, Item = piece; stock is kept in the base unit |
| Low-stock level | In base units; triggers dashboard alert |

| Pack field | Rule |
| --- | --- |
| Pack label | Auto, e.g. "50 kg bag", "500 ml bottle"; owner can override |
| Pack size and unit | Number + unit (g, kg, bag, ml, L, piece); converted to base unit (500 ml = 0.5 L) |
| MRP | Required, per pack |
| Selling (cash) price | Optional; defaults to MRP, can be lower |
| Credit price | Optional; defaults to selling price |
| Barcode / SKU | Optional, scannable in POS |
| Batch number, manufacture and expiry date | Optional per stock receipt; expiry alerts 30 days ahead |
| Loose sale allowed | Yes or No; if Yes the owner can bill part of a pack (for example 3 kg from a 50 kg bag) at price per base unit |

- Product list: big search, filter by category, brand, low stock, active status; columns show name, brand, packs, stock, price
- Add product form is one screen with a repeatable "Packs" section and large **Add another pack** button
- Duplicate check on brand + name + pack size

## 6. Stock

- **Stock in** (purchase from supplier): product, pack, quantity, cost price, batch, expiry, supplier name, date. Increases stock
- **Stock out:** every bill reduces stock automatically; manual adjustment for damage or loss with a reason
- Stock is shown in packs and in base units (for example 40 bags = 2,000 kg); negative stock is blocked unless the owner confirms
- Stock ledger per product: date, type (in, sale, adjustment, return), quantity, balance

## 7. Farmers (Customers)

- Fields: name, mobile (unique within the shop), village, address, land size (optional), notes (optional), opening balance (amount the farmer already owes or has advanced), credit limit (optional), photo (optional)
- Farmer list shows name, village, mobile, outstanding balance, last bill date; filter "has dues", "overdue"
- Farmer profile has tabs: Summary, Bills, Khata, Payments
- A walk-in customer option exists for quick cash sales with no farmer record

## 8. Seasons and Pricing Rules

Prices and interest differ by season and festival, so the owner defines **seasons** (for example Kharif 2026, Rabi 2026, Diwali offer).

| Season field | Meaning |
| --- | --- |
| Name | Kharif 2026 |
| Start and end date | Window in which the season applies |
| Default cash discount | % or ₹ per bill or per item, applied when the farmer pays on the spot |
| Default credit interest | % per month on the credit amount (for example 1 = ₹1 per month per ₹100) |
| Default credit due date | Normally the season end date |
| Grace days | Days after the due date before late interest starts (optional) |
| Late interest rate | % per month after the due date (optional; defaults to the credit rate) |

All defaults are suggestions. On every bill the owner can change the discount, interest rate and due date **case by case**.

## 9. Billing and Calculations

### 9.1 Bill fields

Bill number (auto, per shop), date, farmer (or walk-in), season, line items (product, pack, quantity, unit price, line total), payment type, discount, interest rate, due date, notes, created by.

### 9.2 Payment types

1. **Paid on the spot (cash, UPI, card):** price = MRP (or the selling price) minus discount
2. **Credit (khata):** the farmer pays later; the owner may add interest depending on how long the farmer takes
3. **Part payment:** part paid now, the balance goes to khata as credit

### 9.3 Formulas

Let **Subtotal** = sum of (quantity × unit price) over all lines, where unit price is the MRP or the owner's selling price.

- **Spot bill:** Discount = fixed ₹ amount or Subtotal × discount %. Total payable = Subtotal − Discount
- **Credit bill:** Interest = Subtotal × (rate % per month ÷ 100) × months. Total payable at the due date = Subtotal + Interest
- **Months** = number of months agreed with the farmer (the owner can type it), or if a due date is chosen, days from bill date to due date ÷ 30, rounded to 1 decimal place
- **Simple interest only** by default; compound interest is not used
- **Late interest** (optional): after due date plus grace days, interest continues at the late rate on the unpaid principal until paid
- **Part payment:** Credit amount = Total − amount paid now; interest is calculated on the credit amount only
- **GST:** prices are treated as tax-inclusive by default; the invoice prints the tax split (taxable value, CGST, SGST). A shop setting can switch to tax-exclusive
- Round totals to the nearest ₹1 and show the rounding line on the invoice

### 9.4 Worked examples

Bill value (Subtotal) is ₹1,000 in each case.

| Case | Setting | Calculation | Farmer pays |
| --- | --- | --- | --- |
| Spot, 5% discount | Discount ₹50 | 1,000 − 50 | ₹950 |
| Credit, 1 month | 1% per month (₹1 per ₹100) | 1,000 + (1,000 × 1% × 1 = 10) | ₹1,010 |
| Credit, 6 months, until season end | 1% per month | 1,000 + (1,000 × 1% × 6 = 60) | ₹1,060 |
| Credit, owner offers lower rate | 0.5% per month, 6 months | 1,000 + 30 | ₹1,030 |
| Part payment | ₹400 paid now, ₹600 on credit, 1% per month, 4 months | 600 + (600 × 1% × 4 = 24) | ₹400 now and ₹624 later |

### 9.5 Bill screen behaviour

- As the owner changes payment type, discount, rate or months, the totals panel updates live and shows each line: Subtotal, Discount or Interest, GST info, Total, Paid now, Balance, Due date
- A clear label on credit bills: "Interest: 1% per month for 6 months = ₹60"
- The owner can edit the interest rate and discount only before saving; edits afterwards create a revision entry with the reason
- Print and share: A4 and 80 mm thermal formats, PDF download, WhatsApp share; invoice shows shop name, GSTIN, farmer, items with pack sizes, totals and the credit terms
- Bill actions: Save and print, Save only, Hold (park the bill), Cancel (void with reason)

## 10. Khata (Farmer Ledger)

The khata is an account book per farmer. Every movement of money is an entry with a running balance.

| Entry type | Direction | Created by |
| --- | --- | --- |
| Credit sale (amount owed) | Out: farmer owes more (debit) | Credit or part-payment bill |
| Interest charge | Out: farmer owes more (debit) | Credit bill interest or late interest |
| Payment received | In: farmer owes less (credit) | **Receive Payment** screen or bill payment |
| Discount or write-off | In: reduces dues | Owner action with reason |
| Return | In: reduces dues | Sales return |
| Opening balance | Either | Set when adding the farmer |

- **Receive Payment:** farmer, amount, mode (cash, UPI, bank), date, note. Payment is allocated to the oldest unpaid bill first (FIFO) unless the owner picks a bill. Interest already added to a bill is paid before principal
- **Ledger view:** date, description, bill number, debit (out), credit (in), balance; filter by date, season, bill; export PDF or Excel; share by WhatsApp
- **Dues list:** all farmers with outstanding balance, overdue days, last payment date; large **Receive Payment** and **Send Reminder** buttons
- **Overdue:** a bill is overdue after its due date plus grace days; shown in red with days overdue
- Entries are never deleted; a correction is a reversing entry
- Shop-level cashbook: daily total of money in (cash, UPI) and out (supplier payments, expenses)

## 11. Data Model (Reference)

| Entity | Key fields |
| --- | --- |
| Tenant (shop) | id, name, GSTIN, address, phone, plan |
| User (owner) | id, tenantId, name, email, phone, authProviders |
| Brand | id, tenantId, name, logo, active |
| Category | id, tenantId, name, productType |
| Product | id, tenantId, brandId, categoryId, name, grade, hsn, gstPercent, baseUnit, lowStockLevel, active |
| Pack | id, productId, label, size, unit, sizeInBaseUnit, mrp, cashPrice, creditPrice, barcode, looseAllowed |
| StockLot | id, packId, batchNo, expiryDate, qtyBase, costPrice, supplier, receivedAt |
| Farmer | id, tenantId, name, mobile, village, address, creditLimit, openingBalance |
| Season | id, tenantId, name, startDate, endDate, cashDiscount, creditInterestPct, dueDate, graceDays, lateInterestPct |
| Bill | id, tenantId, number, date, farmerId, seasonId, paymentType, subtotal, discount, interestPct, months, interestAmount, total, paidNow, balance, dueDate, status |
| BillItem | id, billId, packId, qty, unitPrice, lineTotal |
| KhataEntry | id, tenantId, farmerId, billId, type, direction, amount, balanceAfter, date, note |
| Payment | id, farmerId, amount, mode, date, allocations |

All rows carry `tenantId`; the backend scopes every query by it, and the frontend never sends an editable tenant id.

## 12. Angular Structure

```
src/app/
  core/ (auth.service, auth.interceptor, guards, tenant.service, api.service)
  app-shell/ (shell, topbar, sidebar, status-bar)
  features/
    dashboard/ pos/ brands/ products/ stock/ farmers/ khata/ bills/ seasons/ settings/
  shared/ (big-button, bordered-card, money-pipe, unit-pipe, confirm-dialog, bill-totals)
  models/ (brand, product, pack, farmer, bill, khata-entry, season)
  utils/ interest.util.ts (pure functions for spot discount and credit interest, unit tests)
```

Put all money formulas in pure, unit-tested functions (`calcSpotTotal`, `calcCreditTotal`, `monthsBetween`, `allocatePayment`).

## 13. Acceptance Criteria

1. Brand name Ferti+ is top-left and the shop name is top-right on every `/app` page; every layer and card has a visible border.
2. No interactive control is under 48 px high; primary actions are 56 px; no icon-only buttons.
3. The owner can add, edit and deactivate brands, categories and products, with several packs per product (for example Urea in 5 kg and 50 kg bags, a liquid in 500 ml and 5 L).
4. Stock in and sale reduce and increase stock correctly in base units, including loose sales.
5. A ₹1,000 spot bill with ₹50 discount totals ₹950; a ₹1,000 credit bill at 1% per month for 6 months totals ₹1,060; both match section 9.4.
6. Discount, interest rate, months and due date can be changed per bill before saving.
7. Every credit bill creates a khata entry; payments reduce the balance and the ledger shows a correct running balance.
8. Dues list shows overdue farmers; ledger exports to PDF.
9. All `/app` routes redirect to `/signin` when signed out; sign in works with email, phone OTP and Google (mocked).
10. Unit tests cover all formulas in section 9.3.

## 14. Ready-to-Paste Prompt for GitHub Copilot

Attach this document and the sign-in prototype screenshot.

```
You are a senior Angular engineer. Build the Ferti+ shop owner application exactly as described in the attached specification. Stack: Angular (latest stable, standalone components, Angular CLI, TypeScript), Angular Router with lazy-loaded routes, Bootstrap 5.3 (SCSS) + ng-bootstrap, Bootstrap Icons, Angular Reactive Forms. Do not use React.

Only fertilizer shop owners log in (email+password, phone OTP, Google OAuth, reset link). After login show a POS-style shell: Ferti+ brand top-left, shop (tenant) name chip top-right, collapsible sidebar, status bar, 1.5px borders (#CBD5CE) between every layer and card, buttons at least 48px (primary 56px), no icon-only buttons.

Features: brands, categories, products with multiple packs (solids in kg and bags such as Urea, DAP, NPK 20-20-0-13; liquids in ml and litres such as 500 ml, 5 L), stock in/out with batch and expiry, farmers, seasons, billing and khata ledger.

Billing rules: spot payment = subtotal minus discount (example 1000 -> 950). Credit = subtotal + simple interest, interest = subtotal x rate% per month x months (1% per month for 6 months on 1000 = 60). Owner can change discount, rate, months and due date per bill. Part payments charge interest only on the credit portion. Payments are allocated FIFO. Put formulas in pure functions in utils/interest.util.ts with unit tests.

Use mock data and placeholder services. Work step by step: 1) scaffold and design tokens, 2) auth screens, 3) app shell, 4) brands and products, 5) stock, 6) farmers, 7) seasons, 8) billing and POS, 9) khata, 10) tests and README. Run and fix errors after each step.
```
