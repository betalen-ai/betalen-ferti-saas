import { Component, HostListener } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LogoComponent } from '../../shared/logo/logo.component';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, LogoComponent],
  template: `
    <header class="navbar-wrap" [class.scrolled]="scrolled">
      <nav class="container nav-inner" aria-label="Main navigation">
        <app-logo></app-logo>
        <button class="menu-toggle" (click)="open = !open" [attr.aria-expanded]="open" aria-label="Toggle menu"><i class="bi bi-list"></i></button>
        <div class="nav-links" [class.open]="open">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact:true}" (click)="open=false">Home</a>
          <a routerLink="/about" routerLinkActive="active" (click)="open=false">About</a>
          <a routerLink="/products" routerLinkActive="active" (click)="open=false">Products</a>
          <a routerLink="/pricing" routerLinkActive="active" (click)="open=false">Pricing</a>
          <a routerLink="/contact" routerLinkActive="active" (click)="open=false">Contact</a>
          <div class="nav-auth">
            <a class="btn btn-outline-primary" routerLink="/signin" (click)="open=false">Sign in</a>
            <a class="btn btn-primary" routerLink="/signup" (click)="open=false">Sign up free</a>
          </div>
        </div>
      </nav>
    </header>
  `,
  styles: [`
    .navbar-wrap{position:fixed;z-index:1000;top:0;left:0;right:0;height:82px;color:var(--surface);transition:.25s}.navbar-wrap.scrolled{background:var(--surface);color:var(--text);box-shadow:0 4px 20px rgba(20,33,26,.1)}.nav-inner{height:82px;display:flex;align-items:center;justify-content:space-between}.nav-links{display:flex;align-items:center;gap:28px}.nav-links>a{position:relative;text-decoration:none;color:inherit;font-weight:700}.nav-links>a.active::after{content:'';position:absolute;left:0;right:0;bottom:-10px;height:3px;background:var(--accent)}.nav-auth{display:flex;gap:10px}.menu-toggle{display:none;border:0;background:transparent;font-size:28px;color:inherit}@media(max-width:991px){.menu-toggle{display:block}.nav-links{display:none;position:absolute;top:82px;left:16px;right:16px;background:var(--surface);color:var(--text);padding:24px;border-radius:16px;box-shadow:0 20px 50px rgba(20,33,26,.18);flex-direction:column;align-items:stretch}.nav-links.open{display:flex}.nav-links>a{padding:8px}.nav-auth{margin-top:8px}.nav-auth .btn{flex:1}}
  `]
})
export class NavbarComponent {
  scrolled = false;
  open = false;
  @HostListener('window:scroll') onScroll() { this.scrolled = window.scrollY > 40; }
}
