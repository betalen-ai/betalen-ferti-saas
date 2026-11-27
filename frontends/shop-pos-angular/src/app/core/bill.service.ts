import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiService } from './api.service';
import { FarmerService } from './farmer.service';
import { KhataService } from './khata.service';
import { ProductService } from './product.service';
import { PageQuery, ShopApiHelper } from './shop-api.helper';
import { allocatePayment, calcCreditTotal, calcSpotTotal, UnpaidBill } from '../utils/interest.util';
import { Bill, BillLine, PaymentType } from '../models';

export interface SaveBillInput {
  farmerId: string | null;
  seasonId: string | null;
  paymentType: PaymentType;
  paymentMode: 'cash' | 'UPI' | 'card' | 'credit';
  lines: BillLine[];
  discount: number;
  discountType: 'amount' | 'percent';
  interestPct: number;
  months: number;
  paidNow: number;
  dueDate: string | null;
  taxExclusive: boolean;
  hold?: boolean;
}

@Injectable({ providedIn: 'root' })
export class BillService {
  private api = inject(ApiService);
  private helper = inject(ShopApiHelper);
  private farmerService = inject(FarmerService);
  private productService = inject(ProductService);
  private khataService = inject(KhataService);

  readonly bills = signal<Bill[]>([]);

  readonly todaySales = computed(() =>
    this.bills()
      .filter(b => b.bill_date === this.helper.today() && b.status !== 'void' && b.status !== 'held')
      .reduce((sum, b) => sum + b.total, 0)
  );

  readonly cashInHand = computed(() =>
    this.bills()
      .filter(b => b.bill_date === this.helper.today() && b.status !== 'void' && b.status !== 'held')
      .reduce((sum, b) => sum + b.paid_now, 0)
  );

  async refreshBills(query: PageQuery = {}): Promise<Bill[]> {
    const rows = await firstValueFrom(this.api.get<Bill[]>(this.helper.url('/bills', query)));
    this.bills.set(rows);
    return rows;
  }

  async getBillItems(billId: string): Promise<BillLine[]> {
    return firstValueFrom(this.api.get<BillLine[]>(this.helper.url(`/bills/${billId}/items`)));
  }

  async saveBill(input: SaveBillInput): Promise<Bill> {
    if (!input.lines.length) throw new Error('Add at least one item to the bill.');
    if (input.paymentType !== 'cash' && !input.farmerId) {
      throw new Error('Choose a farmer before adding a sale to khata.');
    }
    const subtotal = input.lines.reduce((sum, line) => sum + line.line_total, 0);
    const discount = input.paymentType === 'cash'
      ? subtotal - calcSpotTotal(subtotal, input.discount, input.discountType)
      : 0;
    const netSubtotal = subtotal - discount;

    let taxableValue = 0;
    let taxAmount = 0;
    for (const line of input.lines) {
      const netLine = subtotal > 0 ? netSubtotal * line.line_total / subtotal : 0;
      const rate = Math.max(0, line.gstPercent ?? 0);
      if (input.taxExclusive) {
        taxableValue += netLine;
        taxAmount += netLine * rate / 100;
      } else {
        const inclusiveTax = rate > 0 ? netLine * rate / (100 + rate) : 0;
        taxableValue += netLine - inclusiveTax;
        taxAmount += inclusiveTax;
      }
    }
    taxableValue = Math.round(taxableValue * 100) / 100;
    const cgst = Math.round(taxAmount * 50) / 100;
    const sgst = Math.round(taxAmount * 50) / 100;
    const principalTotal = netSubtotal + (input.taxExclusive ? cgst + sgst : 0);
    const due = input.paymentType === 'credit' || input.paymentType === 'part'
      ? calcCreditTotal(principalTotal, input.interestPct, input.months, input.paymentType === 'part' ? input.paidNow : 0)
      : { principal: 0, interest: 0, total: Math.round(principalTotal), balance: 0 };
    const total = input.paymentType === 'cash' ? Math.round(principalTotal) : due.total;
    const paidNow = input.hold
      ? 0
      : input.paymentType === 'cash'
        ? total
        : input.paymentType === 'credit'
          ? 0
          : Math.min(total, Math.max(0, input.paidNow));
    const balance = input.hold ? 0 : Math.max(0, total - paidNow);
    const billNumber = `F-${String(this.bills().length + 1).padStart(5, '0')}`;
    const farmer = input.farmerId ? this.farmerService.farmers().find(item => item.id === input.farmerId) : undefined;

    if (farmer && farmer.creditLimit != null && this.khataService.farmerBalance(farmer.id) + balance > farmer.creditLimit) {
      throw new Error(`${farmer.name}'s credit limit would be exceeded.`);
    }

    const bill: Bill = {
      id: this.helper.id('bill'),
      tenant_id: this.helper.tenantId ?? '',
      created_at: this.helper.nowIso(),
      updated_at: this.helper.nowIso(),
      version: 1,
      bill_number: billNumber,
      bill_date: this.helper.today(),
      farmer_id: input.farmerId ?? '',
      season_id: input.seasonId,
      payment_type: input.paymentType,
      subtotal,
      discount,
      interest_amount: due.interest,
      gst_amount: cgst + sgst,
      round_off: 0,
      total,
      paid_now: paidNow,
      balance,
      status: input.hold ? 'held' : balance === 0 ? 'paid' : paidNow > 0 ? 'part-paid' : 'credit',
      terms: null,
      due_date: balance > 0 ? input.dueDate : null,
      farmerName: farmer?.name ?? 'Walk-in customer',
      paymentMode: input.paymentMode,
      lines: input.lines,
      interestPct: input.interestPct,
      months: input.months,
      principalBalance: balance > 0 ? Math.max(0, principalTotal - (input.paymentType === 'part' ? paidNow : 0)) : 0,
      interestBalance: balance > 0 ? due.interest : 0,
      taxableValue,
      cgst,
      sgst,
    };

    for (const line of input.lines) {
      const product = this.productService.product(line.productId ?? '');
      if (!product) continue;
      const available = product.stockBase?.[line.pack_id] ?? 0;
      if (available - line.quantity_base < 0) throw new Error(`${line.product_name} does not have enough stock.`);
    }

    this.bills.update(items => [bill, ...items]);
    if (farmer && !input.hold && balance > 0) {
      const principal = Math.max(0, principalTotal - paidNow);
      if (principal > 0) this.khataService.appendLedgerLocal(farmer.id, `Credit sale ${billNumber}`, principal, 'debit', billNumber);
      if (due.interest > 0) this.khataService.appendLedgerLocal(farmer.id, `Interest ${billNumber}`, due.interest, 'debit', billNumber);
      if (paidNow > 0) this.khataService.appendLedgerLocal(farmer.id, `Payment on ${billNumber}`, paidNow, 'credit', billNumber);
    }
    return bill;
  }

  async voidBill(id: string, reason: string): Promise<void> {
    const bill = this.bills().find(item => item.id === id);
    if (!bill) throw new Error('Bill not found.');
    if (bill.status === 'void') throw new Error('This bill is already void.');
    if (!reason.trim()) throw new Error('Enter a reason to void this bill.');
    if (bill.status !== 'held' && (bill.payment_type === 'cash' || bill.paid_now > 0 || bill.balance < bill.total)) {
      throw new Error('A paid or partially paid bill cannot be voided. Record a return or refund instead.');
    }
    this.bills.update(items => items.map(item => item.id === id
      ? { ...item, status: 'void', balance: 0, principalBalance: 0, interestBalance: 0 }
      : item));
  }

  async receivePayment(farmerId: string, amount: number, mode: string, note: string): Promise<void> {
    if (amount <= 0) throw new Error('Enter a payment amount greater than zero.');
    const farmer = this.farmerService.farmers().find(item => item.id === farmerId);
    if (!farmer) throw new Error('Choose a farmer to receive payment from.');
    const bills = this.bills().filter(bill => bill.farmer_id === farmerId && bill.balance > 0);
    const allocations = allocatePayment(amount, bills.map(bill => this.unpaidBill(bill)));
    this.bills.update(items => items.map(bill => {
      const allocation = allocations.find(a => a.billId === bill.id);
      if (!allocation) return bill;
      const interestBalance = Math.max(0, (bill.interestBalance ?? 0) - allocation.interestPaid);
      const principalBalance = Math.max(0, (bill.principalBalance ?? 0) - allocation.principalPaid);
      const balance = interestBalance + principalBalance;
      return {
        ...bill,
        balance,
        interestBalance,
        principalBalance,
        status: balance === 0 ? 'paid' as const : 'part-paid' as const,
      };
    }));
    this.khataService.appendLedgerLocal(farmerId, `Payment received (${mode})`, amount, 'credit', note);
  }

  private unpaidBill(bill: Bill): UnpaidBill {
    return {
      billId: bill.id,
      date: bill.bill_date,
      interestDue: bill.interestBalance ?? 0,
      principalDue: bill.principalBalance ?? 0,
    };
  }

  reset(): void {
    this.bills.set([]);
  }
}
