import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Pack, PackCreate, PackUpdate, ProductPackInput } from '../models';

@Injectable({ providedIn: 'root' })
export class PackService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly packs = signal<Pack[]>([]);

  async refreshPacks(query: PageQuery & { product_id?: string } = {}): Promise<Pack[]> {
    const rows = await firstValueFrom(this.api.get<Pack[]>(this.helper.url('/packs', query)));
    this.packs.set(rows);
    return rows;
  }

  async createPack(input: ProductPackInput & { product_id: string }): Promise<Pack> {
    const payload = this.helper.withTenant<PackCreate>({
      product_id: input.product_id,
      size: input.size,
      size_unit: input.unit,
      size_in_base_unit: this.helper.toBase(input.size, input.unit),
      mrp: input.mrp,
      cash_price: input.cashPrice || input.mrp,
      credit_price: input.creditPrice || input.cashPrice || input.mrp,
      allow_loose_sale: input.looseAllowed,
      active: true,
    });
    const created = await firstValueFrom(this.api.post<Pack>(`${SHOP_API_BASE}/packs`, payload));
    this.packs.update(items => [...items, created]);
    return created;
  }

  async updatePack(packId: string, input: ProductPackInput): Promise<Pack> {
    const payload = this.helper.withTenant<PackUpdate>({
      mrp: input.mrp,
      cash_price: input.cashPrice || input.mrp,
      credit_price: input.creditPrice || input.cashPrice || input.mrp,
      allow_loose_sale: input.looseAllowed,
    });
    const updated = await firstValueFrom(this.api.patch<Pack>(`${SHOP_API_BASE}/packs/${packId}`, payload));
    this.packs.update(items => items.map(p => p.id === packId ? updated : p));
    return updated;
  }

  reset(): void {
    this.packs.set([]);
  }
}
