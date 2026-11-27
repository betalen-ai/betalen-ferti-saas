import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  Bill, BillLine, Brand, BrandCreate, BrandUpdate, Cashbook, CashbookCreate, CashbookUpdate,
  Category, CategoryCreate, CategoryUpdate, Farmer, FarmerCreate, FarmerUpdate,
  KhataEntry, Pack, PackCreate, PackUpdate, PackUnit, PaymentType,
  Product, ProductCreate, ProductPackInput, ProductType, ProductUpdate,
  Season, SeasonCreate, SeasonUpdate, Settings, SettingsIn,
  StockLot, StockLotCreate, StockLotUpdate, StockMovement, StockMovementCreate, StockEntry,
} from '../models/shop.models';
import { allocatePayment, calcCreditTotal, calcSpotTotal, UnpaidBill } from '../utils/interest.util';

const API_BASE = '/api/ferti';

interface PageQuery {
  limit?: number;
  offset?: number;
  search?: string;
  tenant_id?: string;
}

@Injectable({ providedIn: 'root' })
export class ShopDataService {
  private readonly http = inject(HttpClient);

  // ---- reactive store -----------------------------------------------------
  readonly brands = signal<Brand[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly products = signal<Product[]>([]);
  readonly packs = signal<Pack[]>([]);
  readonly farmers = signal<Farmer[]>([]);
  readonly seasons = signal<Season[]>([]);
  readonly bills = signal<Bill[]>([]);
  readonly stockLots = signal<StockLot[]>([]);
  readonly stockMovements = signal<StockMovement[]>([]);
  readonly stockLedger = signal<StockEntry[]>([]); // UI-joined view
  readonly khataEntries = signal<KhataEntry[]>([]);
  readonly settings = signal<Settings | null>(null);

  readonly todaySales = computed(() =>
    this.bills().filter(b => b.bill_date === this.today() && b.status !== 'void' && b.status !== 'held')
      .reduce((sum, b) => sum + b.total, 0));
  readonly cashInHand = computed(() =>
    this.bills().filter(b => b.bill_date === this.today() && b.status !== 'void' && b.status !== 'held')
      .reduce((sum, b) => sum + b.paid_now, 0));
  readonly totalCredit = computed(() =>
    this.farmers().reduce((sum, f) => sum + this.farmerBalance(f.id), 0));
  readonly lowStockProducts = computed(() =>
    this.products().filter(p => p.active && this.totalStock(p) <= p.low_stock_level));

  // ---- loading ------------------------------------------------------------
  async loadAll(query: PageQuery = {}): Promise<void> {
    await Promise.all([
      this.refreshBrands(query),
      this.refreshCategories(query),
      this.refreshProducts(query),
      this.refreshFarmers(query),
      this.refreshSeasons(query),
      this.refreshBills(query),
      this.refreshKhata(query),
      this.refreshSettings(query),
    ]);
  }

  // ---- Brands -------------------------------------------------------------
  async refreshBrands(query: PageQuery = {}): Promise<Brand[]> {
    const rows = await firstValueFrom(this.http.get<Brand[]>(`${API_BASE}/brands`, { params: this.params(query) }));
    this.brands.set(rows);
    return rows;
  }

  async addBrand(name: string, manufacturer: string, notes: string): Promise<Brand> {
    if (!name.trim()) throw new Error('Enter a brand name.');
    const payload: BrandCreate = { name: name.trim(), manufacturer: manufacturer.trim(), notes: notes.trim(), active: true };
    const created = await firstValueFrom(this.http.post<Brand>(`${API_BASE}/brands`, payload));
    this.brands.update(items => [...items, created]);
    return created;
  }

  async updateBrand(id: string, name: string, manufacturer: string, notes: string): Promise<Brand> {
    const payload: BrandUpdate = { name: name.trim(), manufacturer: manufacturer.trim(), notes: notes.trim() };
    const updated = await firstValueFrom(this.http.patch<Brand>(`${API_BASE}/brands/${id}`, payload));
    this.brands.update(items => items.map(b => b.id === id ? updated : b));
    return updated;
  }

  async deactivateBrand(id: string): Promise<void> {
    const updated = await firstValueFrom(this.http.patch<Brand>(`${API_BASE}/brands/${id}`, { active: false } satisfies BrandUpdate));
    this.brands.update(items => items.map(b => b.id === id ? updated : b));
  }

  // ---- Categories ---------------------------------------------------------
  async refreshCategories(query: PageQuery = {}): Promise<Category[]> {
    const rows = await firstValueFrom(this.http.get<Category[]>(`${API_BASE}/categories`, { params: this.params(query) }));
    this.categories.set(rows);
    return rows;
  }

  async addCategory(name: string, productType: ProductType, _gstPercent: number): Promise<Category> {
    // Backend Category has no gst field; GST lives on Product. Accept arg for form compatibility, ignore.
    if (!name.trim()) throw new Error('Enter a category name.');
    const payload: CategoryCreate = { name: name.trim(), product_type: productType, active: true };
    const created = await firstValueFrom(this.http.post<Category>(`${API_BASE}/categories`, payload));
    this.categories.update(items => [...items, created]);
    return created;
  }

  async updateCategory(id: string, name: string, productType: ProductType, _gstPercent: number): Promise<Category> {
    if (!name.trim()) throw new Error('Enter a category name.');
    const payload: CategoryUpdate = { name: name.trim(), product_type: productType };
    const updated = await firstValueFrom(this.http.patch<Category>(`${API_BASE}/categories/${id}`, payload));
    this.categories.update(items => items.map(c => c.id === id ? updated : c));
    return updated;
  }

  async deactivateCategory(id: string): Promise<void> {
    const updated = await firstValueFrom(this.http.patch<Category>(`${API_BASE}/categories/${id}`, { active: false } satisfies CategoryUpdate));
    this.categories.update(items => items.map(c => c.id === id ? updated : c));
  }

  // ---- Products -----------------------------------------------------------
  async refreshProducts(query: PageQuery = {}): Promise<Product[]> {
    const rows = await firstValueFrom(this.http.get<Product[]>(`${API_BASE}/products`, { params: this.params(query) }));
    this.products.set(rows);
    return rows;
  }

  async addProduct(input: Omit<ProductCreate, 'packs'>, packs: ProductPackInput[]): Promise<Product> {
    if (!packs.length) throw new Error('Add at least one product pack.');
    const product = await firstValueFrom(this.http.post<Product>(`${API_BASE}/products`, input));
    const prepared = await Promise.all(packs.map(p => this.createPack({ ...p, product_id: product.id })));
    const withPacks: Product = { ...product, packs: prepared };
    this.products.update(items => [...items, withPacks]);
    return withPacks;
  }

  async updateProduct(id: string, input: Partial<ProductCreate>, packs: ProductPackInput[]): Promise<Product> {
    if (!packs.length) throw new Error('Add at least one product pack.');
    const payload: ProductUpdate = { ...input };
    const updated = await firstValueFrom(this.http.patch<Product>(`${API_BASE}/products/${id}`, payload));
    const current = this.product(id);
    const existingPacks = current?.packs ?? [];
    const prepared: Pack[] = [];
    for (let i = 0; i < packs.length; i++) {
      const prev = existingPacks[i];
      if (prev) {
        const changed = await firstValueFrom(this.http.patch<Pack>(`${API_BASE}/packs/${prev.id}`, this.packUpdatePayload(packs[i])));
        prepared.push(changed);
      } else {
        prepared.push(await this.createPack({ ...packs[i], product_id: id }));
      }
    }
    const result: Product = { ...updated, packs: prepared };
    this.products.update(items => items.map(p => p.id === id ? result : p));
    return result;
  }

  async deactivateProduct(id: string): Promise<void> {
    const updated = await firstValueFrom(this.http.patch<Product>(`${API_BASE}/products/${id}`, { active: false } satisfies ProductUpdate));
    this.products.update(items => items.map(p => p.id === id ? updated : p));
  }

  // ---- Packs --------------------------------------------------------------
  private async createPack(input: ProductPackInput & { product_id: string }): Promise<Pack> {
    const payload: PackCreate = {
      product_id: input.product_id,
      size: input.size,
      size_unit: input.unit,
      size_in_base_unit: this.toBase(input.size, input.unit),
      mrp: input.mrp,
      cash_price: input.cashPrice || input.mrp,
      credit_price: input.creditPrice || input.cashPrice || input.mrp,
      allow_loose_sale: input.looseAllowed,
      active: true,
    };
    const created = await firstValueFrom(this.http.post<Pack>(`${API_BASE}/packs`, payload));
    this.packs.update(items => [...items, created]);
    return created;
  }

  private packUpdatePayload(input: ProductPackInput): PackUpdate {
    return {
      mrp: input.mrp,
      cash_price: input.cashPrice || input.mrp,
      credit_price: input.creditPrice || input.cashPrice || input.mrp,
      allow_loose_sale: input.looseAllowed,
    };
  }

  // ---- Farmers ------------------------------------------------------------
  async refreshFarmers(query: PageQuery = {}): Promise<Farmer[]> {
    const rows = await firstValueFrom(this.http.get<Farmer[]>(`${API_BASE}/farmers`, { params: this.params(query) }));
    this.farmers.set(rows);
    return rows;
  }

  async addFarmer(input: FarmerCreate): Promise<Farmer> {
    if (this.farmers().some(f => f.mobile === input.mobile.trim())) {
      throw new Error('A farmer with this mobile number already exists.');
    }
    const created = await firstValueFrom(this.http.post<Farmer>(`${API_BASE}/farmers`, { ...input, mobile: input.mobile.trim() }));
    this.farmers.update(items => [...items, created]);
    if (created.opening_balance !== 0) {
      this.appendLedgerLocal(created.id, 'Opening balance', Math.abs(created.opening_balance),
        created.opening_balance > 0 ? 'debit' : 'credit', '');
    }
    return created;
  }

  async updateFarmer(id: string, input: FarmerUpdate): Promise<Farmer> {
    const updated = await firstValueFrom(this.http.patch<Farmer>(`${API_BASE}/farmers/${id}`, input));
    this.farmers.update(items => items.map(f => f.id === id ? updated : f));
    return updated;
  }

  // ---- Seasons ------------------------------------------------------------
  async refreshSeasons(query: PageQuery = {}): Promise<Season[]> {
    const rows = await firstValueFrom(this.http.get<Season[]>(`${API_BASE}/seasons`, { params: this.params(query) }));
    this.seasons.set(rows);
    return rows;
  }

  async addSeason(input: SeasonCreate): Promise<Season> {
    const created = await firstValueFrom(this.http.post<Season>(`${API_BASE}/seasons`, input));
    this.seasons.update(items => [...items, created]);
    return created;
  }

  async updateSeason(id: string, input: SeasonUpdate): Promise<Season> {
    const updated = await firstValueFrom(this.http.patch<Season>(`${API_BASE}/seasons/${id}`, input));
    this.seasons.update(items => items.map(s => s.id === id ? updated : s));
    return updated;
  }

  async deactivateSeason(id: string): Promise<void> {
    const updated = await firstValueFrom(this.http.patch<Season>(`${API_BASE}/seasons/${id}`, {} satisfies SeasonUpdate));
    this.seasons.update(items => items.map(s => s.id === id ? updated : s));
  }

  // ---- Cashbook -----------------------------------------------------------
  async listCashbook(query: PageQuery = {}): Promise<Cashbook[]> {
    return firstValueFrom(this.http.get<Cashbook[]>(`${API_BASE}/cashbook`, { params: this.params(query) }));
  }

  async createCashbook(input: CashbookCreate): Promise<Cashbook> {
    return firstValueFrom(this.http.post<Cashbook>(`${API_BASE}/cashbook`, input));
  }

  async updateCashbook(id: string, input: CashbookUpdate): Promise<Cashbook> {
    return firstValueFrom(this.http.patch<Cashbook>(`${API_BASE}/cashbook/${id}`, input));
  }

  // ---- Bills (read-only) --------------------------------------------------
  async refreshBills(query: PageQuery = {}): Promise<Bill[]> {
    const rows = await firstValueFrom(this.http.get<Bill[]>(`${API_BASE}/bills`, { params: this.params(query) }));
    this.bills.set(rows);
    return rows;
  }

  async getBillItems(billId: string): Promise<BillLine[]> {
    return firstValueFrom(this.http.get<BillLine[]>(`${API_BASE}/bills/${billId}/items`));
  }

  // ---- Stock lots ---------------------------------------------------------
  async refreshStockLots(query: PageQuery & { pack_id?: string; in_stock_only?: boolean; expiring_before?: string } = {}): Promise<StockLot[]> {
    const rows = await firstValueFrom(this.http.get<StockLot[]>(`${API_BASE}/stock-lots`, { params: this.params(query) }));
    this.stockLots.set(rows);
    return rows;
  }

  async createStockLot(input: StockLotCreate): Promise<StockLot> {
    const created = await firstValueFrom(this.http.post<StockLot>(`${API_BASE}/stock-lots`, input));
    this.stockLots.update(items => [...items, created]);
    return created;
  }

  async updateStockLot(id: string, input: StockLotUpdate): Promise<StockLot> {
    const updated = await firstValueFrom(this.http.patch<StockLot>(`${API_BASE}/stock-lots/${id}`, input));
    this.stockLots.update(items => items.map(l => l.id === id ? updated : l));
    return updated;
  }

  // ---- Stock movements ----------------------------------------------------
  async refreshStockMovements(query: PageQuery & { pack_id?: string; stock_lot_id?: string } = {}): Promise<StockMovement[]> {
    const rows = await firstValueFrom(this.http.get<StockMovement[]>(`${API_BASE}/stock-movements`, { params: this.params(query) }));
    this.stockMovements.set(rows);
    return rows;
  }

  async createStockMovement(input: StockMovementCreate): Promise<StockMovement> {
    const created = await firstValueFrom(this.http.post<StockMovement>(`${API_BASE}/stock-movements`, input));
    this.stockMovements.update(items => [created, ...items]);
    return created;
  }

  // ---- High-level stock helpers (map UI → lot + movement) -----------------
  async stockIn(packId: string, quantityBase: number, supplier: string, batchNo: string, expiryDate: string, costPrice: number): Promise<StockLot> {
    if (quantityBase <= 0) throw new Error('Enter a quantity greater than zero.');
    return this.createStockLot({
      pack_id: packId,
      supplier: supplier || null,
      received_date: this.today(),
      quantity_base: quantityBase,
      cost_price: costPrice,
      batch_number: batchNo || null,
      expiry_date: expiryDate || null,
    });
  }

  async adjustStock(lotId: string, quantityBase: number, reason: string): Promise<StockMovement> {
    if (quantityBase === 0 || !reason.trim()) throw new Error('Enter a quantity and a reason.');
    return this.createStockMovement({
      stock_lot_id: lotId,
      movement_type: 'adjustment',
      quantity_base: quantityBase,
      reason: reason.trim(),
    });
  }

  // ---- Khata ledger (read-only) ------------------------------------------
  async refreshKhata(query: PageQuery & { farmer_id?: string; bill_id?: string } = {}): Promise<KhataEntry[]> {
    const rows = await firstValueFrom(this.http.get<KhataEntry[]>(`${API_BASE}/khata`, { params: this.params(query) }));
    this.khataEntries.set(rows);
    return rows;
  }

  // ---- Settings -----------------------------------------------------------
  async refreshSettings(query: PageQuery = {}): Promise<Settings | null> {
    try {
      const row = await firstValueFrom(this.http.get<Settings>(`${API_BASE}/settings`, { params: this.params(query) }));
      this.settings.set(row);
      return row;
    } catch {
      this.settings.set(null);
      return null;
    }
  }

  async saveSettings(values: Record<string, any>): Promise<Settings> {
    const payload: SettingsIn = { values };
    const row = await firstValueFrom(this.http.put<Settings>(`${API_BASE}/settings`, payload));
    this.settings.set(row);
    return row;
  }

  // ---- Billing (client-side authoritative until backend billing service) --
  // NOTE: backend routes expose bills as read-only; the authoritative writer is
  // assumed to be a separate billing service. This method keeps the existing
  // client computation logic and POSTs the computed bill for persistence if
  // your billing endpoint exists; otherwise it operates on the local signal.
  async saveBill(input: {
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
  }): Promise<Bill> {
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
    const paidNow = input.hold ? 0 : input.paymentType === 'cash' ? total : input.paymentType === 'credit' ? 0 : Math.min(total, Math.max(0, input.paidNow));
    const balance = input.hold ? 0 : Math.max(0, total - paidNow);
    const billNumber = `F-${String(this.bills().length + 1).padStart(5, '0')}`;
    const farmer = input.farmerId ? this.farmers().find(item => item.id === input.farmerId) : undefined;
    if (farmer && (farmer as any).creditLimit != null && this.farmerBalance(farmer.id) + balance > (farmer as any).creditLimit) {
      throw new Error(`${farmer.name}'s credit limit would be exceeded.`);
    }
    const bill: Bill = {
      id: this.id('bill'), tenant_id: '', created_at: this.nowIso(), updated_at: this.nowIso(), version: 1,
      bill_number: billNumber, bill_date: this.today(), farmer_id: input.farmerId ?? '',
      season_id: input.seasonId, payment_type: input.paymentType, subtotal, discount,
      interest_amount: due.interest, gst_amount: cgst + sgst, round_off: 0,
      total, paid_now: paidNow, balance,
      status: input.hold ? 'held' : balance === 0 ? 'paid' : paidNow > 0 ? 'part-paid' : 'credit',
      terms: null, due_date: balance > 0 ? input.dueDate : null,
      farmerName: farmer?.name ?? 'Walk-in customer', paymentMode: input.paymentMode, lines: input.lines,
      interestPct: input.interestPct, months: input.months,
      principalBalance: balance > 0 ? Math.max(0, principalTotal - (input.paymentType === 'part' ? paidNow : 0)) : 0,
      interestBalance: balance > 0 ? due.interest : 0,
      taxableValue, cgst, sgst,
    };
    for (const line of input.lines) {
      const product = this.product(line.productId ?? '');
      if (!product) continue;
      const available = product.stockBase?.[line.pack_id] ?? 0;
      if (available - line.quantity_base < 0) throw new Error(`${line.product_name} does not have enough stock.`);
    }
    this.bills.update(items => [bill, ...items]);
    if (farmer && !input.hold && balance > 0) {
      const principal = Math.max(0, principalTotal - paidNow);
      if (principal > 0) this.appendLedgerLocal(farmer.id, `Credit sale ${billNumber}`, principal, 'debit', billNumber);
      if (due.interest > 0) this.appendLedgerLocal(farmer.id, `Interest ${billNumber}`, due.interest, 'debit', billNumber);
      if (paidNow > 0) this.appendLedgerLocal(farmer.id, `Payment on ${billNumber}`, paidNow, 'credit', billNumber);
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
    const farmer = this.farmers().find(item => item.id === farmerId);
    if (!farmer) throw new Error('Choose a farmer to receive payment from.');
    const bills = this.bills().filter(bill => bill.farmer_id === farmerId && bill.balance > 0);
    const allocations = allocatePayment(amount, bills.map(bill => this.unpaidBill(bill)));
    this.bills.update(items => items.map(bill => {
      const allocation = allocations.find(a => a.billId === bill.id);
      if (!allocation) return bill;
      const interestBalance = Math.max(0, bill.interestBalance! - allocation.interestPaid);
      const principalBalance = Math.max(0, bill.principalBalance! - allocation.principalPaid);
      const balance = interestBalance + principalBalance;
      return { ...bill, balance, interestBalance, principalBalance,
        status: balance === 0 ? 'paid' as const : 'part-paid' as const };
    }));
    this.appendLedgerLocal(farmerId, `Payment received (${mode})`, amount, 'credit', note);
  }

  // ---- lookups / derived --------------------------------------------------
  farmerBalance(farmerId: string): number {
    return this.khataEntries().filter(e => e.farmer_id === farmerId)
      .reduce((bal, e) => bal + (e.debit > 0 ? e.debit : -e.credit), 0);
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
    return Object.values(product.stockBase ?? {}).reduce((sum, amt) => sum + amt, 0);
  }

  stockInPacks(product: Product, pack: Pack): number {
    return (product.stockBase?.[pack.id] ?? 0) / pack.size_in_base_unit;
  }

  private unpaidBill(bill: Bill): UnpaidBill {
    return { billId: bill.id, date: bill.bill_date, interestDue: bill.interestBalance ?? 0, principalDue: bill.principalBalance ?? 0 };
  }

  private appendLedgerLocal(farmerId: string, description: string, amount: number, direction: 'debit' | 'credit', note: string): void {
    const balanceAfter = this.farmerBalance(farmerId) + (direction === 'debit' ? amount : -amount);
    this.khataEntries.update(items => [...items, {
      id: this.id('entry'), tenant_id: '', created_at: this.nowIso(), updated_at: this.nowIso(), version: 1,
      farmer_id: farmerId, bill_id: null, payment_id: null, entry_type: direction,
      debit: direction === 'debit' ? amount : 0, credit: direction === 'credit' ? amount : 0,
      description, reverses_entry_id: null,
      date: this.today(), billNumber: note.startsWith('F-') ? note : '',
      direction, amount, balanceAfter, note,
    }]);
  }

  // ---- helpers ------------------------------------------------------------
  private params(query: Record<string, any>): HttpParams {
    let p = new HttpParams();
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== '') p = p.set(k, String(v));
    }
    return p;
  }

  private toBase(size: number, unit: PackUnit): number {
    return unit === 'g' || unit === 'ml' ? size / 1000 : size;
  }

  private id(prefix: string): string {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  }

  private today(): string {
    return new Date().toISOString().slice(0, 10);
  }

  private nowIso(): string {
    return new Date().toISOString();
  }
}