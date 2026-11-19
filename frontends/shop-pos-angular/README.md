# Ferti+ Corporate Website

Responsive Angular marketing and authentication website for Ferti+, a free shop-management app for fertilizer retailers.

## Routes

- `/` Home
- `/about` About
- `/products` Products
- `/pricing` Pricing
- `/contact` Contact
- `/signin` Sign in
- `/signup` Sign up
- `/forgot-password` Forgot password

## Development server

From this directory, run `npm install` and `npm start`. Navigate to `http://localhost:4200/`.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `npm run build`. The production build is written to `dist/shop-pos`.

## Environment variables

Set the API base URL in `src/environments/environment.ts` for development and `src/environments/environment.prod.ts` for production. Auth and contact submissions currently use placeholder UI loading states and can be connected to:

- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/forgot-password`
- `POST /api/contact`

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.
