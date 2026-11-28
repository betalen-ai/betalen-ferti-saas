# Ferti+ Shop Owner Application

Responsive Angular marketing website and POS-style shop-owner application for Ferti+, a free shop-management app for fertilizer retailers. Shop features use tenant-scoped mock data in Angular; backend and database implementation are out of scope.

## Routes

- `/` Home
- `/about` About
- `/products` Products
- `/pricing` Pricing
- `/contact` Contact
- `/signin` Sign in
- `/signup` Sign up
- `/forgot-password` Forgot password
- `/reset-password?token=...` Reset password
- `/app/dashboard` through `/app/settings` Protected shop-owner application (dashboard, POS, products, brands, stock, farmers, khata, bills, seasons, settings)

## Demo authentication and data

- Email sign-in accepts any valid email and a password of at least 8 characters.
- Phone OTP is simulated with code `123456`; resend is enabled after 30 seconds, codes expire after 5 minutes, and verification stops after 5 failed attempts.
- Google sign-in and email recovery are simulated. Google first-time setup asks for shop name and mobile number.
- Authentication state and shop data are in memory and reset on reload. `AuthService`, `TenantService`, and `ShopDataService` are mock implementations intended to be connected to the specified API endpoints and secure backend cookies.
- Stock, sales, farmers, seasons, and ledger changes are maintained in the browser session only.

## Development server

From this directory, run `npm install` and `npm start`. Navigate to `http://localhost:4200/`.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `npm run build`. The production build is written to `dist/shop-pos`.

## Environment variables

Set the API base URL in `src/environments/environment.ts` for development and `src/environments/environment.prod.ts` for production. The credential interceptor sends cookies and attempts one refresh on a 401 response. Replace the mock auth and shop data services with API implementations for:

- `POST /api/auth/register`, `/login`, `/otp/send`, `/otp/verify`, `/forgot-password`, `/reset-password`, `/refresh`, and `/logout`
- `GET /api/tenant/me`
- Feature APIs for products, stock, farmers, seasons, bills and khata
- `POST /api/contact`

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.
