import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { LogoComponent } from '../../shared/logo/logo.component';

type SignInMethod = 'email' | 'phone';

@Component({
  selector: 'app-signin',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink, LogoComponent],
  template: `
    <section class="auth-layout">
      <aside class="auth-photo">
        <app-logo variant="dark"></app-logo>
        <div>
          <span>FERTI+</span>
          <h1>Growing better,<br>together.</h1>
          <p>Every farmer, product and sale in one simple place for your shop.</p>
        </div>
      </aside>
      <div class="auth-panel">
        <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <span class="eyebrow">WELCOME BACK</span>
          <h1>Sign in to Ferti+</h1>
          <p class="lead">Choose how you would like to sign in to your shop.</p>

          <div class="method-tabs" role="tablist" aria-label="Sign-in method">
            <button type="button" role="tab" [attr.aria-selected]="method === 'email'" [class.active]="method === 'email'" (click)="selectMethod('email')">Email</button>
            <button type="button" role="tab" [attr.aria-selected]="method === 'phone'" [class.active]="method === 'phone'" (click)="selectMethod('phone')">Phone</button>
          </div>

          <div class="alert alert-danger" *ngIf="error" role="alert">{{error}}</div>
          
          <ng-container *ngIf="method === 'email'; else phoneForm">
            <label for="email">Email address</label>
            <input id="email" type="email" class="form-control" formControlName="email" autocomplete="username" placeholder="you@shop.com">
            <small class="error" *ngIf="bad('email')">Enter a valid email address.</small>
            
            <div class="label-row">
              <label for="password">Password</label>
              <a routerLink="/forgot-password">Forgot password?</a>
            </div>
            <div class="password">
              <input id="password" [type]="showPassword ? 'text' : 'password'" class="form-control" formControlName="password" autocomplete="current-password">
              <button type="button" class="toggle-password" (click)="showPassword = !showPassword" [attr.aria-label]="showPassword ? 'Hide password' : 'Show password'">{{showPassword ? 'Hide' : 'Show'}}</button>
            </div>
            <small class="error" *ngIf="bad('password')">Password must be at least 8 characters.</small>

            <label for="tenantId">Shop Subdomain / Tenant ID</label>
            <input id="tenantId" type="text" class="form-control" formControlName="tenantId" placeholder="e.g. greenvalley">
            <small class="hint">Leave blank if you are a Super Admin.</small>

            <button class="btn btn-primary primary-action" [disabled]="loading">{{loading ? 'Signing in...' : 'Sign in'}} <i class="bi bi-arrow-right"></i></button>
          </ng-container>

          <ng-template #phoneForm>
            <label for="phone">Mobile number</label>
            <div class="phone-input"><span>+91</span><input id="phone" type="tel" inputmode="numeric" maxlength="10" class="form-control" formControlName="phone" autocomplete="tel-national" placeholder="10-digit mobile number"></div>
            <small class="error" *ngIf="bad('phone')">Enter a valid 10-digit Indian mobile number.</small>
            <button *ngIf="!otpSent" type="button" class="btn btn-primary primary-action" [disabled]="loading" (click)="sendCode()">{{loading ? 'Sending code...' : 'Send OTP'}}</button>
            
            <ng-container *ngIf="otpSent">
              <label for="otp">6-digit verification code</label>
              <input id="otp" type="text" inputmode="numeric" maxlength="6" class="form-control otp-input" formControlName="otp" autocomplete="one-time-code" placeholder="Enter code">
              <small class="hint">Demo code: 123456 · Code expires in {{otpExpiry}}.</small>
              <small class="error" *ngIf="bad('otp')">Enter the 6-digit code.</small>
              <small class="hint">Attempts remaining: {{5 - attempts}}.</small>
              <button type="submit" class="btn btn-primary primary-action" [disabled]="loading || attempts >= 5">{{loading ? 'Verifying...' : 'Verify and sign in'}}</button>
              <button type="button" class="btn secondary-action resend" [disabled]="resendSeconds > 0 || loading || attempts >= 5" (click)="sendCode()">
                {{resendSeconds > 0 ? 'Resend code in ' + resendSeconds + 's' : 'Resend code'}}
              </button>
            </ng-container>
          </ng-template>

          <div class="divider"><span>or</span></div>
          <div class="google-setup" *ngIf="googleSetup">
            <p>Finish setting up your shop to continue with Google.</p>
            <label for="google-shop">Shop name</label><input id="google-shop" class="form-control" [(ngModel)]="googleShopName" [ngModelOptions]="{standalone:true}">
            <label for="google-phone">Mobile number</label><input id="google-phone" class="form-control" type="tel" inputmode="numeric" maxlength="10" [(ngModel)]="googlePhone" [ngModelOptions]="{standalone:true}">
            <button type="button" class="btn btn-primary primary-action" [disabled]="loading" (click)="completeGoogleSignIn()">Continue with Google</button>
          </div>
          <button *ngIf="!googleSetup" type="button" class="btn secondary-action google" [disabled]="loading" (click)="signInGoogle()">
            <i class="bi bi-google"></i> Continue with Google
          </button>
          <p class="switch">New to Ferti+? <a routerLink="/signup">Create a free account</a></p>
          <p class="mock-notice">Demo authentication: OTP is 123456; Google sign-in is simulated.</p>
        </form>
      </div>
    </section>
  `,
  styles: [`
    :host{display:block;min-height:100vh;min-height:100svh}
    .auth-layout{display:grid;grid-template-columns:1fr 1fr;min-height:100vh;min-height:100svh}
    .auth-photo{min-height:100%;padding:36px 42px;background:linear-gradient(180deg,rgba(8,77,42,.2),rgba(8,77,42,.92)),url('https://images.unsplash.com/photo-1530836176759-510bc5e1c4e8?auto=format&fit=crop&w=1200&q=80') center/cover;color:white;display:flex;flex-direction:column;justify-content:space-between}
    .auth-photo app-logo{color:white}.auth-photo div{max-width:520px}.auth-photo div span{font-size:14px;font-weight:800;letter-spacing:.15em}
    .auth-photo h1{color:white;font-size:48px}.auth-photo p{font-size:18px;color:rgba(255,255,255,.9)}
    .auth-panel{min-width:0;background:var(--cream);display:grid;place-items:center;padding:40px}.auth-panel form{width:min(440px,100%)}
    .auth-panel h1{font-size:clamp(30px,3vw,38px);margin:8px 0}.lead{color:var(--muted);margin-bottom:20px}
    .auth-panel label{display:block;font-weight:700;margin:14px 0 6px}
    .method-tabs{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:20px 0;border-bottom:1.5px solid #cbd5ce}
    .method-tabs button{height:48px;border:0;border-bottom:3px solid transparent;background:transparent;color:var(--muted);font:inherit;font-weight:700}
    .method-tabs button.active{border-bottom-color:var(--primary);color:var(--primary)}
    .label-row{display:flex;align-items:end;justify-content:space-between;gap:12px}.label-row a{font-size:14px;margin-bottom:6px;white-space:nowrap}
    .password{position:relative}.password input{padding-right:70px}.toggle-password{position:absolute;right:8px;top:6px;height:36px;border:0;background:transparent;color:var(--primary);font-weight:700}
    .phone-input{display:flex;align-items:center;gap:8px}.phone-input>span{height:52px;display:grid;place-items:center;padding:0 12px;border:1.5px solid #cbd5ce;border-radius:10px;background:#fff;font-weight:700}
    .phone-input input{flex:1}.otp-input{letter-spacing:.35em}.primary-action,.secondary-action{width:100%;min-height:56px;margin-top:18px;font-size:18px;font-weight:800}
    .secondary-action{min-height:48px;border:1.5px solid var(--primary);background:white;color:var(--primary);font-size:16px}
    .resend{margin-top:8px}.divider{height:1px;background:#cbd5ce;margin:26px 0;position:relative}.divider span{position:absolute;left:50%;top:-13px;transform:translateX(-50%);background:var(--cream);padding:0 14px;color:var(--muted)}
    .google{margin-top:0}.google i{margin-right:8px}.switch{text-align:center;margin:20px 0 8px;color:var(--muted)}
    .google-setup{padding:14px;border:1.5px solid #cbd5ce;border-radius:10px;background:white}.google-setup p{margin:0;color:var(--muted)}
    .mock-notice,.hint{display:block;color:var(--muted);font-size:14px}.mock-notice{text-align:center}.error{display:block;color:#b42318;margin-top:5px;font-size:14px}
    @media(max-width:900px){.auth-layout{grid-template-columns:1fr}.auth-photo{min-height:180px;padding:20px}.auth-photo div{margin-top:auto}.auth-photo h1{font-size:28px;margin:5px 0}.auth-photo p{display:none}.auth-panel{min-height:calc(100vh - 180px);min-height:calc(100svh - 180px);padding:36px 24px}}
    @media(max-width:575px){.auth-photo{min-height:150px}.auth-panel{padding:28px 20px}.auth-panel h1{font-size:30px}}
  `]
})
export class SigninComponent implements OnDestroy {
  method: SignInMethod = 'email';
  showPassword = false;
  loading = false;
  error = '';
  otpSent = false;
  attempts = 0;
  resendSeconds = 0;
  otpExpiry = '05:00';
  googleSetup = false;
  googleShopName = '';
  googlePhone = '';
  private interval?: ReturnType<typeof setInterval>;
  private otpExpiresAt = 0;
  form: FormGroup;

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router, private route: ActivatedRoute) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      phone: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
      otp: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]],
      tenantId: ['']
    });
  }

  ngOnDestroy(): void {
    if (this.interval) clearInterval(this.interval);
  }

  selectMethod(method: SignInMethod): void {
    this.method = method;
    this.error = '';
    this.otpSent = false;
    this.form.get(method === 'email' ? 'phone' : 'email')?.markAsUntouched();
  }

  bad(name: string): boolean {
    const control = this.form.get(name);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  async submit(): Promise<void> {
    this.error = '';
    if (this.method === 'email') {
      const email = this.form.controls['email'];
      const password = this.form.controls['password'];
      email.markAsTouched();
      password.markAsTouched();
      if (email.invalid || password.invalid) return;
      
      await this.runAuth(() => this.auth.signInEmail(email.value ?? '', password.value ?? '', this.form.controls['tenantId'].value ?? undefined));
      return;
    }

    const otp = this.form.controls['otp'];
    otp.markAsTouched();
    if (otp.invalid || !this.otpSent || this.attempts >= 5) return;
    if (Date.now() > this.otpExpiresAt) {
      this.error = 'That code has expired. Request a new one to continue.';
      return;
    }
    this.attempts++;
    await this.runAuth(() => this.auth.signInOtp(this.form.controls['phone'].value ?? '', otp.value ?? ''));
  }

  async sendCode(): Promise<void> {
    const phone = this.form.controls['phone'];
    phone.markAsTouched();
    if (phone.invalid) return;
    this.loading = true;
    this.error = '';
    try {
      await this.auth.sendOtp(phone.value ?? '', 'LOGIN');
      this.otpSent = true;
      this.attempts = 0;
      this.form.controls['otp'].reset('');
      this.resendSeconds = 30;
      this.otpExpiresAt = Date.now() + 5 * 60 * 1000;
      this.startCountdown();
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to send a verification code right now.';
    } finally {
      this.loading = false;
    }
  }

  signInGoogle(): void {
    this.error = '';
    this.googleSetup = true;
  }

  async completeGoogleSignIn(): Promise<void> {
    await this.runAuth(() => this.auth.signInGoogle());
  }

  private async runAuth(action: () => Promise<void>): Promise<void> {
    this.loading = true;
    this.error = '';
    try {
      await action();
      const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
      await this.router.navigateByUrl(returnUrl?.startsWith('/app') ? returnUrl : '/app/dashboard');
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to sign in right now. Please try again.';
    } finally {
      this.loading = false;
    }
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