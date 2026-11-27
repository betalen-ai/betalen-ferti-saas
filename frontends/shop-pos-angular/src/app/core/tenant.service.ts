import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { SubscriptionService } from './subscription.service';
import { Tenant } from '../models/tenant.model';


@Injectable({ providedIn: 'root' })
export class TenantService {
  private api = inject(ApiService);
  private subscription = inject(SubscriptionService);

  readonly tenant = signal<Tenant | null>(null);
  readonly name = computed(() => this.tenant()?.name ?? '');

  /** Plan label comes from the live subscription, not from stored data. */
  readonly planLabel = computed(() => {
    switch (this.subscription.status()) {
      case 'TRIAL': return 'Free trial';
      case 'ACTIVE': return 'Subscribed';
      case 'GRACE': return 'Renewal due';
      case 'EXPIRED': return 'Expired';
      default: return '';
    }
  });

  /** GET /tenants/me returns TenantOut. Adjust the path if your route differs. */
  load(): void {
    this.api.get<any>('/tenants/me').subscribe({
      next: t => this.tenant.set({ id: t.id, name: t.name, gstin: t.gstin ?? '', status: t.status }),
      error: () => { /* the header falls back to an empty name */ },
    });
  }

  updateName(name: string): void {
    const t = this.tenant();
    if (t && name.trim()) this.tenant.set({ ...t, name: name.trim() });
  }

  reset(): void { this.tenant.set(null); }
}