import { Injectable } from '@angular/core';

/** Access token: memory only. Refresh token: sessionStorage (also sent by the
 *  backend as an httpOnly cookie). `hasSession` is a non-secret marker so the
 *  app knows it should try to restore the session after a reload. */
@Injectable({ providedIn: 'root' })
export class TokenStore {
  private access: string | null = null;
  private readonly key = 'ferti_rt';
  private readonly flagKey = 'ferti_has_session';

  get accessToken(): string | null { return this.access; }

  get refreshToken(): string | null {
    try { return sessionStorage.getItem(this.key); } catch { return null; }
  }

  get hasSession(): boolean {
    try { return localStorage.getItem(this.flagKey) === '1'; } catch { return false; }
  }

  set(access: string, refresh?: string | null): void {
    this.access = access;
    try {
      if (refresh) sessionStorage.setItem(this.key, refresh);
      localStorage.setItem(this.flagKey, '1');
    } catch { /* storage blocked */ }
  }

  clear(): void {
    this.access = null;
    try {
      sessionStorage.removeItem(this.key);
      localStorage.removeItem(this.flagKey);
    } catch { /* ignore */ }
  }
}