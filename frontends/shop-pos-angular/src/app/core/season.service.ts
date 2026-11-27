import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Season, SeasonCreate, SeasonUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class SeasonService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly seasons = signal<Season[]>([]);

  async refreshSeasons(query: PageQuery = {}): Promise<Season[]> {
    const rows = await firstValueFrom(this.api.get<Season[]>(this.helper.url('/seasons', query)));
    this.seasons.set(rows);
    return rows;
  }

  async addSeason(input: SeasonCreate): Promise<Season> {
    const created = await firstValueFrom(
      this.api.post<Season>(`${SHOP_API_BASE}/seasons`, this.helper.withTenant(input))
    );
    this.seasons.update(items => [...items, created]);
    return created;
  }

  async updateSeason(id: string, input: SeasonUpdate): Promise<Season> {
    const updated = await firstValueFrom(
      this.api.patch<Season>(`${SHOP_API_BASE}/seasons/${id}`, this.helper.withTenant(input))
    );
    this.seasons.update(items => items.map(s => s.id === id ? updated : s));
    return updated;
  }

  async deactivateSeason(id: string): Promise<void> {
    const updated = await firstValueFrom(
      this.api.patch<Season>(`${SHOP_API_BASE}/seasons/${id}`, this.helper.withTenant<SeasonUpdate>({}))
    );
    this.seasons.update(items => items.map(s => s.id === id ? updated : s));
  }

  reset(): void {
    this.seasons.set([]);
  }
}
