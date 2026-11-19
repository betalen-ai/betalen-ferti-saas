import { Injectable, computed, signal } from '@angular/core';
import {
  Bill, BillLine, Brand, Category, Farmer, KhataEntry, Pack, PackUnit, PaymentType,
  Product, ProductPackInput, ProductType, Season, StockEntry
} from '../models/shop.models';
import { allocatePayment, calcCreditTotal, calcSpotTotal, UnpaidBill } from '../utils/interest.util';

@Injectable({ providedIn: 'root' })
export class ShopDataService {
  readonly brands = signal<Brand[]>([
    { id: 'brand-kisan', name: 'Kisan Gold', manufacturer: 'Kisan Agro', notes: '', active: true },
    { id: 'brand-green', name: 'GreenGrow', manufacturer: 'GreenGrow India', notes: '', active: true },
    { id: 'brand-bharat', name: 'Bharat Seeds', manufacturer: 'Bharat Agri', notes: '', active: true }
  ]);
  readonly categories = signal<Category[]>([
    { id: 'cat-fertilizer', name: 'Chemical fertilizer', type: 'Solid', gstPercent: 5, active: true },
    { id: 'cat-liquid', name: 'Liquid fertilizer and bio-stimulant', type: 'Liquid', gstPercent: 18, active: true },
    { id: 'cat-seed', name: 'Seeds', type: 'Solid', gstPercent: 0, active: true },
    { id: 'cat-tool', name: 'Machinery and tools', type: 'Item', gstPercent: 18, active: true }
  ]);
  readonly products = signal<Product[]>([
    this.seedProduct('product-urea', 'Urea', 'brand-kisan', 'cat-fertilizer', 'Solid', '46% Nitrogen', 'kg', [
      this.seedPack('urea-5', '5 kg bag', 5, 'kg', 150, 145),
      this.seedPack('urea-50', '50 kg bag', 50, 'kg', 270, 265)
    ], { 'urea-5': 75, 'urea-50': 2000 }, 250),
    this.seedProduct('product-dap', 'DAP', 'brand-kisan', 'cat-fertilizer', 'Solid', '18-46-0', 'kg', [
      this.seedPack('dap-50', '50 kg bag', 50, 'kg', 1350, 1320)
    ], { 'dap-50': 1000 }, 500),
    this.seedProduct('product-nano', 'Nano Urea', 'brand-green', 'cat-liquid', 'Liquid', '4% Nitrogen', 'L', [
      this.seedPack('nano-500', '500 ml bottle', 0.5, 'L', 225, 210),
      this.seedPack('nano-5l', '5 L can', 5, 'L', 1800, 1750)
    ], { 'nano-500': 14, 'nano-5l': 30 }, 20)
  ]);
  readonly farmers = signal<Farmer[]>([
    { id: 'farmer-ramesh', name: 'Ramesh Patel', mobile: '9876543210', village: 'Naranpura', address: '', landSize: 4, notes: '', openingBalance: 0, creditLimit: 25000, lastBillDate: null },
    { id: 'farmer-sita', name: 'Sita Devi', mobile: '9876543211', village: 'Bopal', address: '', landSize: 2, notes: '', openingBalance: 0, creditLimit: 15000, lastBillDate: null }
  ]);
  readonly seasons = signal<Season[]>([
    { id: 'season-kharif', name: 'Kharif 2026', startDate: '2026-06-01', endDate: '2026-10-31', cashDiscount: 0, discountType: 'amount', creditInterestPct: 1, dueDate: '2026-10-31', graceDays: 7, lateInterestPct: 1, active: true }
  ]);
  readonly bills = signal<Bill[]>([]);
  readonly stockLedger = signal<StockEntry[]>([]);
  readonly khataEntries = signal<KhataEntry[]>([]);
  readonly todaySales = computed(() => this.bills().filter(bill => bill.date === this.today() && bill.status !== 'void' && bill.status !== 'held').reduce((sum, bill) => sum + bill.total, 0));
  readonly cashInHand = computed(() => this.bills().filter(bill => bill.date === this.today() && bill.paymentMode === 'cash').reduce((sum, bill) => sum + bill.paidNow, 0));
  readonly totalCredit = computed(() => this.farmers().reduce((sum, farmer) => sum + this.farmerBalance(farmer.id), 0));
  readonly lowStockProducts = computed(() => this.products().filter(product => product.active && this.totalStock(product) <= product.lowStockLevel));

  addBrand(name: string, manufacturer: string, notes: string): void {
    if (!name.trim()) return;
    this.brands.update(items => [...items, { id: this.id('brand'), name: name.trim(), manufacturer: manufacturer.trim(), notes: notes.trim(), active: true }]);
  }

  updateBrand(id: string, name: string, manufacturer: string, notes: string): void {
    this.brands.update(items => items.map(item => item.id === id ? { ...item, name: name.trim(), manufacturer: manufacturer.trim(), notes: notes.trim() } : item));
  }

  deactivateBrand(id: string): void {
    this.brands.update(items => items.map(item => item.id === id ? { ...item, active: false } : item));
  }

  addCategory(name: string, type: ProductType, gstPercent: number): void {
    if (!name.trim()) return;
    this.categories.update(items => [...items, { id: this.id('category'), name: name.trim(), type, gstPercent: Math.max(0, gstPercent), active: true }]);
  }

  updateCategory(id: string, name: string, type: ProductType, gstPercent: number): void {
    if (!name.trim()) throw new Error('Enter a category name.');
    this.categories.update(items => items.map(item => item.id === id
      ? { ...item, name: name.trim(), type, gstPercent: Math.max(0, gstPercent) }
      : item));
  }

  deactivateCategory(id: string): void {
    this.categories.update(items => items.map(item => item.id === id ? { ...item, active: false } : item));
  }

  addProduct(input: Omit<Product, 'id' | 'packs' | 'stockBase'>, packs: ProductPackInput[]): string {
    const duplicate = this.products().some(product =>
      product.active && product.brandId === input.brandId && product.name.trim().toLowerCase() === input.name.trim().toLowerCase()
      && product.packs.some(existing => packs.some(pack => existing.sizeInBaseUnit === this.toBase(pack.size, pack.unit)))
    );
    if (duplicate) throw new Error('A product with this brand, name, and pack size already exists.');
    if (!packs.length) throw new Error('Add at least one product pack.');

    const id = this.id('product');
    const preparedPacks = packs.map(pack => this.makePack(pack));
    this.products.update(items => [...items, { ...input, id, packs: preparedPacks, stockBase: Object.fromEntries(preparedPacks.map(pack => [pack.id, 0])) }]);
    return id;
  }

  updateProduct(id: string, input: Omit<Product, 'id' | 'packs' | 'stockBase'>, packs: ProductPackInput[]): void {
    const current = this.product(id);
    if (!current) throw new Error('Product not found.');
    if (!packs.length) throw new Error('Add at least one product pack.');
    if (current.type !== input.type && this.totalStock(current) > 0) {
      throw new Error('Product type cannot be changed while stock is on hand.');
    }
    if (current.packs.slice(packs.length).some(pack => (current.stockBase[pack.id] ?? 0) > 0)) {
      throw new Error('Move or sell the remaining stock before removing a pack.');
    }
    const duplicate = this.products().some(product =>
      product.id !== id && product.active && product.brandId === input.brandId
      && product.name.trim().toLowerCase() === input.name.trim().toLowerCase()
      && product.packs.some(existing => packs.some(pack => existing.sizeInBaseUnit === this.toBase(pack.size, pack.unit)))
    );
    if (duplicate) throw new Error('A product with this brand, name, and pack size already exists.');
    const prepared = packs.map((pack, index) => {
      const previous = current.packs[index];
      return previous ? { ...this.makePack(pack), id: previous.id } : this.makePack(pack);
    });
    const stockBase = Object.fromEntries(prepared.map(pack => [pack.id, current.stockBase[pack.id] ?? 0]));
    this.products.update(items => items.map(product => product.id === id ? { ...input, id, packs: prepared, stockBase } : product));
  }

  deactivateProduct(id: string): void {
    this.products.update(items => items.map(item => item.id === id ? { ...item, active: false } : item));
  }

  addFarmer(input: Omit<Farmer, 'id' | 'lastBillDate'>): void {
    if (this.farmers().some(farmer => farmer.mobile === input.mobile.trim())) {
      throw new Error('A farmer with this mobile number already exists.');
    }
    const farmer: Farmer = { ...input, id: this.id('farmer'), mobile: input.mobile.trim(), lastBillDate: null };
    this.farmers.update(items => [...items, farmer]);
    if (farmer.openingBalance !== 0) {
      this.appendLedger(farmer.id, 'Opening balance', Math.abs(farmer.openingBalance), farmer.openingBalance > 0 ? 'debit' : 'credit', '');
    }
  }

  addSeason(input: Omit<Season, 'id' | 'active'>): void {
    if (!input.name.trim()) return;
    this.seasons.update(items => [...items, { ...input, id: this.id('season'), active: true }]);
  }

  deactivateSeason(id: string): void {
    this.seasons.update(items => items.map(item => item.id === id ? { ...item, active: false } : item));
  }

  stockIn(productId: string, packId: string, quantity: number, supplier: string, batchNo: string, expiryDate: string, costPrice: number): void {
    const product = this.product(productId);
    const pack = product?.packs.find(item => item.id === packId);
    if (!product || !pack || quantity <= 0) throw new Error('Choose a product pack and a quantity greater than zero.');
    const amount = quantity * pack.sizeInBaseUnit;
    this.changeStock(productId, packId, amount);
    this.addStockEntry(product, 'in', amount, `${quantity} ${pack.label}`, batchNo, expiryDate, supplier, costPrice);
  }

  adjustStock(productId: string, packId: string, quantity: number, reason: string, allowNegative = false): void {
    const product = this.product(productId);
    const pack = product?.packs.find(item => item.id === packId);
    if (!product || !pack || quantity === 0 || !reason.trim()) throw new Error('Choose a product pack, enter a quantity, and provide a reason.');
    const amount = quantity * pack.sizeInBaseUnit;
    const current = product.stockBase[packId] ?? 0;
    if (current + amount < 0 && !allowNegative) throw new Error('This adjustment would make stock negative. Confirm the adjustment to continue.');
    this.changeStock(productId, packId, amount);
    this.addStockEntry(product, 'adjustment', amount, reason.trim(), '', '', '');
  }

  saveBill(input: {
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
  }): Bill {
    if (!input.lines.length) throw new Error('Add at least one item to the bill.');
    if (input.paymentType !== 'cash' && !input.farmerId) {
      throw new Error('Choose a farmer before adding a sale to khata.');
    }
    const subtotal = input.lines.reduce((sum, line) => sum + line.lineTotal, 0);
    const discount = input.paymentType === 'cash'
      ? subtotal - calcSpotTotal(subtotal, input.discount, input.discountType)
      : 0;
    const netSubtotal = subtotal - discount;
    let taxableValue = 0;
    let taxAmount = 0;
    for (const line of input.lines) {
      const netLine = subtotal > 0 ? netSubtotal * line.lineTotal / subtotal : 0;
      const rate = Math.max(0, line.gstPercent);
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
    const paidNow = input.hold ? 0 : input.paymentType === 'cash' ? total : input.paymentType === 'credit' ? 0 : Math.min(total, Math.max(0, input.paidNow));
    const balance = input.hold ? 0 : Math.max(0, total - paidNow);
    const billNumber = `F-${String(this.bills().length + 1).padStart(5, '0')}`;
    const farmer = input.farmerId ? this.farmers().find(item => item.id === input.farmerId) : undefined;
    if (farmer?.creditLimit !== null && farmer?.creditLimit !== undefined
      && this.farmerBalance(farmer.id) + balance > farmer.creditLimit) {
      throw new Error(`${farmer.name}'s credit limit would be exceeded.`);
    }
    const bill: Bill = {
      id: this.id('bill'), number: billNumber, date: this.today(), farmerId: input.farmerId,
      farmerName: farmer?.name ?? 'Walk-in customer', seasonId: input.seasonId,
      paymentType: input.paymentType, paymentMode: input.paymentMode, lines: input.lines, subtotal, discount, interestPct: input.interestPct,
      months: input.months, interestAmount: due.interest, total, paidNow, balance,
      principalBalance: balance > 0 ? Math.max(0, principalTotal - (input.paymentType === 'part' ? paidNow : 0)) : 0,
      interestBalance: balance > 0 ? due.interest : 0,
      taxableValue, cgst, sgst, rounding: total - (principalTotal + due.interest),
      dueDate: balance > 0 ? input.dueDate : null,
      status: input.hold ? 'held' : balance === 0 ? 'paid' : paidNow > 0 ? 'part-paid' : 'credit'
    };

    for (const line of input.lines) {
      const product = this.product(line.productId);
      if (!product) continue;
      const available = product.stockBase[line.packId] ?? 0;
      if (available - line.quantityBase < 0) throw new Error(`${line.productName} does not have enough stock.`);
    }
    if (!input.hold) {
      for (const line of input.lines) {
        this.changeStock(line.productId, line.packId, -line.quantityBase);
        const product = this.product(line.productId);
        if (product) this.addStockEntry(product, 'sale', -line.quantityBase, billNumber, '', '', '');
      }
    }
    this.bills.update(items => [bill, ...items]);
    if (farmer && !input.hold) {
      this.farmers.update(items => items.map(item => item.id === farmer.id ? { ...item, lastBillDate: bill.date } : item));
      if (balance > 0) {
        const principal = Math.max(0, principalTotal - paidNow);
        if (principal > 0) this.appendLedger(farmer.id, `Credit sale ${billNumber}`, principal, 'debit', billNumber);
        if (due.interest > 0) this.appendLedger(farmer.id, `Interest ${billNumber}`, due.interest, 'debit', billNumber);
      }
      if (paidNow > 0) this.appendLedger(farmer.id, `Payment on ${billNumber}`, paidNow, 'credit', billNumber);
    }
    return bill;
  }

  voidBill(id: string, reason: string): void {
    const bill = this.bills().find(item => item.id === id);
    if (!bill) throw new Error('Bill not found.');
    if (bill.status === 'void') throw new Error('This bill is already void.');
    if (!reason.trim()) throw new Error('Enter a reason to void this bill.');
    if (bill.status !== 'held' && (bill.paymentType === 'cash' || bill.paidNow > 0 || bill.balance < bill.total)) {
      throw new Error('A paid or partially paid bill cannot be voided. Record a return or refund instead.');
    }

    if (bill.status !== 'held') {
      for (const line of bill.lines) {
        this.changeStock(line.productId, line.packId, line.quantityBase);
        const product = this.product(line.productId);
        if (product) this.addStockEntry(product, 'return', line.quantityBase, `Void ${bill.number}: ${reason.trim()}`, '', '', '');
      }
      if (bill.farmerId && bill.balance > 0) {
        this.appendLedger(bill.farmerId, `Void reversal ${bill.number}`, bill.balance, 'credit', bill.number);
      }
    }
    this.bills.update(items => items.map(item => item.id === id
      ? { ...item, status: 'void', balance: 0, principalBalance: 0, interestBalance: 0 }
      : item));
  }

  receivePayment(farmerId: string, amount: number, mode: string, note: string): void {
    if (amount <= 0) throw new Error('Enter a payment amount greater than zero.');
    const farmer = this.farmers().find(item => item.id === farmerId);
    if (!farmer) throw new Error('Choose a farmer to receive payment from.');
    const bills = this.bills().filter(bill => bill.farmerId === farmerId && bill.balance > 0);
    const allocations = allocatePayment(amount, bills.map(bill => this.unpaidBill(bill)));
    let remaining = amount;
    const updatedBills = this.bills().map(bill => {
      const allocation = allocations.find(item => item.billId === bill.id);
      if (!allocation) return bill;
      remaining -= allocation.amount;
      const paid = allocation.amount;
      const interestBalance = Math.max(0, bill.interestBalance - allocation.interestPaid);
      const principalBalance = Math.max(0, bill.principalBalance - allocation.principalPaid);
      const balance = interestBalance + principalBalance;
      return {
        ...bill, balance, interestBalance, principalBalance,
        status: balance === 0 ? 'paid' as const : 'part-paid' as const
      };
    });
    this.bills.set(updatedBills);
    if (amount > 0) this.appendLedger(farmerId, `Payment received (${mode})`, amount, 'credit', note);
    void remaining;
  }

  farmerBalance(farmerId: string): number {
    return this.khataEntries().filter(entry => entry.farmerId === farmerId)
      .reduce((balance, entry) => balance + (entry.direction === 'debit' ? entry.amount : -entry.amount), 0);
  }

  brandName(id: string): string {
    return this.brands().find(item => item.id === id)?.name ?? 'Unknown brand';
  }

  categoryName(id: string): string {
    return this.categories().find(item => item.id === id)?.name ?? 'Uncategorised';
  }

  product(id: string): Product | undefined {
    return this.products().find(item => item.id === id);
  }

  totalStock(product: Product): number {
    return Object.values(product.stockBase).reduce((sum, amount) => sum + amount, 0);
  }

  stockInPacks(product: Product, pack: Pack): number {
    return (product.stockBase[pack.id] ?? 0) / pack.sizeInBaseUnit;
  }

  private unpaidBill(bill: Bill): UnpaidBill {
    return { billId: bill.id, date: bill.date, interestDue: bill.interestBalance, principalDue: bill.principalBalance };
  }

  private appendLedger(farmerId: string, description: string, amount: number, direction: 'debit' | 'credit', note: string): void {
    const balanceAfter = this.farmerBalance(farmerId) + (direction === 'debit' ? amount : -amount);
    this.khataEntries.update(items => [...items, {
      id: this.id('entry'), farmerId, date: this.today(), description,
      billNumber: note.startsWith('F-') ? note : '', direction, amount, balanceAfter, note
    }]);
  }

  private changeStock(productId: string, packId: string, delta: number): void {
    this.products.update(items => items.map(product => product.id === productId
      ? { ...product, stockBase: { ...product.stockBase, [packId]: (product.stockBase[packId] ?? 0) + delta } }
      : product));
  }

  private addStockEntry(product: Product, type: StockEntry['type'], quantityBase: number, reason: string, batchNo: string, expiryDate: string, supplier: string, costPrice = 0): void {
    const updated = this.product(product.id);
    const balanceBase = updated ? this.totalStock(updated) : 0;
    this.stockLedger.update(items => [{
      id: this.id('stock'), date: this.today(), productId: product.id, productName: product.name,
      type, quantityBase, balanceBase, reason, batchNo, expiryDate, supplier, costPrice
    }, ...items]);
  }

  private makePack(input: ProductPackInput): Pack {
    const sizeInBaseUnit = this.toBase(input.size, input.unit);
    const label = input.label.trim() || `${input.size} ${input.unit}`;
    return {
      id: this.id('pack'), label, size: input.size, unit: input.unit, sizeInBaseUnit,
      mrp: input.mrp, cashPrice: input.cashPrice || input.mrp, creditPrice: input.creditPrice || input.cashPrice || input.mrp,
      barcode: '', looseAllowed: input.looseAllowed
    };
  }

  private toBase(size: number, unit: PackUnit): number {
    return unit === 'g' || unit === 'ml' ? size / 1000 : size;
  }

  private seedProduct(
    id: string, name: string, brandId: string, categoryId: string, type: ProductType, grade: string,
    baseUnit: Product['baseUnit'], packs: Pack[], stockBase: Record<string, number>, lowStockLevel: number
  ): Product {
    return { id, name, brandId, categoryId, type, grade, hsn: '', gstPercent: 5, baseUnit, lowStockLevel, active: true, packs, stockBase };
  }

  private seedPack(id: string, label: string, size: number, unit: PackUnit, mrp: number, cashPrice: number): Pack {
    return { id, label, size, unit, sizeInBaseUnit: this.toBase(size, unit), mrp, cashPrice, creditPrice: cashPrice, barcode: '', looseAllowed: unit === 'kg' || unit === 'L' };
  }

  private id(prefix: string): string {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  }

  private today(): string {
    return new Date().toISOString().slice(0, 10);
  }
}
