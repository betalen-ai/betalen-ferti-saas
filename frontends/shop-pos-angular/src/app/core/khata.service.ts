import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, ShopApiHelper } from './shop-api.helper';
import { KhataEntry } from '../models';

@Injectable({ providedIn: 'root' })
export class KhataService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly khataEntries = signal<KhataEntry[]>([]);

  async refreshKhata(query: PageQuery & { farmer_id?: string; bill_id?: string } = {}): Promise<KhataEntry[]> {
    const rows = await firstValueFrom(this.api.get<KhataEntry[]>(this.helper.url('/khata', query)));
    this.khataEntries.set(rows);
    return rows;
  }

  farmerBalance(farmerId: string): number {
    return this.khataEntries()
      .filter(e => e.farmer_id === farmerId)
      .reduce((bal, e) => bal + (e.debit > 0 ? e.debit : -e.credit), 0);
  }

  appendLedgerLocal(
    farmerId: string,
    description: string,
    amount: number,
    direction: 'debit' | 'credit',
    note: string
  ): void {
    const balanceAfter = this.farmerBalance(farmerId) + (direction === 'debit' ? amount : -amount);
    this.khataEntries.update(items => [...items, {
      id: this.helper.id('entry'),
      tenant_id: this.helper.tenantId ?? '',
      created_at: this.helper.nowIso(),
      updated_at: this.helper.nowIso(),
      version: 1,
      farmer_id: farmerId,
      bill_id: null,
      payment_id: null,
      entry_type: direction,
      debit: direction === 'debit' ? amount : 0,
      credit: direction === 'credit' ? amount : 0,
      description,
      reverses_entry_id: null,
      date: this.helper.today(),
      billNumber: note.startsWith('F-') ? note : '',
      direction,
      amount,
      balanceAfter,
      note,
    }]);
  }

  reset(): void {
    this.khataEntries.set([]);
  }
}
