import { Injectable, inject } from '@angular/core';
import { TenantService } from './tenant.service';
import { PackUnit } from '../models';

/** Set to '/ferti' if ferti.router is mounted under /ferti, or '' if mounted directly under ApiService's base URL. */
export const SHOP_API_BASE = '';

export interface PageQuery {
  limit?: number;
  offset?: number;
  search?: string;
  q?: string;
  include_inactive?: boolean;
  tenant_id?: string;
}

@Injectable({ providedIn: 'root' })
export class ShopApiHelper {
  private tenant = inject(TenantService);

  get tenantId(): string | undefined {
    return this.tenant.tenant()?.id;
  }

  withTenant<T extends { tenant_id?: string | null }>(payload: T): T {
    const tid = payload.tenant_id ?? this.tenantId;
    return tid ? { ...payload, tenant_id: tid } : payload;
  }

  url(path: string, query: Record<string, any> = {}): string {
    const params = new URLSearchParams();
    const tid = query['tenant_id'] ?? this.tenantId;
    if (tid) params.set('tenant_id', String(tid));

    for (const [k, v] of Object.entries(query)) {
      if (k === 'tenant_id' || v === undefined || v === null || v === '') continue;
      params.set(k === 'search' ? 'q' : k, String(v));
    }
    const qs = params.toString();
    return qs ? `${SHOP_API_BASE}${path}?${qs}` : `${SHOP_API_BASE}${path}`;
  }

  toBase(size: number, unit: PackUnit): number {
    return unit === 'g' || unit === 'ml' ? size / 1000 : size;
  }

  id(prefix: string): string {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  }

  today(): string {
    return new Date().toISOString().slice(0, 10);
  }

  nowIso(): string {
    return new Date().toISOString();
  }
}
