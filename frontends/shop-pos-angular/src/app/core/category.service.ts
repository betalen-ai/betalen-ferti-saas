import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Category, CategoryCreate, CategoryUpdate, ProductType } from '../models';

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly categories = signal<Category[]>([]);

  async refreshCategories(query: PageQuery = {}): Promise<Category[]> {
    const rows = await firstValueFrom(this.api.get<Category[]>(this.helper.url('/categories', query)));
    this.categories.set(rows);
    return rows;
  }

  async addCategory(name: string, productType: ProductType, _gstPercent: number): Promise<Category> {
    if (!name.trim()) throw new Error('Enter a category name.');
    const payload = this.helper.withTenant<CategoryCreate>({
      name: name.trim(),
      product_type: productType,
      active: true,
    });
    const created = await firstValueFrom(this.api.post<Category>(`${SHOP_API_BASE}/categories`, payload));
    this.categories.update(items => [...items, created]);
    return created;
  }

  async updateCategory(id: string, name: string, productType: ProductType, _gstPercent: number): Promise<Category> {
    if (!name.trim()) throw new Error('Enter a category name.');
    const payload = this.helper.withTenant<CategoryUpdate>({
      name: name.trim(),
      product_type: productType,
    });
    const updated = await firstValueFrom(this.api.patch<Category>(`${SHOP_API_BASE}/categories/${id}`, payload));
    this.categories.update(items => items.map(c => c.id === id ? updated : c));
    return updated;
  }

  async deactivateCategory(id: string): Promise<void> {
    const updated = await firstValueFrom(
      this.api.patch<Category>(`${SHOP_API_BASE}/categories/${id}`, this.helper.withTenant<CategoryUpdate>({ active: false }))
    );
    this.categories.update(items => items.map(c => c.id === id ? updated : c));
  }

  categoryName(id: string): string {
    return this.categories().find(item => item.id === id)?.name ?? 'Uncategorised';
  }

  reset(): void {
    this.categories.set([]);
  }
}
