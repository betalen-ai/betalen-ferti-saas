# Ferti+ Corporate Website: Build Specification

Prepared for: GitHub Copilot (agent / chat mode) Product: Ferti+ (free business management app for fertilizer shops) Deliverable: Responsive, modern corporate marketing website with Sign in / Sign up screens

## 1. Product Context

Ferti+ is a web application where fertilizer shop owners sign up for free and run their daily business: inventory, sales, credit and cash ledgers, and farmer records. Shop owners sell fertilizers, seeds, pesticides and small machinery (pumps, sprayers, etc.) to farmers, on both cash and credit.

This project covers only the corporate website (public marketing site + auth screens). The business application (dashboard, inventory, etc.) is built separately. Auth pages here must be UI-complete and wired to placeholder API endpoints. Sign in and Sign up are for fertilizer shop owners only; the site has no other login or application.

**Target users:** Fertilizer and agri-input shop owners in India (many on mobile, some on slow networks). Only fertilizer shop owners sign up and sign in. There are no other user roles (no farmer, admin or distributor logins).

**Tone:** Trustworthy, simple, practical, modern. Plain language, no jargon.

## 2. Tech Stack

- Angular (latest stable, standalone components, Angular CLI, TypeScript) + Angular Router with lazy-loaded routes
- Bootstrap 5.3 (via SCSS import, customized with design tokens) + ng-bootstrap for navbar, carousel, accordion, modal
- Bootstrap Icons for icons
- Google Fonts: **Space Grotesk** (headings) and **Inter** (body)
- Angular Reactive Forms with built-in and custom validators for form validation
- AOS or Angular animations for subtle scroll animations
- Angular Title and Meta services for per-page SEO tags
- ESLint + Prettier

If the team prefers no framework, the same spec can be built in plain HTML + Bootstrap 5 + vanilla JS with shared header/footer partials.

## 3. Design System

### 3.1 Color palette (fertilizer / agriculture theme)

Define as SCSS variables and override Bootstrap's `$primary`, etc.

| Token | Hex | Usage |
| --- | --- | --- |
| Primary (Forest Green) | #0B6B3A | Buttons, links, brand |
| Primary Dark | #084D2A | Hover, footer |
| Accent (Leaf Lime) | #7BC043 | Highlights, icons, badges |
| Soil Brown | #7A4E2D | Secondary accents, machinery section |
| Harvest Gold | #F2B632 | CTA highlights, pricing badge |
| Sky Tint | #E8F1FB | Input autofill, info blocks |
| Background (Cream) | #F7F7F2 | Page background |
| Surface | #FFFFFF | Cards |
| Text Dark | #14211A | Headings, body |
| Text Muted | #5C6B62 | Secondary text |

### 3.2 Typography and shape

- H1 48/56 px desktop, 32/40 mobile; H2 36/44; H3 24/32; body 16/26
- Small uppercase eyebrow labels above headings (letter-spacing 0.12em, primary color, 12 px), like "WELCOME BACK" in the prototype
- Border radius: 10 px inputs/buttons, 16 px cards
- Soft shadows, generous whitespace, 1200 px max content width
- Primary button: solid forest green, white text, arrow icon on the right (as in the prototype's "Sign in →")
- Inputs: 48 px height, 1 px light border, green focus ring

### 3.3 Brand logo (left side of navbar)

- Rounded-square green icon with a white sprout/leaf glyph, followed by wordmark **Ferti+** and a small tagline "Smart shop manager" below (same pattern as the prototype's "Betalen / Ferti backoffice")
- Provide as an inline SVG component `<Logo variant="light|dark" />`

## 4. Site Map and Routes

| Route | Page |
| --- | --- |
| `/` | Home |
| `/about` | About |
| `/products` | Products (features / modules of Ferti+) |
| `/pricing` | Pricing |
| `/contact` | Contact |
| `/signin` | Sign in |
| `/signup` | Sign up |
| `/forgot-password` | Forgot password |
| `*` | 404 page |

## 5. Global Layout

### 5.1 Navbar (sticky, responsive)

- Left: Ferti+ logo (links to `/`)
- Center/right menu: **Home, About, Products, Pricing, Contact**
- Far right: **Sign in** (outline button) and **Sign up free** (solid green button)
- Transparent over hero at top; becomes white with shadow after 40 px scroll
- Collapses to a hamburger at under 992 px (Bootstrap `lg`) with an off-canvas menu; auth buttons shown inside it
- Active link underline in accent lime

### 5.2 Footer

- Dark green background (#084D2A), 4 columns: brand + short blurb, Quick Links, Products, Contact (address, phone, email)
- Social icons, newsletter email field, bottom bar with copyright "© 2026 Ferti+. All rights reserved.", Privacy Policy and Terms links

## 6. Page Specifications

### 6.1 Home (`/`)

1. **Hero carousel** (Bootstrap carousel, full width, 70-80 vh, auto-play 6 s, pause on hover, swipe on mobile, indicators and arrows). Each slide: background agri image with dark green gradient overlay, eyebrow, H1, sub-text, two CTAs (Sign up free, See how it works). Suggested slides:
   - "Run your fertilizer shop smarter, for free." Inventory, sales and credit in one place.
   - "Know your stock. Never run out in season." Real-time inventory for fertilizers, seeds and pesticides.
   - "Keep every farmer's credit on track." Digital khata with due dates and reminders.
   - "From pumps to sprayers, manage it all." Machinery and equipment tracking.
2. **Trust strip:** "Free forever for shop owners", "Works on mobile and desktop", "Made for Indian agri retailers"
3. **What you can do** (6 feature cards, icon + title + 1-line text): Inventory management, Seeds and pesticides catalog, Machinery (pumps, sprayers), Cash and credit sales, Farmer ledger (khata), Reports and GST-ready invoices
4. **How it works** (3 steps): Create free account, Add your products, Start selling and tracking
5. **Product showcase:** tabbed section (Fertilizers / Seeds / Machinery / Credit) with a dashboard mockup image per tab
6. **Stats counters:** animated numbers (placeholders: 500+ shops, 25,000+ farmers, 1 lakh+ invoices)
7. **Testimonials:** carousel of 3 shop-owner quotes (placeholder data)
8. **FAQ accordion** (5 to 6 questions: Is it really free? Can I use it on phone? Can I track credit? etc.)
9. **Final CTA banner:** "Start managing your shop today" with Sign up free button

### 6.2 About (`/about`)

- Page header banner with breadcrumb
- Our story / mission: help agri-input retailers go digital and stay profitable
- Vision, values (Trust, Simplicity, Farmer-first, Transparency) as icon cards
- Timeline or milestones
- Team grid (4 placeholder members)
- CTA banner

### 6.3 Products (`/products`)

Present Ferti+ modules, each as an alternating image/text section with bullet list:

- **Inventory Manager:** stock in/out, batch and expiry, low-stock alerts, multiple units (kg, bag, litre)
- **Fertilizers and Pesticides:** categories, HSN, MRP vs selling price
- **Seeds:** variety, season, germination and expiry tracking
- **Machinery and Equipment:** pumps, sprayers, small tools; warranty and serial numbers
- **Sales and Billing:** cash and credit invoices, print and share via WhatsApp
- **Credit and Farmer Ledger:** outstanding amounts, due dates, payment history, reminders
- **Reports:** daily sales, stock valuation, profit, dues

End with a feature comparison snapshot and CTA.

### 6.4 Pricing (`/pricing`)

- Headline: "Free for every shop owner."
- Monthly/Yearly toggle (UI only)
- 3 cards: **Starter (Free, highlighted, "Most popular")**: 1 shop, unlimited products, unlimited billing, basic reports. **Growth (Coming soon)**: multi-user, advanced reports, SMS/WhatsApp reminders. **Enterprise (Contact us)**: multi-branch, API access, dedicated support.
- Feature comparison table (responsive horizontal scroll on mobile)
- Pricing FAQ and CTA

Prices in INR (₹); Starter is ₹0.

### 6.5 Contact (`/contact`)

- Two-column layout: contact form (name, mobile, email, subject, message, submit) and info card (address, phone, email, working hours) with an embedded map placeholder
- Form validation with inline errors and a success toast
- POST to `/api/contact` (placeholder)

### 6.6 Sign in (`/signin`): follow the prototype

Split-screen layout (50/50 on desktop, form only on mobile with a smaller image banner on top):

- **Left panel:** full-height greenhouse/farm photo with dark gradient overlay. Top-left: logo. Bottom-left: eyebrow "FERTI+", headline "Growing better, together.", sub-text "A clearer view of your stock, farmers, and business behind every growing season."
- **Right panel** (cream background, form vertically centered, max width 430 px):
  - Eyebrow "WELCOME BACK"
  - H2 "Shop owner sign in"
  - Sub-text "Sign in with your shop owner account to continue."
  - Email address field
  - Password field with show/hide toggle, "Forgot password?" link aligned right of the label
  - Remember me checkbox
  - Full-width **Sign in →** button with loading spinner state
  - Divider "or", then "Continue with Google" button
  - Footer text: "New to Ferti+? Create a free account" linking to `/signup`
- Validation: email format, password required; show server error alert above the form
- POST `/api/auth/login` (placeholder; store token in memory/httpOnly cookie via backend, never in localStorage in production)

### 6.7 Sign up (`/signup`)

Same split layout. Left headline: "Your shop, digitised in minutes." Form fields:

- Owner full name, Shop name, Mobile number (10-digit Indian format), Email
- State and District (dropdowns), optional GSTIN
- Password and Confirm password (strength meter)
- Checkbox: "I agree to the Terms and Privacy Policy"
- Button: **Create free account →**
- Link: "Already have an account? Sign in"
- POST `/api/auth/register` (placeholder); on success redirect to `/signin` with a success message

### 6.8 Forgot password (`/forgot-password`)

Same split layout; single email field, "Send reset link" button, back-to-sign-in link. POST `/api/auth/forgot-password`.

## 7. Non-Functional Requirements

- **Responsive:** mobile-first; test at 360, 768, 992, 1200, 1440 px
- **Performance:** Lighthouse 90+ on Performance, Accessibility, Best Practices, SEO; lazy-load images, WebP, code-split routes
- **Accessibility:** WCAG 2.1 AA, semantic HTML, labels for all inputs, visible focus, keyboard-navigable carousel and menu, alt text, color contrast checked
- **SEO:** unique title and meta description per page, Open Graph tags, sitemap.xml, robots.txt, JSON-LD Organization schema
- **Security:** client and server validation, no secrets in the repo, `environment.ts` for API base URL (`apiBaseUrl in src/environments`)
- **Browser support:** latest Chrome, Edge, Firefox, Safari, and Android Chrome
- **Content:** English first; structure copy in a `content/` folder so Telugu and Hindi can be added later (i18n-ready with ngx-translate)

## 8. Suggested Folder Structure

```
ferti-plus-web/
  src/
    assets/ (images, logo svg)
    environments/ (environment.ts, environment.prod.ts)
    styles/ (_variables.scss, _custom.scss, styles.scss)
    app/
      core/ (services: api.service.ts, auth.service.ts; interceptors; guards)
      layout/ (navbar, footer, auth-layout)
      shared/ (logo, feature-card, pricing-card, faq, testimonials, stats-counter, password-input)
      pages/ (home, about, products, pricing, contact, signin, signup, forgot-password, not-found)
      content/ (copy and data in TS/JSON)
      app.routes.ts, app.config.ts, app.component.ts
    index.html, main.ts
  angular.json
  README.md
```

## 9. Acceptance Criteria

1. All routes in section 4 render without console errors and work with browser back/forward.
2. Navbar and footer are consistent across pages; hamburger menu works on mobile.
3. Home hero carousel has 4 slides, autoplay, swipe, indicators.
4. Sign in page visually matches the prototype layout (split screen, logo top-left, headline bottom-left, form on the right) using the Ferti+ branding and palette.
5. All forms validate and show inline errors; submit buttons show loading state.
6. Color palette and fonts come only from design tokens (no hard-coded hex values in components).
7. Lighthouse scores meet section 7 targets.
8. README explains setup (`npm install`, `ng serve`, `ng build`) and env variables.

## 10. Ready-to-Paste Prompt for GitHub Copilot

Copy everything in the box below into Copilot Chat (Agent mode), and attach the prototype screenshot and this document.

```
You are a senior front-end engineer. Build the "Ferti+" corporate website exactly as described in the attached specification document.

Stack: Angular (latest stable, standalone components, Angular CLI, TypeScript), Angular Router with lazy-loaded routes, Bootstrap 5.3 (SCSS, customised tokens) + ng-bootstrap, Bootstrap Icons, Angular Reactive Forms, AOS/Angular animations, Title and Meta services for SEO. Do not use React.

Product: Ferti+ is a free web app where fertilizer shop owners manage inventory (fertilizers, seeds, pesticides, small machinery like pumps and sprayers) and sell to farmers on cash and credit.

Routes: /, /about, /products, /pricing, /contact, /signin, /signup, /forgot-password, 404. Only fertilizer shop owners can sign up or sign in; build no other user roles, logins or portals (no farmer, admin or distributor).
Navbar: Ferti+ logo on the left; menu Home, About, Products, Pricing, Contact; right side Sign in and Sign up free buttons; sticky, collapses to off-canvas on mobile.
Home: 4-slide Bootstrap carousel hero, trust strip, 6 feature cards, how-it-works, tabbed product showcase, stats, testimonials, FAQ, CTA banner.
Sign in / Sign up: split-screen layout like the attached prototype (left photo with overlay, logo top-left, headline bottom-left; right cream panel with form).
Colors: Forest green #0B6B3A, dark green #084D2A, leaf lime #7BC043, soil brown #7A4E2D, harvest gold #F2B632, cream background #F7F7F2, text #14211A. Fonts: Space Grotesk (headings), Inter (body).

Requirements: mobile-first, WCAG AA, Lighthouse 90+, SEO meta per page, placeholder API calls via an injectable ApiService (HttpClient) using apiBaseUrl from src/environments, reusable components, content kept in src/content.

Work step by step: 1) scaffold project and design tokens, 2) Logo, Navbar, Footer, layout, 3) Home page, 4) other public pages, 5) auth pages, 6) SEO, accessibility and performance pass, 7) README. After each step, run the app and fix errors before continuing.
```

## 11. Notes and Next Steps

- Replace placeholder photos with licensed or own agri images (greenhouse, crop field, shop counter). Keep each under 200 KB.
- Placeholder stats and testimonials must be replaced with real data before launch.
- After the website is done, the next phase is the authenticated application: dashboard, inventory, billing, credit ledger, and reports.
