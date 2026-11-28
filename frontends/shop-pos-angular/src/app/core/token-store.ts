import { Injectable } from '@angular/core';

/** Access token: memory only. Refresh token: sessionStorage until the backend
 *  sets an httpOnly cookie (spec 10). Never localStorage. */
@Injectable({ providedIn: 'root' })
export class TokenStore {
  private access: string | null = null;
  private readonly key = 'ferti_rt';

  get accessToken(): string | null { return this.access; }
  get refreshToken(): string | null { return sessionStorage.getItem(this.key); }

  set(access: string, refresh?: string | null): void {
    this.access = access;
    if (refresh) sessionStorage.setItem(this.key, refresh);
  }

  clear(): void {
    this.access = null;
    sessionStorage.removeItem(this.key);
  }
}