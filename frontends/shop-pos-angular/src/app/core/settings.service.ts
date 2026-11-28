import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { PageQuery, SHOP_API_BASE, ShopApiHelper } from './shop-api.helper';
import { Settings, SettingsIn } from '../models';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);

  readonly settings = signal<Settings | null>(null);

  async refreshSettings(query: PageQuery = {}): Promise<Settings | null> {
    try {
      const row = await firstValueFrom(this.api.get<Settings>(this.helper.url('/settings', query)));
      this.settings.set(row);
      return row;
    } catch {
      this.settings.set(null);
      return null;
    }
  }

  async saveSettings(values: Record<string, any>): Promise<Settings> {
    const payload = this.helper.withTenant<SettingsIn>({ values });
    const row = await firstValueFrom(this.api.put<Settings>(`${SHOP_API_BASE}/settings`, payload));
    this.settings.set(row);
    return row;
  }

  reset(): void {
    this.settings.set(null);
  }
}
