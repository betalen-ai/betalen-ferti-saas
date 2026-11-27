import { CommonModule, CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { BillService } from '../core/bill.service';
import { FarmerService } from '../core/farmer.service';
import { KhataService } from '../core/khata.service';
import { ProductService } from '../core/product.service';
import { Bill, Farmer, Product } from '../models';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterLink, CurrencyPipe, DecimalPipe],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardPageComponent {
  readonly auth = inject(AuthService);
  readonly billService = inject(BillService);
  readonly farmerService = inject(FarmerService);
  readonly khataService = inject(KhataService);
  readonly productService = inject(ProductService);

  readonly dayPart = new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening';
  get ownerName(): string { return this.auth.profile()?.name ?? 'shop owner'; }

  readonly totalCredit = computed(() =>
    this.farmerService.farmers().reduce((sum, f) => sum + this.khataService.farmerBalance(f.id), 0)
  );

  readonly farmersWithDues = computed(() =>
    this.farmerService.farmers().filter(f => this.khataService.farmerBalance(f.id) > 0)
  );

  recentBills(): Bill[] {
    return this.billService.bills().slice(0, 5);
  }

  topDues(): Farmer[] {
    return this.farmersWithDues().slice(0, 5);
  }

  farmerDisplayName(id: string): string {
    return this.farmerService.farmers().find(f => f.id === id)?.name ?? 'Walk-in customer';
  }

  baseUnitOf(product: Product): string {
    if (product.unit_type === 'Liquid' || product.unit_type === 'L') return 'L';
    if (product.unit_type === 'Item' || product.unit_type === 'piece') return 'piece';
    return 'kg';
  }

  trackById(_: number, item: { id: string }): string { return item.id; }
  trackByProduct(_: number, product: Product): string { return product.id; }
}
