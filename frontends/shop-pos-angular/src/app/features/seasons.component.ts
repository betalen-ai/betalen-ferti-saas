import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NoticeService } from '../core/notice.service';
import { SeasonService } from '../core/season.service';
import { Season } from '../models';

@Component({
  selector: 'app-seasons-page',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyPipe, DatePipe],
  templateUrl: './seasons.component.html',
  styleUrls: ['./seasons.component.scss'],
})
export class SeasonsPageComponent {
  readonly seasonService = inject(SeasonService);
  private readonly notice = inject(NoticeService);

  showForm = false;
  seasonName = '';
  seasonStart = '';
  seasonEnd = '';
  seasonDiscount = 0;
  seasonDiscountType: 'amount' | 'percent' = 'amount';
  seasonInterest = 1;
  seasonDue = '';
  seasonGrace = 0;
  seasonLateInterest = 1;
  feedback = '';

  openAddForm(): void {
    this.resetSeasonForm();
    this.showForm = true;
  }

  closeForm(): void {
    this.resetSeasonForm();
    this.showForm = false;
  }

  resetSeasonForm(): void {
    this.seasonName = '';
    this.seasonStart = '';
    this.seasonEnd = '';
    this.seasonDiscount = 0;
    this.seasonDiscountType = 'amount';
    this.seasonInterest = 1;
    this.seasonDue = '';
    this.seasonGrace = 0;
    this.seasonLateInterest = 1;
    this.feedback = '';
  }

  async saveSeason(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.seasonName.trim() || !this.seasonStart || !this.seasonEnd || this.seasonEnd < this.seasonStart) {
        this.feedback = 'Enter a name and a valid season date range.';
        return;
      }
      await this.seasonService.addSeason({
        name: this.seasonName.trim(),
        start_date: this.seasonStart,
        end_date: this.seasonEnd,
        default_cash_discount: this.seasonDiscount,
        default_credit_interest_per_month: this.seasonInterest,
        due_date: this.seasonDue || this.seasonEnd,
        grace_days: this.seasonGrace,
        late_interest_per_day: this.seasonLateInterest,
      });
      this.closeForm();
      this.notice.show('Season saved.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save season.';
    }
  }

  async deactivateSeason(id: string): Promise<void> {
    try {
      await this.seasonService.deactivateSeason(id);
      this.notice.show('Season updated.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not update season.';
    }
  }

  trackById(_: number, season: Season): string { return season.id; }
}