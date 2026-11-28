import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LogoComponent } from '../../shared/logo/logo.component';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [RouterLink, LogoComponent],
  template: `
    <footer>
      <div class="container footer-grid">
        <div><app-logo variant="dark"></app-logo><p>Simple, free business management for every fertilizer shop in India.</p><div class="social"><i class="bi bi-facebook"></i><i class="bi bi-instagram"></i><i class="bi bi-youtube"></i></div></div>
        <div><h3>Quick Links</h3><a routerLink="/about">About</a><a routerLink="/pricing">Pricing</a><a routerLink="/contact">Contact</a></div>
        <div><h3>Products</h3><a routerLink="/products">Inventory</a><a routerLink="/products">Billing</a><a routerLink="/products">Farmer ledger</a></div>
        <div><h3>Stay updated</h3><p>shop&#64;ferti.in<br>+91 98765 43210</p><div class="newsletter"><input aria-label="Email address" placeholder="Your email"><button aria-label="Subscribe"><i class="bi bi-arrow-right"></i></button></div></div>
      </div>
      <div class="container bottom"><span>© 2026 Ferti+. All rights reserved.</span><span><a>Privacy Policy</a> <a>Terms</a></span></div>
    </footer>
  `,
  styles:[`
    footer{background:var(--primary-dark);color:white;padding-top:64px}.footer-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr 1.25fr;gap:48px;padding-bottom:48px}.footer-grid p{color:rgba(255,255,255,.75);margin-top:18px}.footer-grid h3{font-size:16px;color:white;margin-bottom:18px}.footer-grid a{display:block;color:rgba(255,255,255,.75);text-decoration:none;margin:8px 0}.social{display:flex;gap:14px}.newsletter{display:flex}.newsletter input{min-width:0;width:100%;border:0;border-radius:10px 0 0 10px;padding:11px}.newsletter button{border:0;border-radius:0 10px 10px 0;background:var(--gold);width:48px}.bottom{border-top:1px solid rgba(255,255,255,.15);padding:18px 0;display:flex;justify-content:space-between;color:rgba(255,255,255,.65);font-size:13px}.bottom a{color:inherit;margin-left:16px}@media(max-width:991px){.footer-grid{grid-template-columns:1fr 1fr}.bottom{gap:12px;flex-direction:column}}@media(max-width:575px){.footer-grid{grid-template-columns:1fr}.bottom{text-align:center}}
  `]
})
export class FooterComponent {}
