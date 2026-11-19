import { CommonModule } from '@angular/common';
import { Component, HostListener, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { ShopDataService } from '../core/shop-data.service';
import { TenantService } from '../core/tenant.service';

const navigation = [
  { label: 'Dashboard', route: '/app/dashboard', icon: 'bi-grid-1x2' },
  { label: 'New Sale', route: '/app/pos', icon: 'bi-cart-plus' },
  { label: 'Products', route: '/app/products', icon: 'bi-box-seam' },
  { label: 'Brands', route: '/app/brands', icon: 'bi-tag' },
  { label: 'Stock', route: '/app/stock', icon: 'bi-boxes' },
  { label: 'Farmers', route: '/app/farmers', icon: 'bi-people' },
  { label: 'Khata', route: '/app/khata', icon: 'bi-journal-text' },
  { label: 'Bills', route: '/app/bills', icon: 'bi-receipt' },
  { label: 'Seasons', route: '/app/seasons', icon: 'bi-sun' },
  { label: 'Settings', route: '/app/settings', icon: 'bi-gear' }
];

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  template: `
    <div class="app-frame">
      <header class="topbar">
        <button class="menu-button" type="button" (click)="drawerOpen = !drawerOpen" [attr.aria-expanded]="drawerOpen">
          <i class="bi bi-list"></i><span>Menu</span>
        </button>
        <a class="brand" routerLink="/app/dashboard" aria-label="Ferti+ dashboard">
          <span class="brand-mark"><i class="bi bi-flower1"></i></span>
          <strong>Ferti+</strong>
        </a>
        <label class="global-search">
          <i class="bi bi-search"></i>
          <input type="search" placeholder="Search products, farmers or bills" aria-label="Search">
        </label>
        <div class="top-actions">
          <div class="tenant-chip" [title]="tenantName()">
            <i class="bi bi-shop"></i><span class="tenant-name">{{tenantName()}}</span><span class="plan-badge">Free</span>
          </div>
          <div class="profile-actions">
            <button type="button" class="profile-button" (click)="profileOpen = !profileOpen" [attr.aria-expanded]="profileOpen">
              <span class="avatar">{{profileName().slice(0, 1).toUpperCase()}}</span><span>Account</span><i class="bi bi-chevron-down"></i>
            </button>
            <div class="profile-menu" *ngIf="profileOpen">
              <span class="profile-name">{{profileName()}}</span>
              <a routerLink="/app/settings" (click)="profileOpen = false">Profile and settings</a>
              <button type="button" (click)="signOut()">Sign out</button>
            </div>
          </div>
        </div>
      </header>

      <div class="workspace">
        <button class="scrim" *ngIf="drawerOpen" aria-label="Close navigation" (click)="drawerOpen = false"></button>
        <aside class="sidebar" [class.collapsed]="collapsed" [class.drawer-open]="drawerOpen">
          <div class="sidebar-heading">SHOP</div>
          <a *ngFor="let item of nav" [routerLink]="item.route" routerLinkActive="active" (click)="drawerOpen = false" [title]="collapsed ? item.label : ''">
            <i [class]="'bi ' + item.icon"></i><span>{{item.label}}</span>
          </a>
          <button type="button" class="collapse-button" (click)="collapsed = !collapsed">
            <i [class]="collapsed ? 'bi bi-chevron-double-right' : 'bi bi-chevron-double-left'"></i>
            <span>{{collapsed ? 'Expand menu' : 'Collapse menu'}}</span>
          </button>
        </aside>

        <main class="main-content"><router-outlet></router-outlet></main>
      </div>
      <footer class="statusbar">
        <span><i class="bi bi-circle-fill online"></i> Online</span>
        <span><i class="bi bi-calendar3"></i> Today: {{today}}</span>
        <span><i class="bi bi-cash-stack"></i> Cash drawer: {{cashDrawer() | currency:'INR':'symbol':'1.0-0':'en-IN'}}</span>
        <a routerLink="/app/settings"><i class="bi bi-question-circle"></i> Help & settings</a>
      </footer>
    </div>
  `,
  styles: [`
    :host{display:block;min-height:100vh;min-height:100svh;color:#14211a;font-size:16px}
    .app-frame{min-height:100vh;min-height:100svh;display:grid;grid-template-rows:64px 1fr 40px;background:#f7f7f2}
    .topbar{height:64px;display:flex;align-items:center;gap:20px;padding:0 24px;background:#fff;border-bottom:1.5px solid #cbd5ce;z-index:5}
    .brand{display:flex;align-items:center;gap:10px;color:#14211a;text-decoration:none;font-size:22px;min-width:190px}
    .brand-mark{width:36px;height:36px;border-radius:9px;background:#0b6b3a;color:white;display:grid;place-items:center}
    .brand-mark i{font-size:21px}.global-search{display:flex;align-items:center;gap:10px;max-width:560px;width:100%;margin:auto;border:1.5px solid #cbd5ce;border-radius:10px;padding:0 12px;color:#5c6b62}
    .global-search input{border:0;outline:0;min-width:0;width:100%;height:44px;background:transparent;font:inherit}
    .top-actions{display:flex;align-items:center;gap:16px;margin-left:auto}
    .tenant-chip{display:flex;align-items:center;gap:9px;min-width:0;max-width:310px;padding:7px 10px;border:1.5px solid #cbd5ce;border-radius:9px;background:white}
    .tenant-chip>i{color:#0b6b3a}.tenant-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px;font-weight:700}
    .plan-badge{border-radius:20px;background:#edf7ec;color:#0b6b3a;padding:3px 8px;font-size:14px;font-weight:700}
    .profile-actions{position:relative}.profile-button,.menu-button{height:48px;display:flex;align-items:center;gap:8px;padding:0 8px;border:0;background:transparent;font:inherit;font-weight:700}
    .avatar{width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:#e8f1fb;color:#0b6b3a}
    .profile-menu{position:absolute;z-index:8;right:0;top:52px;min-width:220px;padding:10px;background:white;border:1.5px solid #cbd5ce;border-radius:10px;box-shadow:0 8px 22px #14211a24}
    .profile-menu a,.profile-menu button{display:block;width:100%;padding:10px;text-align:left;border:0;background:none;color:#14211a;text-decoration:none;border-radius:6px}
    .profile-menu a:hover,.profile-menu button:hover{background:#f7f7f2}.profile-name{display:block;padding:8px 10px;font-weight:700}
    .menu-button{display:none}.workspace{display:flex;min-height:0}.sidebar{width:240px;flex:0 0 240px;display:flex;flex-direction:column;gap:6px;padding:18px 12px;background:#fff;border-right:1.5px solid #cbd5ce;transition:width .2s,flex-basis .2s}
    .sidebar-heading{padding:10px 12px 6px;color:#5c6b62;font-size:14px;font-weight:800;letter-spacing:.1em}
    .sidebar>a,.collapse-button{height:56px;display:flex;align-items:center;gap:14px;padding:0 12px;border:1.5px solid transparent;border-radius:9px;color:#26382d;text-decoration:none;font-weight:700;white-space:nowrap}
    .sidebar>a i,.collapse-button i{font-size:23px;width:26px;text-align:center}.sidebar>a.active{background:#edf7ec;color:#0b6b3a;border-color:#cbd5ce}
    .sidebar>a:hover,.collapse-button:hover{background:#f7f7f2}.collapse-button{margin-top:auto;background:white;font:inherit}
    .sidebar.collapsed{width:84px;flex-basis:84px}.sidebar.collapsed .sidebar-heading{display:none}.sidebar.collapsed>a,.sidebar.collapsed .collapse-button{height:64px;flex-direction:column;justify-content:center;gap:2px;padding:2px;text-align:center;white-space:normal;font-size:14px;line-height:16px}.sidebar.collapsed>a i,.sidebar.collapsed .collapse-button i{font-size:22px}
    .main-content{flex:1;min-width:0;padding:24px;overflow:auto}
    .statusbar{height:40px;display:flex;align-items:center;gap:28px;padding:0 20px;background:#fff;border-top:1.5px solid #cbd5ce;color:#46564b;font-size:14px}
    .statusbar span,.statusbar a{display:flex;align-items:center;gap:8px;white-space:nowrap}.statusbar a{color:inherit;text-decoration:none;margin-left:auto}
    .online{font-size:9px;color:#219653}.scrim{display:none}
    @media(max-width:1050px){.global-search{max-width:360px}.tenant-chip{max-width:220px}.tenant-name{max-width:110px}.sidebar{width:208px;flex-basis:208px}}
    @media(max-width:760px){
      .app-frame{grid-template-rows:60px 1fr auto}.topbar{height:60px;padding:0 12px;gap:10px}.menu-button{display:flex;padding:0 4px}.menu-button i{font-size:23px}.brand{min-width:auto;font-size:20px}.brand-mark{width:32px;height:32px}.global-search{display:none}
      .top-actions{gap:6px}.tenant-chip{max-width:42vw;padding:6px;gap:5px}.tenant-name{max-width:23vw}.plan-badge{font-size:12px;padding:2px 6px}.profile-button>span:not(.avatar),.profile-button>.bi-chevron-down{display:none}
      .sidebar,.sidebar.collapsed{position:fixed;z-index:12;top:60px;bottom:40px;left:0;width:min(280px,85vw);flex-basis:auto;transform:translateX(-105%);transition:transform .2s;padding-top:12px;box-shadow:8px 0 24px #14211a22}
      .sidebar.drawer-open{transform:translateX(0)}.sidebar.collapsed>a,.sidebar.collapsed .collapse-button{height:56px;flex-direction:row;justify-content:flex-start;gap:14px;padding:0 12px;text-align:left;font-size:16px;line-height:normal}.sidebar.collapsed .sidebar-heading{display:block}.scrim{display:block;position:fixed;inset:60px 0 40px;z-index:11;border:0;background:#14211a55}
      .main-content{padding:16px 12px}.statusbar{height:auto;min-height:40px;padding:8px 12px;gap:8px 16px;flex-wrap:wrap;font-size:14px}.statusbar span:nth-child(3){display:none}
    }
    @media(max-width:390px){.tenant-chip>i{display:none}.tenant-chip{max-width:39vw}.tenant-name{max-width:25vw}.brand-copy{display:none}}
  `]
})
export class AppShellComponent {
  private readonly auth = inject(AuthService);
  private readonly tenant = inject(TenantService);
  private readonly data = inject(ShopDataService);
  nav = navigation;
  collapsed = false;
  drawerOpen = false;
  profileOpen = false;
  today = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date());
  tenantName = computed(() => this.tenant.tenant().name);
  profileName = computed(() => this.auth.profile()?.name ?? 'Shop owner');
  cashDrawer = this.data.cashInHand;

  @HostListener('document:keydown.escape')
  closeMenus(): void {
    this.drawerOpen = false;
    this.profileOpen = false;
  }

  signOut(): void {
    this.profileOpen = false;
    void this.auth.signOut();
  }
}
