import { HttpBackend, HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { environment } from '../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const authenticatedRequest = request.clone({ withCredentials: true });
  const rawHttp = new HttpClient(inject(HttpBackend));

  return next(authenticatedRequest).pipe(catchError((error: unknown) => {
    if (!(error instanceof HttpErrorResponse) || error.status !== 401 || request.url.includes('/auth/refresh')) {
      return throwError(() => error);
    }

    return rawHttp.post(`${environment.apiBaseUrl}/auth/refresh`, {}, { withCredentials: true }).pipe(
      switchMap(() => next(authenticatedRequest)),
      catchError(() => throwError(() => error))
    );
  }));
};
