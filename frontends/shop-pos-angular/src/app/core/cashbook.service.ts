import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Cashbook, CashbookCreate, CashbookUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class CashbookService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  async listCashbook(query: PageQuery = {}): Promise<Cashbook[]> {
    return firstValueFrom(this.api.get<Cashbook[]>(this.helper.url('/cashbook', query)));
  }

  async createCashbook(input: CashbookCreate): Promise<Cashbook> {
    return firstValueFrom(this.api.post<Cashbook>(`${SHOP_API_BASE}/cashbook`, this.helper.withTenant(input)));
  }

  async updateCashbook(id: string, input: CashbookUpdate): Promise<Cashbook> {
    return firstValueFrom(this.api.patch<Cashbook>(`${SHOP_API_BASE}/cashbook/${id}`, this.helper.withTenant(input)));
  }
}
