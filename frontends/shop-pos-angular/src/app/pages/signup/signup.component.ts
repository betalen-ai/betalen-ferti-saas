import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { LogoComponent } from '../../shared/logo/logo.component';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    LogoComponent
  ],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.scss'
})
export class SignupComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  loading = false;
  error = '';
  showPassword = false;

  readonly form = this.fb.nonNullable.group(
    {
      ownerName: ['', [Validators.required, Validators.minLength(2)]],
      shopName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(10)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirm: ['', [Validators.required]]
    },
    {
      validators: (control: AbstractControl): ValidationErrors | null => {
        const password = control.get('password')?.value;
        const confirm = control.get('confirm')?.value;

        return password === confirm ? null : { mismatch: true };
      }
    }
  );

  // True when a field is invalid and has been interacted with.
  bad(name: string): boolean {
    const control = this.form.get(name);

    return !!control && control.invalid && (control.dirty || control.touched);
  }

  // Strip non-digits and cap at 10 digits.
  onPhoneInput(): void {
    const control = this.form.controls.phone;
    const mobile = control.value.replace(/[^0-9]/g, '').slice(0, 10);

    if (control.value !== mobile) {
      control.setValue(mobile, { emitEvent: false });
    }
  }

  async submit(): Promise<void> {
    this.error = '';

    this.onPhoneInput();
    this.form.markAllAsTouched();

    if (this.form.invalid) {
      return;
    }

    this.loading = true;

    try {
      const value = this.form.getRawValue();

      await this.auth.signup({
        owner_name: value.ownerName.trim(),
        shop_name: value.shopName.trim(),
        email: value.email.trim().toLowerCase(),
        mobile: value.phone.trim(),
        password: value.password
      });

      await this.router.navigateByUrl('/app/dashboard');

    } catch (error: unknown) {
      const apiError = error as {
        error?: { detail?: unknown; message?: string };
        message?: string;
      };

      const detail = apiError?.error?.detail;

      if (detail === 'email_already_registered') {
        this.error = 'This email address is already registered.';
      } else if (detail === 'tenant_or_user_already_exists') {
        this.error = 'The shop or owner account already exists.';
      } else if (detail === 'subdomain_unavailable') {
        this.error = 'Unable to generate a shop URL. Please try again.';
      } else if (typeof detail === 'string') {
        this.error = detail;
      } else {
        this.error =
          apiError?.error?.message ||
          apiError?.message ||
          'Unable to create your account. Please try again.';
      }

    } finally {
      this.loading = false;
    }
  }
}