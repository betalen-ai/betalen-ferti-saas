import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { TokenStore } from './token-store';

const PUBLIC_PATHS = [
  '/auth/login', '/auth/register', '/auth/refresh', '/auth/otp/',
  '/auth/google', '/auth/forgot-password', '/auth/reset-password',
];

const withToken = (req: HttpRequest<unknown>, token: string | null) =>
  token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const tokens = inject(TokenStore);
  const isPublic = PUBLIC_PATHS.some(p => request.url.includes(p));

  const outgoing = request.clone({ withCredentials: request.url.includes('/auth/') });
  const sent = isPublic ? outgoing : withToken(outgoing, tokens.accessToken);

  return next(sent).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401 || isPublic) {
        return throwError(() => error);
      }
      if (!tokens.refreshToken) {
        auth.clearSession();
        return throwError(() => error);
      }
      // Refresh once (shared by parallel requests), then retry with the NEW token.
      return auth.refreshAccessToken().pipe(
        catchError(() => {
          auth.clearSession();
          return throwError(() => error);
        }),
        switchMap(newToken => next(withToken(outgoing, newToken))),
      );
    }),
  );
};