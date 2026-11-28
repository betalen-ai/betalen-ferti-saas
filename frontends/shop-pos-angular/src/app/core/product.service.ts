import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PackService } from './pack.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Pack, Product, ProductCreate, ProductPackInput, ProductUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class ProductService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);
  private packService = inject(PackService);

  readonly products = signal<Product[]>([]);

  readonly lowStockProducts = computed(() =>
    this.products().filter(p => p.active && this.totalStock(p) <= p.low_stock_level)
  );

  async refreshProducts(query: PageQuery = {}): Promise<Product[]> {
    const rows = await firstValueFrom(this.api.get<Product[]>(this.helper.url('/products', query)));
    this.products.set(rows);
    return rows;
  }

  async addProduct(input: Omit<ProductCreate, 'packs'>, packs: ProductPackInput[]): Promise<Product> {
    if (!packs.length) throw new Error('Add at least one product pack.');
    const product = await firstValueFrom(
      this.api.post<Product>(`${SHOP_API_BASE}/products`, this.helper.withTenant(input))
    );
    const prepared = await Promise.all(
      packs.map(p => this.packService.createPack({ ...p, product_id: product.id }))
    );
    const withPacks: Product = { ...product, packs: prepared };
    this.products.update(items => [...items, withPacks]);
    return withPacks;
  }

  async updateProduct(id: string, input: Partial<ProductCreate>, packs: ProductPackInput[]): Promise<Product> {
    if (!packs.length) throw new Error('Add at least one product pack.');
    const updated = await firstValueFrom(
      this.api.patch<Product>(`${SHOP_API_BASE}/products/${id}`, this.helper.withTenant<ProductUpdate>({ ...input }))
    );
    const existingPacks = this.product(id)?.packs ?? [];
    const prepared: Pack[] = [];
    for (let i = 0; i < packs.length; i++) {
      const prev = existingPacks[i];
      if (prev) {
        prepared.push(await this.packService.updatePack(prev.id, packs[i]));
      } else {
        prepared.push(await this.packService.createPack({ ...packs[i], product_id: id }));
      }
    }
    const result: Product = { ...updated, packs: prepared };
    this.products.update(items => items.map(p => p.id === id ? result : p));
    return result;
  }

  async deactivateProduct(id: string): Promise<void> {
    const updated = await firstValueFrom(
      this.api.patch<Product>(`${SHOP_API_BASE}/products/${id}`, this.helper.withTenant<ProductUpdate>({ active: false }))
    );
    this.products.update(items => items.map(p => p.id === id ? updated : p));
  }

  product(id: string): Product | undefined {
    return this.products().find(item => item.id === id);
  }

  totalStock(product: Product): number {
    const stockBase = product.stockBase;
    if (!stockBase) return 0;
    return Object.values<number>(stockBase).reduce((sum: number, amt: number) => sum + Number(amt ?? 0), 0);
  }

  stockInPacks(product: Product, pack: Pack): number {
    return (product.stockBase?.[pack.id] ?? 0) / pack.size_in_base_unit;
  }

  reset(): void {
    this.products.set([]);
  }
}
