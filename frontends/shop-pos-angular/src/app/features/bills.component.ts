import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BillService } from '../core/bill.service';
import { FarmerService } from '../core/farmer.service';
import { NoticeService } from '../core/notice.service';
import { TenantService } from '../core/tenant.service';
import { Bill } from '../models';

@Component({
  selector: 'app-bills-page',
  standalone: true,
  imports: [CommonModule, RouterLink, CurrencyPipe, DatePipe],
  templateUrl: './bills.component.html',
  styleUrls: ['./bills.component.scss'],
})
export class BillsPageComponent {
  readonly billService = inject(BillService);
  private readonly farmerService = inject(FarmerService);
  private readonly tenant = inject(TenantService);
  private readonly notice = inject(NoticeService);

  feedback = '';

  trackById(_: number, bill: Bill): string { return bill.id; }

  customerName(bill: Bill): string {
    return bill.farmerName
      || this.farmerService.farmers().find(f => f.id === bill.farmer_id)?.name
      || 'Walk-in customer';
  }

  canShare(bill: Bill): boolean {
    return bill.status === 'credit' || bill.status === 'part-paid';
  }

  canVoid(bill: Bill): boolean {
    return bill.status === 'held' || (bill.status === 'credit' && bill.payment_type === 'credit' && bill.balance === bill.total);
  }

  print(bill: Bill, format: 'a4' | 'thermal' = 'a4'): void {
    const popup = window.open('', '_blank');
    if (!popup) { this.notice.show('Allow pop-ups to print this invoice.'); return; }
    popup.opener = null;
    const customer = this.customerName(bill);
    const rows = (bill.lines ?? []).map(line =>
      `<tr><td>${this.escapeHtml(line.product_name)}<small>${this.escapeHtml(line.pack_name)}</small></td><td>${line.quantity}</td><td>${this.money(line.unit_price)}</td><td>${this.money(line.line_total)}</td></tr>`
    ).join('');
    popup.document.write(`<!doctype html><html><head><title>${this.escapeHtml(bill.bill_number)}</title><style>
      body{font:14px Arial,sans-serif;color:#14211a;margin:24px}main{max-width:780px;margin:auto}h1{font-size:24px;margin:0}p{margin:5px 0}.header{display:flex;justify-content:space-between;border-bottom:1px solid #bbb;padding-bottom:12px}.meta{margin:16px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid #ccc}th{background:#f4f4f4}small{display:block;color:#555}.totals{margin:16px 0 0 auto;width:260px}.totals div{display:flex;justify-content:space-between;padding:5px;border-bottom:1px solid #ddd}.terms{margin-top:16px;padding:12px;border:1px solid #ccc}
      @page{size:${format === 'thermal' ? '80mm auto' : 'A4'};margin:${format === 'thermal' ? '4mm' : '14mm'}}
      @media print{body{margin:0}main{max-width:none}.no-print{display:none}}
    </style></head><body><main><div class="header"><div><h1>${this.escapeHtml(this.tenant.tenant()?.name ?? 'My Shop')}</h1><p>Ferti+ Shop Owner</p>${this.tenant.tenant()?.gstin ? `<p>GSTIN: ${this.escapeHtml(this.tenant.tenant()?.gstin ?? '')}</p>` : ''}</div><div><h2>Invoice</h2><p>${this.escapeHtml(bill.bill_number)}</p><p>${this.escapeHtml(bill.bill_date)}</p></div></div><div class="meta"><b>Customer:</b> ${this.escapeHtml(customer)}<br><b>Payment:</b> ${this.escapeHtml(bill.payment_type)}</div><table><thead><tr><th>Item / pack</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead><tbody>${rows}</tbody></table><div class="totals"><div><span>Subtotal</span><b>${this.money(bill.subtotal)}</b></div><div><span>Discount</span><b>−${this.money(bill.discount)}</b></div><div><span>Taxable value</span><b>${this.money(bill.taxableValue ?? 0)}</b></div><div><span>CGST</span><b>${this.money(bill.cgst ?? 0)}</b></div><div><span>SGST</span><b>${this.money(bill.sgst ?? 0)}</b></div>${bill.interest_amount ? `<div><span>Interest (${bill.interestPct ?? 0}% × ${bill.months ?? 0} months)</span><b>${this.money(bill.interest_amount)}</b></div>` : ''}<div><span>Rounding</span><b>${this.money(bill.rounding ?? bill.round_off)}</b></div><div><span>Total</span><b>${this.money(bill.total)}</b></div><div><span>Paid now</span><b>${this.money(bill.paid_now)}</b></div><div><span>Balance</span><b>${this.money(bill.balance)}</b></div></div>${bill.due_date ? `<div class="terms">Credit due date: ${this.escapeHtml(bill.due_date)}</div>` : ''}<p style="margin-top:28px">Thank you for your business.</p><button class="no-print" onclick="window.print()">Print / save PDF</button></main></body></html>`);
    popup.document.close();
    popup.focus();
    setTimeout(() => popup.print(), 250);
  }

  share(bill: Bill): void {
    const customer = this.customerName(bill);
    const text = `${this.tenant.tenant()?.name ?? 'My Shop'}: bill ${bill.bill_number} for ${customer}. Total ₹${bill.total.toLocaleString('en-IN')}, balance ₹${bill.balance.toLocaleString('en-IN')}.`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
  }

  async void(bill: Bill): Promise<void> {
    this.feedback = '';
    const reason = prompt('Reason for voiding this bill:');
    if (!reason?.trim()) return;
    try {
      await this.billService.voidBill(bill.id, reason);
      this.notice.show('Bill voided and stock / khata reversed.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not void bill.';
    }
  }

  private money(value: number): string {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch] ?? ch);
  }
}
