import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Waits for session restore, so a page reload does not log the user out. */
export const authGuard: CanActivateFn = async (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (await auth.restoreSession()) return true;
  return router.createUrlTree(['/signin'], { queryParams: { returnUrl: state.url } });
};

export const guestGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return (await auth.restoreSession()) ? router.createUrlTree(['/app/dashboard']) : true;
};

/** Example: { path: 'staff', canActivate: [authGuard, roleGuard('TENANT')] } */
export const roleGuard = (...allowed: string[]): CanActivateFn => () => {
  const role = inject(AuthService).role();
  return role && allowed.includes(role) ? true : inject(Router).createUrlTree(['/app/dashboard']);
};