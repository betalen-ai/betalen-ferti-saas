import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <main class="reset-layout">
      <form class="reset-card" [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <span class="eyebrow">ACCOUNT SECURITY</span><h1>Set a new password</h1>
        <p>Choose a password with at least 8 characters.</p>
        <div class="alert alert-danger" *ngIf="error" role="alert">{{error}}</div>
        <label for="password">New password</label><input id="password" class="form-control" [type]="show ? 'text' : 'password'" formControlName="password" autocomplete="new-password">
        <small class="error" *ngIf="bad('password')">Password must be at least 8 characters.</small>
        <label for="confirm">Confirm new password</label><input id="confirm" class="form-control" [type]="show ? 'text' : 'password'" formControlName="confirm" autocomplete="new-password">
        <small class="error" *ngIf="form.errors?.['mismatch'] && form.controls['confirm'].touched">Passwords do not match.</small>
        <label class="check"><input type="checkbox" (change)="show = !show"> Show passwords</label>
        <button class="btn btn-primary primary-action" [disabled]="loading">{{loading ? 'Updating...' : 'Update password'}}</button>
        <a routerLink="/signin">Back to sign in</a>
      </form>
    </main>
  `,
  styles: [`
    .reset-layout{min-height:100vh;min-height:100svh;display:grid;place-items:center;padding:24px;background:var(--cream)}
    .reset-card{width:min(460px,100%);padding:32px;background:#fff;border:1.5px solid #cbd5ce;border-radius:14px}
    h1{font-size:32px;margin:8px 0}.reset-card p{color:var(--muted)}
    label{display:block;font-weight:700;margin:16px 0 6px}.form-control{min-height:52px}
    .check{display:flex;align-items:center;gap:8px}.check input{width:20px;height:20px}
    .primary-action{width:100%;min-height:56px;margin:20px 0 16px;font-weight:800}
    .reset-card>a{display:block;text-align:center}.error{display:block;color:#b42318;margin-top:5px}
  `]
})
export class ResetPasswordComponent {
  loading = false;
  show = false;
  error = '';
  form: FormGroup;
  private readonly token: string | null;

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router, route: ActivatedRoute) {
    this.token = route.snapshot.queryParamMap.get('token');
    this.form = this.fb.group({
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm: ['', Validators.required]
    }, { validators: (control: AbstractControl) => control.get('password')?.value === control.get('confirm')?.value ? null : { mismatch: true } });
  }

  bad(name: 'password' | 'confirm'): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.dirty || control.touched);
  }

  async submit(): Promise<void> {
    this.error = '';
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    if (!this.token) { this.error = 'This reset link is invalid or has expired. Request a new one.'; return; }
    this.loading = true;
    try {
      await this.auth.resetPassword(this.form.controls['password'].value ?? '');
      await this.router.navigate(['/signin'], { queryParams: { passwordReset: 'true' } });
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to update your password.';
    } finally { this.loading = false; }
  }
}
