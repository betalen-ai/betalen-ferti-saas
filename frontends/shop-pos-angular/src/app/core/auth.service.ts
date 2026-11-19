import { Injectable, signal } from '@angular/core';
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

  constructor(private router: Router, private tenant: TenantService) {}

  async signInEmail(email: string, password: string): Promise<void> {
    await this.mockRequest();
    if (!email.trim() || password.length < 8) {
      throw new Error('Check your email and password, then try again.');
    }
    this.startSession({ name: email.split('@')[0], email: email.trim(), phone: '' });
  }

  async sendOtp(phone: string): Promise<void> {
    await this.mockRequest();
    if (!/^[6-9]\d{9}$/.test(phone)) {
      throw new Error('Enter a valid 10-digit Indian mobile number.');
    }
  }

  async verifyOtp(phone: string, otp: string): Promise<void> {
    await this.checkOtp(phone, otp);
    this.startSession({ name: `Shop owner ${phone.slice(-4)}`, email: '', phone });
  }

  async checkOtp(phone: string, otp: string): Promise<void> {
    await this.mockRequest();
    if (!/^[6-9]\d{9}$/.test(phone) || otp !== '123456') {
      throw new Error('That code is not valid. Check it and try again.');
    }
  }

  async signInGoogle(shopName?: string, phone?: string): Promise<void> {
    await this.mockRequest();
    if (shopName !== undefined || phone !== undefined) {
      if (!shopName?.trim() || !phone || !/^[6-9]\d{9}$/.test(phone)) {
        throw new Error('Enter your shop name and a valid 10-digit mobile number to finish Google sign-up.');
      }
      this.tenant.updateName(shopName);
      this.startSession({ name: 'Ferti+ Shop Owner', email: 'owner@example.com', phone });
      return;
    }
    this.startSession({ name: 'Ferti+ Shop Owner', email: 'owner@example.com', phone: '' });
  }

  async register(profile: OwnerProfile, password: string): Promise<void> {
    await this.mockRequest();
    if (!profile.name.trim() || !profile.email.trim() || password.length < 8) {
      throw new Error('Complete the required account details with a password of at least 8 characters.');
    }
    this.startSession(profile);
  }

  async resetPassword(password: string): Promise<void> {
    await this.mockRequest();
    if (password.length < 8) {
      throw new Error('Choose a password with at least 8 characters.');
    }
  }

  async requestPasswordReset(identifier: string): Promise<void> {
    await this.mockRequest();
    void identifier;
  }

  async signOut(): Promise<void> {
    this.authenticated.set(false);
    this.profile.set(null);
    await this.router.navigateByUrl('/signin');
  }

  private startSession(profile: OwnerProfile): void {
    this.profile.set(profile);
    this.authenticated.set(true);
  }

  private mockRequest(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 180));
  }
}
