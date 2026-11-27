import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Brand, BrandCreate, BrandUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class BrandService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly brands = signal<Brand[]>([]);

  async refreshBrands(query: PageQuery = {}): Promise<Brand[]> {
    const rows = await firstValueFrom(this.api.get<Brand[]>(this.helper.url('/brands', query)));
    this.brands.set(rows);
    return rows;
  }

  async addBrand(name: string, manufacturer: string, notes: string): Promise<Brand> {
    if (!name.trim()) throw new Error('Enter a brand name.');
    const payload = this.helper.withTenant<BrandCreate>({
      name: name.trim(),
      manufacturer: manufacturer.trim(),
      notes: notes.trim(),
      active: true,
    });
    const created = await firstValueFrom(this.api.post<Brand>(`${SHOP_API_BASE}/brands`, payload));
    this.brands.update(items => [...items, created]);
    return created;
  }

  async updateBrand(id: string, name: string, manufacturer: string, notes: string): Promise<Brand> {
    const payload = this.helper.withTenant<BrandUpdate>({
      name: name.trim(),
      manufacturer: manufacturer.trim(),
      notes: notes.trim(),
    });
    const updated = await firstValueFrom(this.api.patch<Brand>(`${SHOP_API_BASE}/brands/${id}`, payload));
    this.brands.update(items => items.map(b => b.id === id ? updated : b));
    return updated;
  }

  async deactivateBrand(id: string): Promise<void> {
    const updated = await firstValueFrom(
      this.api.patch<Brand>(`${SHOP_API_BASE}/brands/${id}`, this.helper.withTenant<BrandUpdate>({ active: false }))
    );
    this.brands.update(items => items.map(b => b.id === id ? updated : b));
  }

  brandName(id: string): string {
    return this.brands().find(item => item.id === id)?.name ?? 'Unknown brand';
  }

  reset(): void {
    this.brands.set([]);
  }
}
