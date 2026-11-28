import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { KhataService } from './khata.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Farmer, FarmerCreate, FarmerUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class FarmerService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);
  private khata = inject(KhataService);

  readonly farmers = signal<Farmer[]>([]);

  async refreshFarmers(query: PageQuery = {}): Promise<Farmer[]> {
    const rows = await firstValueFrom(this.api.get<Farmer[]>(this.helper.url('/farmers', query)));
    this.farmers.set(rows);
    return rows;
  }

  async addFarmer(input: FarmerCreate): Promise<Farmer> {
    if (this.farmers().some(f => f.mobile === input.mobile.trim())) {
      throw new Error('A farmer with this mobile number already exists.');
    }
    const payload = this.helper.withTenant<FarmerCreate>({ ...input, mobile: input.mobile.trim() });
    const created = await firstValueFrom(this.api.post<Farmer>(`${SHOP_API_BASE}/farmers`, payload));
    this.farmers.update(items => [...items, created]);
    if (created.opening_balance !== 0) {
      this.khata.appendLedgerLocal(
        created.id,
        'Opening balance',
        Math.abs(created.opening_balance),
        created.opening_balance > 0 ? 'debit' : 'credit',
        ''
      );
    }
    return created;
  }

  async updateFarmer(id: string, input: FarmerUpdate): Promise<Farmer> {
    const updated = await firstValueFrom(
      this.api.patch<Farmer>(`${SHOP_API_BASE}/farmers/${id}`, this.helper.withTenant(input))
    );
    this.farmers.update(items => items.map(f => f.id === id ? updated : f));
    return updated;
  }

  reset(): void {
    this.farmers.set([]);
  }
}
