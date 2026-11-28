import { Injectable, computed, inject } from '@angular/core';
import { BillService, SaveBillInput } from './bill.service';
import { BrandService } from './brand.service';
import { CashbookService } from './cashbook.service';
import { CategoryService } from './category.service';
import { FarmerService } from './farmer.service';
import { KhataService } from './khata.service';
import { PackService } from './pack.service';
import { ProductService } from './product.service';
import { SeasonService } from './season.service';
import { SettingsService } from './settings.service';
import { PageQuery } from './shop-api.helper';
import { StockService } from './stock.service';
import {
  CashbookCreate, CashbookUpdate, FarmerCreate, FarmerUpdate, Pack,
  Product, ProductCreate, ProductPackInput, ProductType,
  SeasonCreate, SeasonUpdate, StockLotCreate, StockLotUpdate, StockMovementCreate,
} from '../models';

/**
 * Facade over the individual domain services so existing components continue to work
 * seamlessly while new components can inject individual services directly.
 */
@Injectable({ providedIn: 'root' })
export class ShopDataService {
  readonly brandService = inject(BrandService);
  readonly categoryService = inject(CategoryService);
  readonly productService = inject(ProductService);
  readonly packService = inject(PackService);
  readonly farmerService = inject(FarmerService);
  readonly seasonService = inject(SeasonService);
  readonly cashbookService = inject(CashbookService);
  readonly billService = inject(BillService);
  readonly stockService = inject(StockService);
  readonly khataService = inject(KhataService);
  readonly settingsService = inject(SettingsService);

  // ---- signals ------------------------------------------------------------
  readonly brands = this.brandService.brands;
  readonly categories = this.categoryService.categories;
  readonly products = this.productService.products;
  readonly packs = this.packService.packs;
  readonly farmers = this.farmerService.farmers;
  readonly seasons = this.seasonService.seasons;
  readonly bills = this.billService.bills;
  readonly stockLots = this.stockService.stockLots;
  readonly stockMovements = this.stockService.stockMovements;
  readonly stockLedger = this.stockService.stockLedger;
  readonly khataEntries = this.khataService.khataEntries;
  readonly settings = this.settingsService.settings;

  readonly todaySales = this.billService.todaySales;
  readonly cashInHand = this.billService.cashInHand;
  readonly lowStockProducts = this.productService.lowStockProducts;
  readonly totalCredit = computed(() =>
    this.farmers().reduce((sum, f) => sum + this.farmerBalance(f.id), 0)
  );

  // ---- lifecycle ----------------------------------------------------------
  async loadAll(query: PageQuery = {}): Promise<void> {
    await Promise.all([
      this.refreshBrands(query),
      this.refreshCategories(query),
      this.refreshProducts(query),
      this.refreshPacks(query),
      this.refreshFarmers(query),
      this.refreshSeasons(query),
      this.refreshBills(query),
      this.refreshStockLots(query),
      this.refreshKhata(query),
      this.refreshSettings(query),
    ]);
  }

  reset(): void {
    this.brandService.reset();
    this.categoryService.reset();
    this.productService.reset();
    this.packService.reset();
    this.farmerService.reset();
    this.seasonService.reset();
    this.billService.reset();
    this.stockService.reset();
    this.khataService.reset();
    this.settingsService.reset();
  }

  // ---- Brands -------------------------------------------------------------
  refreshBrands = (q: PageQuery = {}) => this.brandService.refreshBrands(q);
  addBrand = (name: string, mfg: string, notes: string) => this.brandService.addBrand(name, mfg, notes);
  updateBrand = (id: string, name: string, mfg: string, notes: string) => this.brandService.updateBrand(id, name, mfg, notes);
  deactivateBrand = (id: string) => this.brandService.deactivateBrand(id);
  brandName = (id: string) => this.brandService.brandName(id);

  // ---- Categories ---------------------------------------------------------
  refreshCategories = (q: PageQuery = {}) => this.categoryService.refreshCategories(q);
  addCategory = (name: string, type: ProductType, gst: number) => this.categoryService.addCategory(name, type, gst);
  updateCategory = (id: string, name: string, type: ProductType, gst: number) => this.categoryService.updateCategory(id, name, type, gst);
  deactivateCategory = (id: string) => this.categoryService.deactivateCategory(id);
  categoryName = (id: string) => this.categoryService.categoryName(id);

  // ---- Products & Packs ---------------------------------------------------
  refreshProducts = (q: PageQuery = {}) => this.productService.refreshProducts(q);
  addProduct = (input: Omit<ProductCreate, 'packs'>, packs: ProductPackInput[]) => this.productService.addProduct(input, packs);
  updateProduct = (id: string, input: Partial<ProductCreate>, packs: ProductPackInput[]) => this.productService.updateProduct(id, input, packs);
  deactivateProduct = (id: string) => this.productService.deactivateProduct(id);
  product = (id: string) => this.productService.product(id);
  totalStock = (product: Product) => this.productService.totalStock(product);
  stockInPacks = (product: Product, pack: Pack) => this.productService.stockInPacks(product, pack);
  refreshPacks = (q: PageQuery & { product_id?: string } = {}) => this.packService.refreshPacks(q);

  // ---- Farmers ------------------------------------------------------------
  refreshFarmers = (q: PageQuery = {}) => this.farmerService.refreshFarmers(q);
  addFarmer = (input: FarmerCreate) => this.farmerService.addFarmer(input);
  updateFarmer = (id: string, input: FarmerUpdate) => this.farmerService.updateFarmer(id, input);

  // ---- Seasons ------------------------------------------------------------
  refreshSeasons = (q: PageQuery = {}) => this.seasonService.refreshSeasons(q);
  addSeason = (input: SeasonCreate) => this.seasonService.addSeason(input);
  updateSeason = (id: string, input: SeasonUpdate) => this.seasonService.updateSeason(id, input);
  deactivateSeason = (id: string) => this.seasonService.deactivateSeason(id);

  // ---- Cashbook -----------------------------------------------------------
  listCashbook = (q: PageQuery = {}) => this.cashbookService.listCashbook(q);
  createCashbook = (input: CashbookCreate) => this.cashbookService.createCashbook(input);
  updateCashbook = (id: string, input: CashbookUpdate) => this.cashbookService.updateCashbook(id, input);

  // ---- Bills & Payments ---------------------------------------------------
  refreshBills = (q: PageQuery = {}) => this.billService.refreshBills(q);
  getBillItems = (billId: string) => this.billService.getBillItems(billId);
  saveBill = (input: SaveBillInput) => this.billService.saveBill(input);
  voidBill = (id: string, reason: string) => this.billService.voidBill(id, reason);
  receivePayment = (farmerId: string, amount: number, mode: string, note: string) =>
    this.billService.receivePayment(farmerId, amount, mode, note);

  // ---- Stock --------------------------------------------------------------
  refreshStockLots = (q: PageQuery & { pack_id?: string; in_stock_only?: boolean; expiring_before?: string } = {}) =>
    this.stockService.refreshStockLots(q);
  createStockLot = (input: StockLotCreate) => this.stockService.createStockLot(input);
  updateStockLot = (id: string, input: StockLotUpdate) => this.stockService.updateStockLot(id, input);
  refreshStockMovements = (q: PageQuery & { pack_id?: string; stock_lot_id?: string } = {}) =>
    this.stockService.refreshStockMovements(q);
  createStockMovement = (input: StockMovementCreate) => this.stockService.createStockMovement(input);
  stockIn = (packId: string, qtyBase: number, supplier: string, batchNo: string, expiryDate: string, costPrice: number) =>
    this.stockService.stockIn(packId, qtyBase, supplier, batchNo, expiryDate, costPrice);
  adjustStock = (lotId: string, qtyBase: number, reason: string) => this.stockService.adjustStock(lotId, qtyBase, reason);

  // ---- Khata --------------------------------------------------------------
  refreshKhata = (q: PageQuery & { farmer_id?: string; bill_id?: string } = {}) => this.khataService.refreshKhata(q);
  farmerBalance = (farmerId: string) => this.khataService.farmerBalance(farmerId);

  // ---- Settings -----------------------------------------------------------
  refreshSettings = (q: PageQuery = {}) => this.settingsService.refreshSettings(q);
  saveSettings = (values: Record<string, any>) => this.settingsService.saveSettings(values);
}
