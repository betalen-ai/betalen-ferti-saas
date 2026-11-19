import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { TenantService } from '../../core/tenant.service';
import { LogoComponent } from '../../shared/logo/logo.component';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, LogoComponent],
  template: `
    <section class="auth-layout">
      <aside class="auth-photo"><app-logo variant="dark"></app-logo><div><span>FERTI+</span><h1>Your shop,<br>digitised.</h1><p>Start managing stock, billing and farmer credit with one simple account.</p></div></aside>
      <div class="auth-panel">
        <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <span class="eyebrow">FREE SHOP OWNER ACCOUNT</span><h1>Create your account</h1>
          <p class="lead">One owner account for one shop. All features are free.</p>
          <div class="alert alert-danger" *ngIf="error" role="alert">{{error}}</div>
          <div class="form-grid">
            <label>Owner name<input class="form-control" formControlName="ownerName" autocomplete="name"></label>
            <label>Shop name<input class="form-control" formControlName="shopName" autocomplete="organization"></label>
            <label>Email address<input class="form-control" type="email" formControlName="email" autocomplete="email"></label>
            <label>Mobile number<div class="phone-input"><span>+91</span><input class="form-control" type="tel" inputmode="numeric" maxlength="10" formControlName="phone" autocomplete="tel-national"></div></label>
            <label>Password<div class="password"><input class="form-control" [type]="showPassword?'text':'password'" formControlName="password" autocomplete="new-password"><button type="button" (click)="showPassword=!showPassword">{{showPassword?'Hide':'Show'}}</button></div></label>
            <label>Confirm password<input class="form-control" type="password" formControlName="confirm" autocomplete="new-password"></label>
          </div>
          <small class="error" *ngIf="bad('ownerName')">Enter your name.</small>
          <small class="error" *ngIf="bad('shopName')">Enter your shop name.</small>
          <small class="error" *ngIf="bad('email')">Enter a valid email address.</small>
          <small class="error" *ngIf="bad('phone')">Enter a valid 10-digit Indian mobile number.</small>
          <small class="error" *ngIf="bad('password')">Password must have at least 8 characters.</small>
          <div class="strength" aria-label="Password strength"><i [class.on]="strength>0"></i><i [class.on]="strength>1"></i><i [class.on]="strength>2"></i><i [class.on]="strength>3"></i></div>
          <small class="error" *ngIf="form.errors?.['mismatch'] && form.controls['confirm'].touched">Passwords do not match.</small>
          <button *ngIf="!otpSent" type="button" class="btn btn-primary primary-action" [disabled]="loading" (click)="sendCode()">{{loading ? 'Sending code...' : 'Verify mobile number'}}</button>
          <ng-container *ngIf="otpSent">
            <label class="otp-label">Enter the 6-digit SMS code<input class="form-control" inputmode="numeric" maxlength="6" formControlName="otp" autocomplete="one-time-code"></label>
            <small class="hint">Demo code: 123456 · Expires in {{otpExpiry}}. Attempts remaining: {{5 - attempts}}.</small>
            <button type="submit" class="btn btn-primary primary-action" [disabled]="loading || attempts>=5">{{loading ? 'Creating account...' : 'Verify and create account'}}</button>
            <button type="button" class="btn secondary-action" [disabled]="resendSeconds>0 || loading || attempts>=5" (click)="sendCode()">{{resendSeconds ? 'Resend code in '+resendSeconds+'s' : 'Resend code'}}</button>
          </ng-container>
          <p class="email-notice">After sign-up, an email verification link will be sent to your address.</p>
          <div class="divider"><span>or</span></div>
          <button *ngIf="!googleSetup" type="button" class="btn secondary-action" (click)="googleSetup=true"><i class="bi bi-google"></i> Continue with Google</button>
          <div *ngIf="googleSetup" class="google-setup">
            <label>Shop name<input class="form-control" #googleShop></label><label>Mobile number<input class="form-control" type="tel" maxlength="10" #googlePhone></label>
            <button type="button" class="btn btn-primary primary-action" (click)="signUpWithGoogle(googleShop.value, googlePhone.value)">Finish Google sign-up</button>
          </div>
          <p class="switch">Already have an account? <a routerLink="/signin">Sign in</a></p>
          <p class="mock-notice">Demo authentication: OTP is 123456; Google sign-up is simulated.</p>
        </form>
      </div>
    </section>
  `,
  styles: [`
    :host{display:block}.auth-layout{display:grid;grid-template-columns:.8fr 1.2fr;min-height:100vh;min-height:100svh}
    .auth-photo{position:sticky;top:0;height:100vh;min-height:100svh;padding:36px 42px;background:linear-gradient(180deg,rgba(8,77,42,.2),rgba(8,77,42,.92)),url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1200&q=80') center/cover;color:#fff;display:flex;flex-direction:column;justify-content:space-between}
    .auth-photo app-logo{color:white}.auth-photo div span{font-size:14px;font-weight:800;letter-spacing:.15em}.auth-photo h1{color:white;font-size:48px}.auth-photo p{color:rgba(255,255,255,.9)}
    .auth-panel{min-width:0;background:var(--cream);display:grid;place-items:center;padding:36px}.auth-panel form{width:min(720px,100%)}.auth-panel h1{font-size:clamp(30px,3vw,38px);margin:8px 0}.lead{color:var(--muted)}
    .form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.form-grid label,.otp-label{display:block;font-weight:700;margin:10px 0 4px}.form-control{min-height:52px;margin-top:5px}
    .phone-input{display:flex;gap:8px}.phone-input>span{display:grid;place-items:center;padding:0 12px;border:1.5px solid #cbd5ce;border-radius:10px;background:white}.phone-input input{min-width:0}
    .password{position:relative}.password input{padding-right:70px}.password button{position:absolute;right:7px;top:10px;height:36px;border:0;background:transparent;color:var(--primary);font-weight:700}
    .strength{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:10px 0}.strength i{height:5px;border-radius:5px;background:#dfe6e1}.strength i.on{background:var(--accent)}
    .primary-action,.secondary-action{width:100%;min-height:56px;margin-top:12px;font-size:18px;font-weight:800}.secondary-action{min-height:48px;background:white;border:1.5px solid var(--primary);color:var(--primary);font-size:16px}
    .error{display:block;color:#b42318;margin-top:4px}.hint,.email-notice,.mock-notice{display:block;color:var(--muted);font-size:14px}.email-notice{margin:12px 0}
    .divider{height:1px;background:#cbd5ce;margin:22px 0;position:relative}.divider span{position:absolute;left:50%;top:-12px;transform:translateX(-50%);padding:0 14px;background:var(--cream);color:var(--muted)}
    .switch{text-align:center;margin:20px 0 8px;color:var(--muted)}.mock-notice{text-align:center}.google-setup{padding:14px;border:1.5px solid #cbd5ce;border-radius:10px;background:white}
    @media(max-width:900px){.auth-layout{grid-template-columns:1fr}.auth-photo{position:relative;height:auto;min-height:170px;padding:20px}.auth-photo div{margin-top:auto}.auth-photo h1{font-size:28px;margin:5px 0}.auth-photo p{display:none}.auth-panel{padding:30px 20px}}
    @media(max-width:575px){.auth-photo{min-height:145px}.form-grid{grid-template-columns:1fr}.auth-panel{padding:26px 18px}}
  `]
})
export class SignupComponent implements OnDestroy {
  form: FormGroup;
  loading = false;
  error = '';
  showPassword = false;
  otpSent = false;
  attempts = 0;
  resendSeconds = 0;
  otpExpiry = '05:00';
  googleSetup = false;
  private interval?: ReturnType<typeof setInterval>;
  private otpExpiresAt = 0;

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router, private tenant: TenantService) {
    this.form = this.fb.group({
      ownerName: ['', Validators.required],
      shopName: ['', Validators.required],
      phone: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm: ['', Validators.required],
      otp: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]]
    }, { validators: (control: AbstractControl) => control.get('password')?.value === control.get('confirm')?.value ? null : { mismatch: true } });
  }

  get strength(): number {
    const value = this.form.controls['password'].value ?? '';
    return [value.length >= 8, /\d/.test(value), /[A-Z]/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
  }

  ngOnDestroy(): void { if (this.interval) clearInterval(this.interval); }

  bad(name: 'ownerName' | 'shopName' | 'phone' | 'email' | 'password'): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.dirty || control.touched);
  }

  async sendCode(): Promise<void> {
    this.error = '';
    this.form.markAllAsTouched();
    const required = ['ownerName', 'shopName', 'phone', 'email', 'password', 'confirm'];
    if (required.some(name => this.form.get(name)?.invalid) || this.form.errors?.['mismatch']) return;
    this.loading = true;
    try {
      await this.auth.sendOtp(this.form.controls['phone'].value ?? '');
      this.otpSent = true;
      this.attempts = 0;
      this.resendSeconds = 30;
      this.otpExpiresAt = Date.now() + 5 * 60 * 1000;
      this.startCountdown();
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to send a verification code.';
    } finally { this.loading = false; }
  }

  async submit(): Promise<void> {
    this.error = '';
    this.form.markAllAsTouched();
    if (this.form.invalid || !this.otpSent || this.attempts >= 5) return;
    if (Date.now() > this.otpExpiresAt) { this.error = 'That code has expired. Request a new one.'; return; }
    this.attempts++;
    this.loading = true;
    try {
      await this.auth.checkOtp(this.form.controls['phone'].value ?? '', this.form.controls['otp'].value ?? '');
      const { ownerName, shopName, email, phone, password } = this.form.getRawValue();
      await this.auth.register({ name: ownerName ?? '', email: email ?? '', phone: phone ?? '' }, password ?? '');
      this.tenant.updateName(shopName ?? '');
      await this.router.navigateByUrl('/app/dashboard');
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to create the account.';
    } finally { this.loading = false; }
  }

  async signUpWithGoogle(shopName: string, phone: string): Promise<void> {
    this.error = '';
    this.loading = true;
    try {
      await this.auth.signInGoogle(shopName, phone);
      await this.router.navigateByUrl('/app/dashboard');
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to complete Google sign-up.';
    } finally { this.loading = false; }
  }

  private startCountdown(): void {
    if (this.interval) clearInterval(this.interval);
    this.interval = setInterval(() => {
      if (this.resendSeconds > 0) this.resendSeconds--;
      const remaining = Math.max(0, Math.ceil((this.otpExpiresAt - Date.now()) / 1000));
      this.otpExpiry = `${String(Math.floor(remaining / 60)).padStart(2, '0')}:${String(remaining % 60).padStart(2, '0')}`;
    }, 1000);
  }
}
