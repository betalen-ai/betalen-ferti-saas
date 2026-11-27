import { CommonModule, CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { BillService } from '../core/bill.service';
import { FarmerService } from '../core/farmer.service';
import { KhataService } from '../core/khata.service';
import { NoticeService } from '../core/notice.service';
import { ProductService } from '../core/product.service';
import { SeasonService } from '../core/season.service';
import { SettingsService } from '../core/settings.service';
import { BillLine, Farmer, Pack, PaymentType, Product } from '../models';
import { calcCreditTotal, calcSpotTotal } from '../utils/interest.util';

@Component({
  selector: 'app-pos-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CurrencyPipe, DecimalPipe],
  templateUrl: './pos.component.html',
  styleUrls: ['./pos.component.scss'],
})
export class PosPageComponent {
  readonly productService = inject(ProductService);
  readonly farmerService = inject(FarmerService);
  readonly seasonService = inject(SeasonService);
  readonly billService = inject(BillService);
  readonly khataService = inject(KhataService);
  readonly settingsService = inject(SettingsService);
  private readonly notice = inject(NoticeService);

  productSearch = '';
  cart: BillLine[] = [];
  farmerId = '';
  seasonId = '';
  paymentType: PaymentType = 'cash';
  discount = 0;
  discountType: 'amount' | 'percent' = 'amount';
  paymentMode: 'cash' | 'UPI' | 'card' | 'credit' = 'cash';
  interestPct = 1;
  months = 1;
  dueDate = '';
  paidNow = 0;
  feedback = '';

  get taxExclusive(): boolean {
    return Boolean(this.settingsService.settings()?.values?.['tax_exclusive'] ?? false);
  }

  // ---- Totals -------------------------------------------------------------
  get subtotal(): number {
    return this.cart.reduce((sum, line) => sum + line.line_total, 0);
  }

  get spotDiscount(): number {
    return this.paymentType === 'cash'
      ? this.subtotal - calcSpotTotal(this.subtotal, this.discount, this.discountType)
      : 0;
  }

  get taxableValue(): number {
    const netSubtotal = this.subtotal - this.spotDiscount;
    return Math.round(this.cart.reduce((sum, line) => {
      const netLine = this.subtotal > 0 ? netSubtotal * line.line_total / this.subtotal : 0;
      const rate = line.gstPercent ?? 0;
      return sum + (this.taxExclusive ? netLine : netLine / (1 + rate / 100));
    }, 0) * 100) / 100;
  }

  get taxAmount(): number {
    const netSubtotal = this.subtotal - this.spotDiscount;
    return Math.round(this.cart.reduce((sum, line) => {
      const netLine = this.subtotal > 0 ? netSubtotal * line.line_total / this.subtotal : 0;
      const rate = line.gstPercent ?? 0;
      return sum + (this.taxExclusive ? netLine * rate / 100 : netLine * rate / (100 + rate));
    }, 0) * 100) / 100;
  }

  get cgst(): number { return Math.round(this.taxAmount / 2 * 100) / 100; }
  get sgst(): number { return this.taxAmount - this.cgst; }
  get principal(): number { return this.subtotal - this.spotDiscount + (this.taxExclusive ? this.taxAmount : 0); }

  get creditInterest(): number {
    if (this.paymentType === 'cash') return 0;
    return calcCreditTotal(this.principal, this.interestPct, this.months, this.paymentType === 'part' ? this.paidNow : 0).interest;
  }

  get total(): number {
    if (this.paymentType === 'cash') return Math.round(this.principal);
    return calcCreditTotal(this.principal, this.interestPct, this.months, this.paymentType === 'part' ? this.paidNow : 0).total;
  }

  get rounding(): number {
    const beforeRounding = this.paymentType === 'cash' ? this.principal : this.principal + this.creditInterest;
    return Math.round(beforeRounding) - beforeRounding;
  }

  get boundedPaidNow(): number { return Math.min(this.total, Math.max(0, this.paidNow)); }
  get balance(): number { return Math.max(0, this.total - (this.paymentType === 'part' ? this.boundedPaidNow : 0)); }

  // ---- Farmer / credit checks ---------------------------------------------
  selectedFarmer(): Farmer | undefined {
    return this.farmerService.farmers().find(f => f.id === this.farmerId);
  }

  farmerOutstanding(): number {
    return this.farmerId ? this.khataService.farmerBalance(this.farmerId) : 0;
  }

  creditLeft(): number | null {
    const limit = this.selectedFarmer()?.creditLimit;
    return limit == null ? null : limit - this.farmerOutstanding();
  }

  get needsFarmer(): boolean { return this.paymentType !== 'cash' && !this.farmerId; }

  get overCreditLimit(): boolean {
    const left = this.creditLeft();
    return this.paymentType !== 'cash' && left !== null && this.balance > left;
  }

  get canSave(): boolean {
    return this.cart.length > 0 && !this.needsFarmer && !this.overCreditLimit;
  }

  // ---- Catalog helpers ----------------------------------------------------
  activeSeasons() { return this.seasonService.seasons().filter(s => s.active !== false); }

  filteredPackOptions() {
    const query = this.productSearch.trim().toLowerCase();
    return this.productService.products()
      .filter(p => p.active)
      .flatMap(product => (product.packs ?? []).map(pack => ({ product, pack })))
      .filter(o => !query || `${o.product.name} ${this.packLabel(o.pack)}`.toLowerCase().includes(query));
  }

  packLabel(pack: Pack): string { return `${pack.size} ${pack.size_unit}`; }

  baseUnitOf(product: Product): string {
    if (product.unit_type === 'Liquid' || product.unit_type === 'L') return 'L';
    if (product.unit_type === 'Item' || product.unit_type === 'piece') return 'piece';
    return 'kg';
  }

  priceOf(pack: Pack): number {
    return this.paymentType === 'credit' ? pack.credit_price : pack.cash_price;
  }

  inStock(product: Product, pack: Pack): boolean {
    return (product.stockBase?.[pack.id] ?? 0) >= pack.size_in_base_unit;
  }

  looseAvailable(product: Product, pack: Pack): boolean {
    return pack.allow_loose_sale && (product.stockBase?.[pack.id] ?? 0) >= 1;
  }

  // ---- Cart actions -------------------------------------------------------
  addToCart(productId: string, packId: string, loose = false): void {
    const product = this.productService.product(productId);
    const pack = product?.packs?.find(p => p.id === packId);
    if (!product || !pack) return;
    const stockBase = product.stockBase?.[pack.id] ?? 0;
    const quantityBase = loose ? 1 : pack.size_in_base_unit;
    const lineLabel = loose ? `Loose ${this.baseUnitOf(product)}` : this.packLabel(pack);
    const existing = this.cart.find(l => l.productId === product.id && l.pack_id === pack.id && l.pack_name === lineLabel);

    if (existing && existing.quantity_base + quantityBase > stockBase) {
      this.feedback = `Not enough ${product.name} stock for another sale.`;
      return;
    }
    if (!existing && quantityBase > stockBase) {
      this.feedback = `${product.name} is out of stock in this pack.`;
      return;
    }
    this.feedback = '';
    const unitPrice = (this.paymentType === 'credit' ? pack.credit_price : pack.cash_price) / (loose ? pack.size_in_base_unit : 1);

    if (existing) {
      existing.quantity++;
      existing.quantity_base += quantityBase;
      existing.line_total = Math.round(existing.line_total + unitPrice);
    } else {
      const now = new Date().toISOString();
      this.cart.push({
        id: '', tenant_id: '', created_at: now, updated_at: now, version: 1,
        bill_id: '', pack_id: packId, product_name: product.name, pack_name: lineLabel,
        quantity: 1, quantity_base: quantityBase, unit_price: unitPrice,
        line_total: Math.round(unitPrice), productId, gstPercent: product.gst_rate,
      });
    }
  }

  paymentChanged(paymentType: PaymentType): void {
    this.paymentType = paymentType;
    for (const line of this.cart) {
      const pack = this.productService.product(line.productId ?? '')?.packs?.find(p => p.id === line.pack_id);
      if (!pack) continue;
      const loose = line.pack_name.startsWith('Loose ');
      line.unit_price = (paymentType === 'credit' ? pack.credit_price : pack.cash_price) / (loose ? pack.size_in_base_unit : 1);
      line.line_total = Math.round(line.unit_price * line.quantity);
    }
  }

  changeCartQuantity(index: number, delta: number): void {
    const line = this.cart[index];
    if (!line) return;
    const product = this.productService.product(line.productId ?? '');
    const pack = product?.packs?.find(p => p.id === line.pack_id);
    if (!pack) return;
    if (delta < 0 && line.quantity <= 1) {
      this.cart.splice(index, 1);
      return;
    }
    const unitBase = line.pack_name.startsWith('Loose ') ? 1 : pack.size_in_base_unit;
    if (delta > 0 && line.quantity_base + unitBase > (product?.stockBase?.[pack.id] ?? 0)) {
      this.feedback = `Not enough ${product?.name ?? 'product'} stock.`;
      return;
    }
    line.quantity += delta;
    line.quantity_base += delta * unitBase;
    line.line_total = Math.round(line.quantity * line.unit_price);
  }

  removeLine(index: number): void { this.cart.splice(index, 1); }

  seasonChanged(id: string): void {
    const season = this.seasonService.seasons().find(s => s.id === id);
    if (!season) return;
    this.interestPct = season.default_credit_interest_per_month;
    this.dueDate = season.due_date ?? '';
    if (season.due_date) {
      const days = (new Date(`${season.due_date}T00:00:00`).getTime() - Date.now()) / 86400000;
      this.months = Math.max(0, Math.round(days / 30 * 10) / 10);
    }
    this.discount = season.default_cash_discount;
    this.discountType = season.discountType ?? 'percent';
  }

  async saveSale(hold = false): Promise<void> {
    this.feedback = '';
    try {
      if (!this.cart.length) throw new Error('Add at least one product to the bill.');
      const bill = await this.billService.saveBill({
        farmerId: this.farmerId || null,
        seasonId: this.seasonId || null,
        paymentType: this.paymentType,
        paymentMode: this.paymentType === 'credit' ? 'credit' : this.paymentMode,
        lines: this.cart.map(line => ({ ...line })),
        discount: this.discount,
        discountType: this.discountType,
        interestPct: this.interestPct,
        months: this.months,
        paidNow: this.boundedPaidNow,
        dueDate: this.dueDate || null,
        taxExclusive: this.taxExclusive,
        hold,
      });
      this.notice.show(hold ? `Bill ${bill.bill_number} held.` : `Bill ${bill.bill_number} saved.`);
      this.clearCart();
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save bill.';
    }
  }

  cancelDraft(): void {
    if (this.cart.length && !confirm('Cancel this unsaved bill and clear its items?')) return;
    this.clearCart();
  }

  clearCart(): void {
    this.cart = [];
    this.discount = 0;
    this.paidNow = 0;
    this.feedback = '';
  }

  trackByIndex(index: number): number { return index; }
  trackByPack(_: number, option: { product: Product; pack: Pack }): string { return option.pack.id; }
  trackById(_: number, item: { id: string }): string { return item.id; }
}
