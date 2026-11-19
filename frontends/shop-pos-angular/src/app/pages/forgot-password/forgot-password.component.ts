import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { LogoComponent } from '../../shared/logo/logo.component';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, LogoComponent],
  template: `
    <section class="auth-layout">
      <aside class="auth-photo"><app-logo variant="dark"></app-logo><div><span>FERTI+</span><h1>Back to growing.</h1><p>Secure account recovery helps keep your shop information safe.</p></div></aside>
      <div class="auth-panel"><form [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <span class="eyebrow">ACCOUNT RECOVERY</span><h1>Forgot password?</h1>
        <p>Enter your account email or recover a phone-only account with an OTP.</p>
        <div class="method-tabs"><button type="button" [class.active]="method==='email'" (click)="select('email')">Email</button><button type="button" [class.active]="method==='phone'" (click)="select('phone')">Phone</button></div>
        <div class="alert alert-success" *ngIf="sent" role="status">If an account exists, we sent a recovery link or code.</div>
        <label *ngIf="method==='email'" for="email">Email address</label>
        <input *ngIf="method==='email'" id="email" type="email" class="form-control" formControlName="email" autocomplete="email" placeholder="you@shop.com">
        <small class="error" *ngIf="method==='email' && bad('email')">Enter a valid email address.</small>
        <ng-container *ngIf="method==='phone'">
          <label for="phone">Mobile number</label><div class="phone-input"><span>+91</span><input id="phone" type="tel" inputmode="numeric" maxlength="10" class="form-control" formControlName="phone"></div>
          <small class="error" *ngIf="bad('phone')">Enter a valid 10-digit mobile number.</small>
          <button *ngIf="!otpSent" type="button" class="btn btn-primary action" [disabled]="loading" (click)="sendCode()">Send recovery code</button>
          <ng-container *ngIf="otpSent"><label for="otp">6-digit recovery code</label><input id="otp" class="form-control" inputmode="numeric" maxlength="6" formControlName="otp" autocomplete="one-time-code"><small class="hint">Demo code: 123456 · Attempts remaining: {{5-attempts}}.</small></ng-container>
        </ng-container>
        <button *ngIf="method==='email' || otpSent" type="submit" class="btn btn-primary action" [disabled]="loading">{{loading ? 'Checking...' : method==='email' ? 'Send recovery link' : 'Verify code'}}</button>
        <div class="alert alert-danger" *ngIf="error" role="alert">{{error}}</div>
        <a class="back" routerLink="/signin">Back to sign in</a>
        <p class="mock-notice">Demo recovery flow; the response does not reveal whether an account exists.</p>
      </form></div>
    </section>
  `,
  styles: [`
    :host{display:block}.auth-layout{min-height:100vh;min-height:100svh;display:grid;grid-template-columns:1fr 1fr}.auth-photo{padding:36px 42px;background:linear-gradient(180deg,rgba(8,77,42,.2),rgba(8,77,42,.92)),url('https://images.unsplash.com/photo-1529313780224-1a12b68bed16?auto=format&fit=crop&w=1200&q=80') center/cover;color:white;display:flex;flex-direction:column;justify-content:space-between}
    .auth-photo app-logo{color:white}.auth-photo div span{font-size:14px;font-weight:800;letter-spacing:.15em}.auth-photo h1{color:white;font-size:46px}.auth-photo p{color:rgba(255,255,255,.9)}
    .auth-panel{display:grid;place-items:center;min-width:0;padding:40px;background:var(--cream)}form{width:min(440px,100%)}h1{font-size:clamp(30px,3vw,38px);margin:8px 0}.auth-panel p{color:var(--muted)}
    label{display:block;font-weight:700;margin:14px 0 6px}.form-control{min-height:52px}.method-tabs{display:grid;grid-template-columns:1fr 1fr;margin:18px 0;border-bottom:1.5px solid #cbd5ce}.method-tabs button{height:48px;border:0;border-bottom:3px solid transparent;background:transparent;font:inherit;font-weight:700}.method-tabs button.active{border-color:var(--primary);color:var(--primary)}
    .phone-input{display:flex;gap:8px}.phone-input>span{display:grid;place-items:center;padding:0 12px;border:1.5px solid #cbd5ce;border-radius:10px;background:white}.phone-input input{flex:1}
    .action{width:100%;min-height:56px;margin-top:18px;font-size:18px;font-weight:800}.error{display:block;color:#b42318}.hint,.mock-notice{display:block;font-size:14px;color:var(--muted)}.back{display:block;margin:20px;text-align:center}.mock-notice{text-align:center}
    @media(max-width:900px){.auth-layout{grid-template-columns:1fr}.auth-photo{min-height:155px;padding:20px}.auth-photo div{margin-top:auto}.auth-photo h1{font-size:28px;margin:6px 0}.auth-photo p{display:none}.auth-panel{padding:28px 20px}}
  `]
})
export class ForgotPasswordComponent implements OnDestroy {
  form: FormGroup;
  method: 'email' | 'phone' = 'email';
  loading = false;
  sent = false;
  otpSent = false;
  attempts = 0;
  error = '';
  private interval?: ReturnType<typeof setTimeout>;

  constructor(private fb: FormBuilder, private auth: AuthService) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      phone: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
      otp: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]]
    });
  }

  ngOnDestroy(): void { if (this.interval) clearTimeout(this.interval); }
  bad(name: 'email' | 'phone'): boolean { const control = this.form.controls[name]; return control.invalid && (control.dirty || control.touched); }

  select(method: 'email' | 'phone'): void { this.method = method; this.sent = false; this.error = ''; this.otpSent = false; }

  async sendCode(): Promise<void> {
    this.form.controls['phone'].markAsTouched();
    if (this.form.controls['phone'].invalid) return;
    this.loading = true; this.error = '';
    try { await this.auth.sendOtp(this.form.controls['phone'].value ?? ''); this.otpSent = true; }
    catch (error) { this.error = error instanceof Error ? error.message : 'Unable to send a recovery code.'; }
    finally { this.loading = false; }
  }

  async submit(): Promise<void> {
    this.error = '';
    if (this.method === 'email') {
      this.form.controls['email'].markAsTouched();
      if (this.form.controls['email'].invalid) return;
      this.loading = true;
      try { await this.auth.requestPasswordReset(this.form.controls['email'].value ?? ''); this.sent = true; }
      catch { this.error = 'Unable to send recovery instructions right now. Please try again.'; }
      finally { this.loading = false; }
      return;
    }

    this.form.controls['otp'].markAsTouched();
    if (!this.otpSent || this.form.controls['otp'].invalid || this.attempts >= 5) return;
    this.attempts++;
    this.loading = true;
    try { await this.auth.checkOtp(this.form.controls['phone'].value ?? '', this.form.controls['otp'].value ?? ''); this.sent = true; }
    catch (error) { this.error = error instanceof Error ? error.message : 'That code is not valid. Try again.'; }
    finally { this.loading = false; }
  }
}
