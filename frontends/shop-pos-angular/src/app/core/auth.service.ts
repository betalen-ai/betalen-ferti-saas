import { Injectable, inject, signal } from '@angular/core';
import { HttpBackend, HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, finalize, firstValueFrom, map, shareReplay, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { ApiService } from './api.service';
import { TokenStore } from './token-store';
import { SubscriptionService } from './subscription.service';
import { TenantService } from './tenant.service';

const TERMS_VERSION = '2026-11-23';
const PASSWORD_RULE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
const PHONE_RULE = /^[6-9]\d{9}$/;

export type OtpPurpose = 'LOGIN' | 'REGISTER_VERIFY' | 'RESET_PASSWORD';

export interface OwnerProfile { name: string; email: string; phone: string; }

export interface ShopDetails {
  shopName: string;
  shopTypes: string[];              // fertilizers | pesticides | seeds | machinery
  addressLine?: string; villageTown?: string; mandalTaluk?: string;
  district?: string; state?: string; pincode?: string;
  gstin?: string; pan?: string; referralCode?: string; heardFrom?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
  expires_in: number;
  subscription_status?: string | null;
  subscription_days_left?: number | null;
}

/** Thrown by signInGoogle when the Google email has no account yet. */
export class RegistrationRequiredError extends Error {
  constructor(public prefill: { email: string; name: string }) {
    super('REGISTRATION_REQUIRED');
  }
}

const MESSAGES: Record<string, string> = {
  invalid_credentials: 'The shop, email or password is incorrect.',
  tenant_suspended: 'Your account is suspended. Please contact support.',
  tenant_closed: 'This account is closed.',
  OTP_INVALID: 'That code is not correct.',
  OTP_EXPIRED: 'That code has expired. Request a new one.',
  otp_rate_limited: 'Too many codes requested. Try again in an hour.',
  otp_resend_too_soon: 'Please wait 30 seconds before asking for another code.',
  EMAIL_EXISTS: 'An account with this email already exists.',
  PHONE_EXISTS: 'An account with this mobile number already exists.',
};

function decodeClaims(token: string): Record<string, any> {
  try {
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(part.padEnd(Math.ceil(part.length / 4) * 4, '=')));
  } catch { return {}; }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);
  private tokens = inject(TokenStore);
  private router = inject(Router);
  private subscription = inject(SubscriptionService);
  private tenant = inject(TenantService);
  /** Bypasses interceptors so refresh and logout can never loop. */
  private raw = new HttpClient(inject(HttpBackend));
  private base = environment.apiBaseUrl;

  readonly authenticated = signal(false);
  readonly profile = signal<OwnerProfile | null>(null);
  readonly role = signal<string | null>(null);

  private phoneVerifiedToken: string | null = null;
  private googleRegistrationToken: string | null = null;
  private refreshInFlight$: Observable<string> | null = null;

  // ---------------------------------------------------------------- sign in
  async signInEmail(email: string, password: string, tenantId?: string): Promise<void> {
    try {
      const r = await firstValueFrom(this.api.post<TokenResponse>('/auth/login', {
        tenant_id: tenantId || undefined,
        email: email.trim().toLowerCase(),
        password,
      }));
      this.startSession(r, { name: email.split('@')[0], email: email.trim().toLowerCase(), phone: '' });
    } catch (e) { throw this.apiError(e); }
  }

  /** Phone-OTP sign-in. Works once the backend returns tokens for purpose LOGIN. */
  async signInOtp(phone: string, otp: string): Promise<void> {
    this.assertPhone(phone); this.assertOtp(otp);
    try {
      const r = await firstValueFrom(this.api.post<any>('/auth/otp/verify',
        { phone: `+91${phone}`, otp, purpose: 'LOGIN' }));
      if (!r.access_token) throw new Error('Phone sign-in is not available yet. Use email and password.');
      this.startSession(r, { name: `Shop owner ${phone.slice(-4)}`, email: '', phone });
    } catch (e) { throw this.apiError(e); }
  }

  async signInGoogle(): Promise<void> {
    const credential = await this.getGoogleIdToken();
    try {
      const r = await firstValueFrom(this.api.post<any>('/auth/google', { credential }));
      if (r.status === 'registration_required') {
        this.googleRegistrationToken = r.registration_token ?? null;
        throw new RegistrationRequiredError({ email: r.email ?? '', name: r.name ?? '' });
      }
      this.startSession(r, { name: r.name ?? '', email: r.email ?? '', phone: '' });
    } catch (e) {
      if (e instanceof RegistrationRequiredError) throw e;
      throw this.apiError(e);
    }
  }

  // ------------------------------------------------------------------- OTP
  async sendOtp(phone: string, purpose: OtpPurpose = 'REGISTER_VERIFY'): Promise<void> {
    this.assertPhone(phone);
    try {
      await firstValueFrom(this.api.post('/auth/otp/send', { phone: `+91${phone}`, purpose }));
    } catch (e) { throw this.apiError(e); }
  }

  /** Verify the registration OTP and keep the 15-minute phone_verified_token. */
  async checkOtp(phone: string, otp: string): Promise<void> {
    this.assertPhone(phone); this.assertOtp(otp);
    try {
      const r = await firstValueFrom(this.api.post<any>('/auth/otp/verify',
        { phone: `+91${phone}`, otp, purpose: 'REGISTER_VERIFY' }));
      this.phoneVerifiedToken = r.phone_verified_token ?? null;
    } catch (e) { throw this.apiError(e); }
  }

  // ------------------------------------------------------------ registration
  /** Instant registration with a 6-month trial (spec 4.3). No approval step. */
  async register(profile: OwnerProfile, password: string, shop: ShopDetails, language = 'en'): Promise<void> {
    this.assertNewPassword(password);
    if (!profile.name.trim() || !profile.email.trim()) throw new Error('Enter your name and email.');
    if (!this.phoneVerifiedToken) throw new Error('Verify your mobile number first.');
    try {
      const r = await firstValueFrom(this.api.post<TokenResponse>('/auth/register', {
        full_name: profile.name.trim(),
        email: profile.email.trim().toLowerCase(),
        mobile: `+91${profile.phone}`,
        password,
        confirm_password: password,
        preferred_language: language,
        ...this.shopBody(shop),
        consent_terms_version: TERMS_VERSION,
        consent_at: new Date().toISOString(),
        phone_verified_token: this.phoneVerifiedToken,
      }));
      this.phoneVerifiedToken = null;
      this.startSession(r, profile);
    } catch (e) { throw this.apiError(e); }
  }

  /** Second step after signInGoogle threw RegistrationRequiredError. */
  async registerWithGoogle(phone: string, password: string, shop: ShopDetails, language = 'en'): Promise<void> {
    this.assertNewPassword(password);
    if (!this.googleRegistrationToken) throw new Error('Google registration expired. Start again.');
    if (!this.phoneVerifiedToken) throw new Error('Verify your mobile number first.');
    try {
      const r = await firstValueFrom(this.api.post<any>('/auth/google/register', {
        registration_token: this.googleRegistrationToken,
        mobile: `+91${phone}`,
        password,
        confirm_password: password,
        preferred_language: language,
        shop_name: shop.shopName,
        shop_types: shop.shopTypes,
        phone_verified_token: this.phoneVerifiedToken,
        consent_terms_version: TERMS_VERSION,
        consent_at: new Date().toISOString(),
      }));
      this.googleRegistrationToken = null;
      this.phoneVerifiedToken = null;
      this.startSession(r, { name: r.name ?? '', email: r.email ?? '', phone });
    } catch (e) { throw this.apiError(e); }
  }

  // --------------------------------------------------------------- password
  async requestPasswordReset(phone: string): Promise<void> {
    this.assertPhone(phone);
    try {
      await firstValueFrom(this.api.post('/auth/forgot-password', { phone: `+91${phone}` }));
    } catch (e) { throw this.apiError(e); }
  }

  async resetPassword(phone: string, otp: string, newPassword: string): Promise<void> {
    this.assertPhone(phone); this.assertOtp(otp); this.assertNewPassword(newPassword);
    try {
      await firstValueFrom(this.api.post('/auth/reset-password',
        { phone: `+91${phone}`, otp, new_password: newPassword }));
    } catch (e) { throw this.apiError(e); }
  }

  async changePassword(current: string, next: string): Promise<void> {
    this.assertNewPassword(next);
    try {
      await firstValueFrom(this.api.post('/auth/change-password',
        { current_password: current, new_password: next }));
    } catch (e) { throw this.apiError(e); }
  }

  // ---------------------------------------------------------- tokens/session
  /** One refresh at a time. Parallel callers share the same request. */
  refreshAccessToken(): Observable<string> {
    if (!this.refreshInFlight$) {
      this.refreshInFlight$ = this.raw
        .post<TokenResponse>(`${this.base}/auth/refresh`, { refresh_token: this.tokens.refreshToken },
          { withCredentials: true })
        .pipe(
          tap(r => this.applyTokens(r)),
          map(r => r.access_token),
          finalize(() => (this.refreshInFlight$ = null)),
          shareReplay(1),
        );
    }
    return this.refreshInFlight$;
  }

  /** Restores the session after a page reload. Used by guards and app start. */
  async restoreSession(): Promise<boolean> {
    if (this.authenticated()) return true;
    if (!this.tokens.refreshToken) return false;
    try {
      await firstValueFrom(this.refreshAccessToken());
      this.tenant.load();
      return true;
    } catch {
      this.clearSession(false);
      return false;
    }
  }

  async signOut(): Promise<void> {
    const refresh_token = this.tokens.refreshToken;
    if (refresh_token) {
      try {
        await firstValueFrom(this.raw.post(`${this.base}/auth/logout`, { refresh_token },
          { withCredentials: true }));
      } catch { /* local sign-out still completes */ }
    }
    this.clearSession();
  }

  clearSession(redirect = true): void {
    this.tokens.clear();
    this.authenticated.set(false);
    this.profile.set(null);
    this.role.set(null);
    this.subscription.reset();
    this.tenant.reset();
    if (redirect) void this.router.navigateByUrl('/signin');
  }

  // ---------------------------------------------------------------- helpers
  private applyTokens(r: TokenResponse): void {
    this.tokens.set(r.access_token, r.refresh_token);
    const claims = decodeClaims(r.access_token);
    this.role.set(claims['role'] ?? null);
    this.subscription.update(r.subscription_status, r.subscription_days_left);
    this.authenticated.set(true);
    if (!this.profile() && claims['email']) {
      this.profile.set({ name: String(claims['email']).split('@')[0], email: claims['email'], phone: '' });
    }
  }

  private startSession(r: TokenResponse, profile: OwnerProfile): void {
    this.applyTokens(r);
    this.profile.set(profile);
    this.tenant.load();
  }

  private shopBody(s: ShopDetails) {
    return {
      shop_name: s.shopName, shop_types: s.shopTypes,
      address_line: s.addressLine, village_town: s.villageTown, mandal_taluk: s.mandalTaluk,
      district: s.district, state: s.state, pincode: s.pincode,
      gstin: s.gstin, pan: s.pan, referral_code: s.referralCode, heard_from: s.heardFrom,
    };
  }

  private assertPhone(phone: string): void {
    if (!PHONE_RULE.test(phone)) throw new Error('Enter a valid 10-digit Indian mobile number.');
  }
  private assertOtp(otp: string): void {
    if (!/^\d{6}$/.test(otp)) throw new Error('Enter the 6-digit code.');
  }
  private assertNewPassword(password: string): void {
    if (!PASSWORD_RULE.test(password)) {
      throw new Error('Use at least 8 characters with upper case, lower case, a number and a symbol.');
    }
  }

  private getGoogleIdToken(): Promise<string> {
    const google = (window as any).google;
    if (!google?.accounts?.id || !environment.googleClientId) {
      return Promise.reject(new Error('Google sign-in is not configured.'));
    }
    return new Promise<string>((resolve, reject) => {
      google.accounts.id.initialize({
        client_id: environment.googleClientId,
        callback: (r: any) => r?.credential ? resolve(r.credential)
          : reject(new Error('Google sign-in was cancelled.')),
      });
      google.accounts.id.prompt((n: any) => {
        if (n.isNotDisplayed?.() || n.isSkippedMoment?.()) {
          reject(new Error('Google sign-in could not be shown. Allow pop-ups and try again.'));
        }
      });
    });
  }

  private apiError(error: unknown): Error {
    if (error instanceof Error && !(error instanceof HttpErrorResponse)) return error;
    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) return new Error('Cannot reach the server. Check your connection.');
      const body = error.error;
      const detail = body?.detail ?? body?.code;
      if (typeof detail === 'string') return new Error(MESSAGES[detail] ?? detail);
      if (Array.isArray(detail) && detail[0]?.msg) return new Error(detail[0].msg);
    }
    return new Error('Unable to complete the request. Please try again.');
  }
}