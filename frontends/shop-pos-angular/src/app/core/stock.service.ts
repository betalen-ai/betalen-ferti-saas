import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import {
  StockEntry, StockLot, StockLotCreate, StockLotUpdate, StockMovement, StockMovementCreate,
} from '../models';

@Injectable({ providedIn: 'root' })
export class StockService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly stockLots = signal<StockLot[]>([]);
  readonly stockMovements = signal<StockMovement[]>([]);
  readonly stockLedger = signal<StockEntry[]>([]);

  async refreshStockLots(
    query: PageQuery & { pack_id?: string; in_stock_only?: boolean; expiring_before?: string } = {}
  ): Promise<StockLot[]> {
    const rows = await firstValueFrom(this.api.get<StockLot[]>(this.helper.url('/stock-lots', query)));
    this.stockLots.set(rows);
    return rows;
  }

  async createStockLot(input: StockLotCreate): Promise<StockLot> {
    const created = await firstValueFrom(
      this.api.post<StockLot>(`${SHOP_API_BASE}/stock-lots`, this.helper.withTenant(input))
    );
    this.stockLots.update(items => [...items, created]);
    return created;
  }

  async updateStockLot(id: string, input: StockLotUpdate): Promise<StockLot> {
    const updated = await firstValueFrom(
      this.api.patch<StockLot>(`${SHOP_API_BASE}/stock-lots/${id}`, this.helper.withTenant(input))
    );
    this.stockLots.update(items => items.map(l => l.id === id ? updated : l));
    return updated;
  }

  async refreshStockMovements(
    query: PageQuery & { pack_id?: string; stock_lot_id?: string } = {}
  ): Promise<StockMovement[]> {
    const rows = await firstValueFrom(this.api.get<StockMovement[]>(this.helper.url('/stock-movements', query)));
    this.stockMovements.set(rows);
    return rows;
  }

  async createStockMovement(input: StockMovementCreate): Promise<StockMovement> {
    const created = await firstValueFrom(
      this.api.post<StockMovement>(`${SHOP_API_BASE}/stock-movements`, this.helper.withTenant(input))
    );
    this.stockMovements.update(items => [created, ...items]);
    return created;
  }

  async stockIn(
    packId: string,
    quantityBase: number,
    supplier: string,
    batchNo: string,
    expiryDate: string,
    costPrice: number
  ): Promise<StockLot> {
    if (quantityBase <= 0) throw new Error('Enter a quantity greater than zero.');
    return this.createStockLot({
      pack_id: packId,
      supplier: supplier || null,
      received_date: this.helper.today(),
      quantity_base: quantityBase,
      cost_price: costPrice,
      batch_number: batchNo || null,
      expiry_date: expiryDate || null,
    });
  }

  async adjustStock(lotId: string, quantityBase: number, reason: string): Promise<StockMovement> {
    if (quantityBase === 0 || !reason.trim()) throw new Error('Enter a quantity and a reason.');
    return this.createStockMovement({
      stock_lot_id: lotId,
      movement_type: 'adjustment',
      quantity_base: quantityBase,
      reason: reason.trim(),
    });
  }

  reset(): void {
    this.stockLots.set([]);
    this.stockMovements.set([]);
    this.stockLedger.set([]);
  }
}
