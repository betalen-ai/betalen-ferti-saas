import { Injectable, signal } from '@angular/core';

export interface Tenant {
  id: string;
  name: string;
  plan: string;
  gstin: string;
}

@Injectable({ providedIn: 'root' })
export class TenantService {
  readonly tenant = signal<Tenant>({
    id: 'demo-shop',
    name: 'Green Valley Agri Store',
    plan: 'Free',
    gstin: ''
  });

  updateName(name: string): void {
    const tenant = this.tenant();
    this.tenant.set({ ...tenant, name: name.trim() || tenant.name });
  }

  name(): string {
    return this.tenant().name;
  }
}
