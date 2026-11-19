import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-auth-callback',
  standalone: true,
  template: `<main class="callback"><p>{{message}}</p></main>`,
  styles: [`.callback{min-height:100vh;display:grid;place-items:center;padding:24px;font-weight:700;font-size:18px}`]
})
export class AuthCallbackComponent implements OnInit {
  message = 'Completing sign in...';
  constructor(private auth: AuthService, private router: Router) {}

  async ngOnInit(): Promise<void> {
    try {
      await this.auth.signInGoogle();
      await this.router.navigateByUrl('/app/dashboard');
    } catch {
      this.message = 'Google sign-in could not be completed. Please return to sign in and try again.';
    }
  }
}
