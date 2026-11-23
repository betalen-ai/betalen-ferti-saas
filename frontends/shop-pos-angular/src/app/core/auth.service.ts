import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Router } from '@angular/router';
import { TenantService } from './tenant.service';

export interface OwnerProfile {
  name: string;
  email: string;
  phone: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly authenticated = signal(false);
  readonly profile = signal<OwnerProfile | null>(null);
  private accessToken: string | null = null;
  private phoneVerifiedToken: string | null = null;
  private googleRegistrationToken: string | null = null;

  constructor(private router: Router, private tenant: TenantService, private http: HttpClient) {}

  async signInEmail(email: string, password: string, tenantId?: string): Promise<void> {
    try {
      const result = await firstValueFrom(this.http.post<any>('/api/v1/auth/login', { tenant_id: tenantId || undefined, email: email.trim().toLowerCase(), password }, { withCredentials: true }));
      this.accessToken = result.access_token ?? null;
      this.startSession({ name: email.split('@')[0], email: email.trim(), phone: '' });
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async sendOtp(phone: string, purpose: 'LOGIN' | 'REGISTER_VERIFY' | 'RESET_PASSWORD' = 'REGISTER_VERIFY'): Promise<void> {
    if (!/^[6-9]\d{9}$/.test(phone)) {
      throw new Error('Enter a valid 10-digit Indian mobile number.');
    }
    try {
      await firstValueFrom(this.http.post('/api/v1/auth/otp/send', { phone: `+91${phone}`, purpose }, { withCredentials: true }));
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async verifyOtp(phone: string, otp: string): Promise<void> {
    if (!/^[6-9]\d{9}$/.test(phone) || !/^\d{6}$/.test(otp)) {
      throw new Error('That code is not valid. Check it and try again.');
    }
    try {
      const result = await firstValueFrom(this.http.post<any>(
        '/api/v1/auth/otp/verify',
        { phone: `+91${phone}`, otp, purpose: 'LOGIN' },
        { withCredentials: true },
      ));
      this.accessToken = result.access_token ?? null;
      this.startSession({ name: `Shop owner ${phone.slice(-4)}`, email: '', phone });
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async checkOtp(phone: string, otp: string, purpose: 'LOGIN' | 'REGISTER_VERIFY' | 'RESET_PASSWORD' = 'REGISTER_VERIFY'): Promise<void> {
    if (!/^[6-9]\d{9}$/.test(phone) || !/^\d{6}$/.test(otp)) {
      throw new Error('That code is not valid. Check it and try again.');
    }
    try {
      const result = await firstValueFrom(this.http.post<any>(
        '/api/v1/auth/otp/verify',
        { phone: `+91${phone}`, otp, purpose },
        { withCredentials: true },
      ));
      this.phoneVerifiedToken = result.phoneVerifiedToken ?? null;
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async signInGoogle(shopName?: string, phone?: string): Promise<void> {
    const idToken = await this.getGoogleIdToken();
    try {
      const result = await firstValueFrom(this.http.post<any>('/api/v1/auth/google', { idToken }, { withCredentials: true }));
      if (result.registrationRequired) {
        this.googleRegistrationToken = result.registrationToken ?? null;
        throw new Error('REGISTRATION_REQUIRED');
      }
      this.accessToken = result.access_token ?? null;
      this.startSession({ name: 'Ferti+ Shop Owner', email: result.email ?? 'owner@example.com', phone: phone ?? '' });
    } catch (error) {
      if (error instanceof Error && error.message === 'REGISTRATION_REQUIRED') throw error;
      throw this.apiError(error);
    }
  }

  async register(profile: OwnerProfile, password: string): Promise<void> {
    if (!profile.name.trim() || !profile.email.trim() || password.length < 8) {
      throw new Error('Complete the required account details with a password of at least 8 characters.');
    }
    if (!this.phoneVerifiedToken) {
      throw new Error('Verify your mobile number before submitting the request.');
    }
    try {
      await firstValueFrom(this.http.post('/api/v1/onboarding/requests', {
        ownerFullName: profile.name,
        ownerEmail: profile.email,
        ownerPhone: `+91${profile.phone}`,
        ownerPassword: password,
        confirmPassword: password,
        shopName: this.tenant.name(),
        preferredLanguage: 'en',
        phoneVerifiedToken: this.phoneVerifiedToken,
        termsAccepted: true,
        privacyAccepted: true,
        termsVersion: '2026-11-22',
        contactConsent: true,
      }));
      this.profile.set(profile);
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async resetPassword(password: string): Promise<void> {
    if (password.length < 8) {
      throw new Error('Choose a password with at least 8 characters.');
    }
    throw new Error('Use the password-reset link from your email or the verified OTP flow.');
  }

  async requestPasswordReset(identifier: string): Promise<void> {
    try {
      await firstValueFrom(this.http.post('/api/v1/auth/forgot-password', { email: identifier, subdomain: '' }));
    } catch (error) {
      throw this.apiError(error);
    }
  }

  async signOut(): Promise<void> {
    try {
      await firstValueFrom(this.http.post('/api/v1/auth/logout', {}, { withCredentials: true }));
    } catch {
      // Local sign-out still completes if the API is unavailable.
    }
    this.accessToken = null;
    this.authenticated.set(false);
    this.profile.set(null);
    await this.router.navigateByUrl('/signin');
  }

  private startSession(profile: OwnerProfile): void {
    this.profile.set(profile);
    this.authenticated.set(true);
  }

  private async getGoogleIdToken(): Promise<string> {
    const google = (window as any).google;
    if (!google?.accounts?.id) {
      throw new Error('Google sign-in is not configured in this browser.');
    }
    return await new Promise<string>((resolve, reject) => {
      google.accounts.id.initialize({
        client_id: (window as any).FERTI_GOOGLE_CLIENT_ID,
        callback: (response: any) => response?.credential ? resolve(response.credential) : reject(new Error('Google sign-in was cancelled.')),
      });
      google.accounts.id.prompt();
    });
  }

  private apiError(error: unknown): Error {
    if (error instanceof HttpErrorResponse) {
      const body = error.error;
      if (body?.code || body?.detail) {
        return new Error(body.detail ?? body.message ?? body.code);
      }
    }
    return new Error('Unable to complete the request. Please try again.');
  }
}
