import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { BillService } from '../core/bill.service';
import { FarmerService } from '../core/farmer.service';
import { KhataService } from '../core/khata.service';
import { NoticeService } from '../core/notice.service';
import { SeasonService } from '../core/season.service';
import { Farmer } from '../models';

@Component({
  selector: 'app-farmers-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CurrencyPipe, DatePipe],
  templateUrl: './farmers.component.html',
  styleUrls: ['./farmers.component.scss'],
})
export class FarmersPageComponent {
  readonly farmerService = inject(FarmerService);
  readonly khataService = inject(KhataService);
  private readonly billService = inject(BillService);
  private readonly seasonService = inject(SeasonService);
  private readonly notice = inject(NoticeService);

  farmerName = '';
  farmerMobile = '';
  farmerVillage = '';
  farmerAddress = '';
  farmerLand: number | null = null;
  farmerCreditLimit: number | null = null;
  farmerOpening = 0;
  farmerNotes = '';
  farmerSearch = '';
  duesOnly = false;
  overdueOnly = false;
  feedback = '';

  get validMobile(): boolean {
    return /^[6-9]\d{9}$/.test(this.farmerMobile.trim());
  }

  get duplicateMobile(): boolean {
    const mobile = this.farmerMobile.trim();
    return !!mobile && this.farmerService.farmers().some(f => f.mobile === mobile);
  }

  get canSaveFarmer(): boolean {
    return !!this.farmerName.trim() && this.validMobile && !this.duplicateMobile;
  }

  async saveFarmer(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.farmerName.trim() || !this.validMobile) {
        throw new Error('Enter a farmer name and valid 10-digit mobile number.');
      }
      await this.farmerService.addFarmer({
        name: this.farmerName.trim(),
        mobile: this.farmerMobile.trim(),
        village: this.farmerVillage.trim() || null,
        address: this.farmerAddress.trim() || null,
        opening_balance: this.farmerOpening,
        active: true,
      });
      this.farmerName = '';
      this.farmerMobile = '';
      this.farmerVillage = '';
      this.farmerAddress = '';
      this.farmerLand = null;
      this.farmerCreditLimit = null;
      this.farmerOpening = 0;
      this.farmerNotes = '';
      this.notice.show('Farmer added.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not add farmer.';
    }
  }

  filteredFarmers(): Farmer[] {
    const query = this.farmerSearch.trim().toLowerCase();
    return this.farmerService.farmers().filter(farmer =>
      (!query || `${farmer.name} ${farmer.mobile} ${farmer.village ?? ''}`.toLowerCase().includes(query))
      && (!this.duesOnly || this.khataService.farmerBalance(farmer.id) > 0)
      && (!this.overdueOnly || this.farmerOverdue(farmer.id))
    );
  }

  farmerOverdue(farmerId: string): boolean {
    const grace = Math.max(0, ...this.seasonService.seasons().map(s => s.grace_days));
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - grace);
    return this.billService.bills().some(
      b => b.farmer_id === farmerId && b.balance > 0 && !!b.due_date && new Date(`${b.due_date}T00:00:00`) < cutoff
    );
  }

  trackById(_: number, farmer: Farmer): string { return farmer.id; }
}
