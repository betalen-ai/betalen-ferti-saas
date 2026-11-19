import { BillLine } from '../models/shop.models';
import { ShopDataService } from './shop-data.service';

describe('ShopDataService', () => {
  function line(productId: string, packId: string, name: string, label: string, amount: number, stock: number): BillLine {
    return {
      productId, packId, productName: name, packLabel: label,
      quantity: 1, unitPrice: amount, gstPercent: 0, lineTotal: amount, quantityBase: stock
    };
  }

  it('records a spot bill and removes sold stock in base units', () => {
    const data = new ShopDataService();
    const urea = data.product('product-urea');
    expect(urea).toBeDefined();
    const pack = urea!.packs.find(item => item.id === 'urea-50')!;
    const initialStock = urea!.stockBase[pack.id];

    const bill = data.saveBill({
      farmerId: null, seasonId: null, paymentType: 'cash', paymentMode: 'cash',
      lines: [line(urea!.id, pack.id, urea!.name, pack.label, 1000, pack.sizeInBaseUnit)],
      discount: 50, discountType: 'amount', interestPct: 0, months: 0, paidNow: 0,
      dueDate: null, taxExclusive: false
    });

    expect(bill.total).toBe(950);
    expect(bill.balance).toBe(0);
    expect(data.product(urea!.id)!.stockBase[pack.id]).toBe(initialStock - pack.sizeInBaseUnit);
  });

  it('creates a khata debit for a credit sale with simple interest', () => {
    const data = new ShopDataService();
    const dap = data.product('product-dap')!;
    const pack = dap.packs[0];
    const bill = data.saveBill({
      farmerId: 'farmer-ramesh', seasonId: null, paymentType: 'credit', paymentMode: 'credit',
      lines: [line(dap.id, pack.id, dap.name, pack.label, 1000, pack.sizeInBaseUnit)],
      discount: 0, discountType: 'amount', interestPct: 1, months: 6, paidNow: 0,
      dueDate: '2026-10-31', taxExclusive: false
    });

    expect(bill.interestAmount).toBe(60);
    expect(bill.total).toBe(1060);
    expect(bill.balance).toBe(1060);
    expect(data.farmerBalance('farmer-ramesh')).toBe(1060);
  });

  it('allocates received payments to interest before principal and updates balances', () => {
    const data = new ShopDataService();
    const dap = data.product('product-dap')!;
    const pack = dap.packs[0];
    const bill = data.saveBill({
      farmerId: 'farmer-ramesh', seasonId: null, paymentType: 'credit', paymentMode: 'credit',
      lines: [line(dap.id, pack.id, dap.name, pack.label, 1000, pack.sizeInBaseUnit)],
      discount: 0, discountType: 'amount', interestPct: 1, months: 6, paidNow: 0,
      dueDate: '2026-10-31', taxExclusive: false
    });

    data.receivePayment('farmer-ramesh', 60, 'UPI', 'Receipt 1');
    const updatedBill = data.bills().find(item => item.id === bill.id)!;
    expect(updatedBill.interestBalance).toBe(0);
    expect(updatedBill.principalBalance).toBe(1000);
    expect(updatedBill.balance).toBe(1000);
    expect(data.farmerBalance('farmer-ramesh')).toBe(1000);
  });

  it('creates a part-payment bill with interest only on the remaining credit', () => {
    const data = new ShopDataService();
    const dap = data.product('product-dap')!;
    const pack = dap.packs[0];
    const bill = data.saveBill({
      farmerId: 'farmer-ramesh', seasonId: null, paymentType: 'part', paymentMode: 'cash',
      lines: [line(dap.id, pack.id, dap.name, pack.label, 1000, pack.sizeInBaseUnit)],
      discount: 0, discountType: 'amount', interestPct: 1, months: 4, paidNow: 400,
      dueDate: '2026-10-31', taxExclusive: false
    });

    expect(bill.interestAmount).toBe(24);
    expect(bill.total).toBe(1024);
    expect(bill.paidNow).toBe(400);
    expect(bill.balance).toBe(624);
  });
});
