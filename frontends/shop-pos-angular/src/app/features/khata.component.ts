import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { BillService } from '../core/bill.service';
import { FarmerService } from '../core/farmer.service';
import { KhataService } from '../core/khata.service';
import { NoticeService } from '../core/notice.service';
import { SeasonService } from '../core/season.service';
import { Farmer, KhataEntry } from '../models';

@Component({
  selector: 'app-khata-page',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyPipe, DatePipe],
  templateUrl: './khata.component.html',
  styleUrls: ['./khata.component.scss'],
})
export class KhataPageComponent {
  readonly khataService = inject(KhataService);
  readonly farmerService = inject(FarmerService);
  private readonly billService = inject(BillService);
  private readonly seasonService = inject(SeasonService);
  private readonly notice = inject(NoticeService);
  private readonly route = inject(ActivatedRoute);

  paymentFarmerId = this.route.snapshot.queryParamMap.get('farmer') ?? '';
  paymentAmount = 0;
  khataPaymentMode = 'Cash';
  paymentNote = '';
  ledgerFarmerId = this.route.snapshot.queryParamMap.get('farmer') ?? '';
  feedback = '';

  readonly farmersWithDues = computed(() =>
    this.farmerService.farmers().filter(f => this.khataService.farmerBalance(f.id) > 0)
  );

  selectedFarmer(): Farmer | undefined {
    return this.farmerService.farmers().find(f => f.id === this.paymentFarmerId);
  }

  selectedFarmerBalance(): number {
    return this.paymentFarmerId ? this.khataService.farmerBalance(this.paymentFarmerId) : 0;
  }

  get canReceivePayment(): boolean {
    return !!this.paymentFarmerId && this.paymentAmount > 0;
  }

  payFullBalance(): void {
    const balance = this.selectedFarmerBalance();
    if (balance > 0) this.paymentAmount = balance;
  }

  async receivePayment(): Promise<void> {
    this.feedback = '';
    try {
      await this.billService.receivePayment(
        this.paymentFarmerId, this.paymentAmount, this.khataPaymentMode, this.paymentNote
      );
      this.notice.show('Payment received and allocated to oldest unpaid bills.');
      this.paymentAmount = 0;
      this.paymentNote = '';
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not receive payment.';
    }
  }

  selectPaymentFarmer(id: string): void {
    this.paymentFarmerId = id;
    document.querySelector('.form-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  filteredLedger(): KhataEntry[] {
    return this.khataService.khataEntries().filter(e => !this.ledgerFarmerId || e.farmer_id === this.ledgerFarmerId);
  }

  farmerDisplayName(id: string): string {
    return this.farmerService.farmers().find(f => f.id === id)?.name ?? 'Walk-in customer';
  }

  farmerOverdue(farmerId: string): boolean {
    const grace = Math.max(0, ...this.seasonService.seasons().map(s => s.grace_days));
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - grace);
    return this.billService.bills().some(
      b => b.farmer_id === farmerId && b.balance > 0 && !!b.due_date && new Date(`${b.due_date}T00:00:00`) < cutoff
    );
  }

  lastPayment(id: string): string | null {
    const entry = this.khataService.khataEntries().find(e => e.farmer_id === id && e.description.startsWith('Payment'));
    return entry ? (entry.date ?? entry.created_at) : null;
  }

  printLedger(): void { window.print(); }
  sendReminder(): void { this.notice.show('Reminder sharing can be connected when WhatsApp integration is available.'); }

  trackById(_: number, item: { id: string }): string { return item.id; }
  trackByEntry(_: number, entry: KhataEntry): string { return entry.id; }
}
