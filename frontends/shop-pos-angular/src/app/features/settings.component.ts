import { CommonModule } from '@angular/common';
import { Component, effect, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NoticeService } from '../core/notice.service';
import { SettingsService } from '../core/settings.service';
import { TenantService } from '../core/tenant.service';

@Component({
  selector: 'app-settings-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss'],
})
export class SettingsPageComponent {
  private readonly settingsService = inject(SettingsService);
  private readonly tenant = inject(TenantService);
  private readonly notice = inject(NoticeService);

  settingsShopName = this.tenant.name();
  settingsGstin = this.tenant.tenant()?.gstin ?? '';
  settingsAddress = String(this.settingsService.settings()?.values?.['address'] ?? '');
  taxExclusive = Boolean(this.settingsService.settings()?.values?.['tax_exclusive'] ?? false);
  feedback = '';

  constructor() {
    effect(() => {
      const t = this.tenant.tenant();
      if (t) {
        if (!this.settingsShopName) this.settingsShopName = t.name;
        if (!this.settingsGstin) this.settingsGstin = t.gstin;
      }
      const s = this.settingsService.settings()?.values;
      if (s) {
        if (!this.settingsAddress && s['address']) this.settingsAddress = String(s['address']);
        if (typeof s['tax_exclusive'] === 'boolean') this.taxExclusive = s['tax_exclusive'];
      }
    });
  }

  async saveSettings(): Promise<void> {
    this.feedback = '';
    if (!this.settingsShopName.trim()) {
      this.feedback = 'Shop name cannot be empty.';
      return;
    }
    try {
      this.tenant.updateName(this.settingsShopName);
      await this.settingsService.saveSettings({
        ...(this.settingsService.settings()?.values ?? {}),
        shop_name: this.settingsShopName.trim(),
        gstin: this.settingsGstin.trim(),
        address: this.settingsAddress.trim(),
        tax_exclusive: this.taxExclusive,
      });
      this.notice.show('Shop profile saved.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save settings.';
    }
  }
}
