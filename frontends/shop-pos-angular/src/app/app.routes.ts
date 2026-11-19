import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/auth.guards';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent) },
  { path: 'about', loadComponent: () => import('./pages/about/about.component').then(m => m.AboutComponent) },
  { path: 'products', loadComponent: () => import('./pages/products/products.component').then(m => m.ProductsComponent) },
  { path: 'pricing', loadComponent: () => import('./pages/pricing/pricing.component').then(m => m.PricingComponent) },
  { path: 'contact', loadComponent: () => import('./pages/contact/contact.component').then(m => m.ContactComponent) },
  { path: 'signin', canActivate: [guestGuard], loadComponent: () => import('./pages/signin/signin.component').then(m => m.SigninComponent) },
  { path: 'signup', canActivate: [guestGuard], loadComponent: () => import('./pages/signup/signup.component').then(m => m.SignupComponent) },
  { path: 'forgot-password', canActivate: [guestGuard], loadComponent: () => import('./pages/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent) },
  { path: 'reset-password', canActivate: [guestGuard], loadComponent: () => import('./pages/reset-password/reset-password.component').then(m => m.ResetPasswordComponent) },
  { path: 'auth/callback', loadComponent: () => import('./pages/auth-callback/auth-callback.component').then(m => m.AuthCallbackComponent) },
  {
    path: 'app',
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    loadComponent: () => import('./app-shell/app-shell.component').then(m => m.AppShellComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', data: { page: 'dashboard' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'pos', data: { page: 'pos' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'products', data: { page: 'products' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'brands', data: { page: 'brands' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'stock', data: { page: 'stock' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'farmers', data: { page: 'farmers' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'khata', data: { page: 'khata' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'bills', data: { page: 'bills' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'seasons', data: { page: 'seasons' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) },
      { path: 'settings', data: { page: 'settings' }, loadComponent: () => import('./features/app-feature.component').then(m => m.AppFeatureComponent) }
    ]
  },
  { path: '**', loadComponent: () => import('./pages/not-found/not-found.component').then(m => m.NotFoundComponent) }
];
