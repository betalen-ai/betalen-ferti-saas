import { CommonModule, CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { ShopDataService } from '../core/shop-data.service';
import { TenantService } from '../core/tenant.service';
import {
  BillLine,
  Pack,
  PackUnit,
  PaymentType,
  Product,
  ProductCreate,
  ProductPackInput,
  ProductType,
  StockLot,
} from '../models/shop.models';
import { calcCreditTotal, calcSpotTotal } from '../utils/interest.util';

interface DraftPack {
  label: string;
  size: number;
  unit: PackUnit;
  mrp: number;
  cashPrice: number;
  creditPrice: number;
  looseAllowed: boolean;
}

@Component({
  selector: 'app-feature',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CurrencyPipe, DatePipe, DecimalPipe],
  template: `
    <ng-container [ngSwitch]="page">
      <ng-container *ngSwitchCase="'dashboard'">
        <header class="page-heading">
          <div>
            <span class="eyebrow">SHOP OVERVIEW</span>
            <h1>Good {{dayPart}}, {{ownerName}}</h1>
            <p>Your shop at a glance for today.</p>
          </div>
          <a class="btn btn-primary primary-action" routerLink="/app/pos"><i class="bi bi-cart-plus"></i> New Sale</a>
        </header>
        <section class="kpi-grid">
          <article class="panel kpi"><span>Today's sales</span><strong>{{data.todaySales() | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong><small>Collected today</small></article>
          <article class="panel kpi"><span>Cash in hand</span><strong>{{data.cashInHand() | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong><small>Cash drawer total today</small></article>
          <article class="panel kpi"><span>Credit outstanding</span><strong>{{data.totalCredit() | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong><small>{{data.farmers().length}} customers</small></article>
          <article class="panel kpi warning"><span>Low-stock items</span><strong>{{data.lowStockProducts().length}}</strong><small>Review stock and reorder</small></article>
        </section>
        <section class="quick-actions">
          <a class="panel quick" routerLink="/app/pos"><i class="bi bi-cart-plus"></i><span>New Sale</span></a>
          <a class="panel quick" routerLink="/app/products"><i class="bi bi-plus-square"></i><span>Add Product</span></a>
          <a class="panel quick" routerLink="/app/farmers"><i class="bi bi-person-plus"></i><span>Add Farmer</span></a>
          <a class="panel quick" routerLink="/app/khata"><i class="bi bi-cash-coin"></i><span>Receive Payment</span></a>
        </section>
        <section class="dashboard-panels">
          <article class="panel">
            <div class="panel-title"><h2>Recent bills</h2><a routerLink="/app/bills">View all bills</a></div>
            <ng-container *ngIf="data.bills().length; else noBills">
              <div class="list-row" *ngFor="let bill of data.bills().slice(0,5)">
                <b>{{bill.bill_number}}</b>
                <span>{{bill.farmerName || farmerDisplayName(bill.farmer_id)}}</span>
                <strong>{{bill.total | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong>
              </div>
            </ng-container>
            <ng-template #noBills><p class="empty">Bills you create will appear here.</p></ng-template>
          </article>
          <article class="panel">
            <div class="panel-title"><h2>Low stock alerts</h2><a routerLink="/app/stock">Manage stock</a></div>
            <div class="list-row" *ngFor="let product of data.lowStockProducts()">
              <b>{{product.name}}</b>
              <span>{{data.totalStock(product) | number:'1.0-2'}} {{baseUnitOf(product)}} left</span>
              <strong class="danger">Low</strong>
            </div>
            <p *ngIf="!data.lowStockProducts().length" class="empty">No products below their reorder level.</p>
          </article>
          <article class="panel">
            <div class="panel-title"><h2>Dues this week</h2><a routerLink="/app/khata">Open khata</a></div>
            <div class="list-row" *ngFor="let farmer of farmersWithDues().slice(0,5)">
              <b>{{farmer.name}}</b>
              <span>{{farmer.mobile}}</span>
              <strong>{{data.farmerBalance(farmer.id) | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong>
            </div>
            <p *ngIf="!farmersWithDues().length" class="empty">No outstanding customer balances.</p>
          </article>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'pos'">
        <header class="page-heading">
          <div><span class="eyebrow">POINT OF SALE</span><h1>New sale</h1><p>Add products, choose payment terms, and create a bill.</p></div>
          <a class="btn secondary-action" routerLink="/app/bills"><i class="bi bi-receipt"></i> Bills</a>
        </header>
        <div class="pos-layout">
          <section class="panel pos-catalog">
            <div class="panel-title"><h2>Products</h2><label class="search"><i class="bi bi-search"></i><input [(ngModel)]="productSearch" placeholder="Search products"></label></div>
            <div class="product-tiles">
              <article class="product-tile" *ngFor="let option of filteredPackOptions()">
                <b>{{option.product.name}}</b>
                <span>{{packLabel(option.pack)}}</span>
                <strong>{{option.pack.cash_price | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong>
                <small>Stock {{data.stockInPacks(option.product, option.pack) | number:'1.0-1'}}</small>
                <div class="tile-actions">
                  <button type="button" class="btn secondary-action" (click)="addToCart(option.product.id, option.pack.id)">Add pack</button>
                  <button *ngIf="option.pack.allow_loose_sale" type="button" class="btn secondary-action" (click)="addToCart(option.product.id, option.pack.id, true)">Add loose {{baseUnitOf(option.product)}}</button>
                </div>
              </article>
            </div>
            <p *ngIf="!filteredPackOptions().length" class="empty">No matching products. Add active products in Product Catalog.</p>
          </section>
          <section class="panel bill-builder">
            <div class="panel-title"><h2>Current bill</h2><span class="bill-number">New bill</span></div>
            <label>Farmer / customer</label>
            <select class="form-select" [(ngModel)]="farmerId">
              <option value="">Walk-in customer</option>
              <option *ngFor="let farmer of data.farmers()" [value]="farmer.id">{{farmer.name}} · {{farmer.mobile}}</option>
            </select>
            <label>Season</label>
            <select class="form-select" [(ngModel)]="seasonId" (ngModelChange)="seasonChanged($event)">
              <option value="">No season</option>
              <option *ngFor="let season of activeSeasons()" [value]="season.id">{{season.name}}</option>
            </select>
            <div class="cart-lines" *ngIf="cart.length; else emptyCart">
              <div class="cart-line" *ngFor="let line of cart; let i = index">
                <div><b>{{line.product_name}}</b><small>{{line.pack_name}}</small></div>
                <div class="quantity">
                  <button type="button" (click)="changeCartQuantity(i,-1)">−</button>
                  <span>{{line.quantity}}</span>
                  <button type="button" (click)="changeCartQuantity(i,1)">+</button>
                </div>
                <strong>{{line.line_total | currency:'INR':'symbol':'1.0-0':'en-IN'}}</strong>
              </div>
            </div>
            <ng-template #emptyCart><p class="empty cart-empty">Choose product packs to add them to the bill.</p></ng-template>
            <div class="bill-options">
              <label>Payment type
                <select class="form-select" [(ngModel)]="paymentType" (ngModelChange)="paymentChanged($event)">
                  <option value="cash">Paid on the spot</option>
                  <option value="credit">Credit / khata</option>
                  <option value="part">Part payment</option>
                </select>
              </label>
              <label *ngIf="paymentType !== 'credit'">Paid using
                <select class="form-select" [(ngModel)]="paymentMode">
                  <option value="cash">Cash</option>
                  <option value="UPI">UPI</option>
                  <option value="card">Card</option>
                </select>
              </label>
              <label *ngIf="paymentType === 'cash'">Discount type
                <select class="form-select" [(ngModel)]="discountType">
                  <option value="amount">Fixed amount (₹)</option>
                  <option value="percent">Percent (%)</option>
                </select>
              </label>
              <label *ngIf="paymentType === 'cash'">Discount<input class="form-control" type="number" min="0" [(ngModel)]="discount"></label>
              <label *ngIf="paymentType !== 'cash'">Interest per month (%)<input class="form-control" type="number" min="0" step="0.1" [(ngModel)]="interestPct"></label>
              <label *ngIf="paymentType !== 'cash'">Months<input class="form-control" type="number" min="0" step="0.1" [(ngModel)]="months"></label>
              <label *ngIf="paymentType !== 'cash'">Due date<input class="form-control" type="date" [(ngModel)]="dueDate"></label>
              <label *ngIf="paymentType === 'part'">Paid now<input class="form-control" type="number" min="0" [max]="subtotal" [(ngModel)]="paidNow"></label>
            </div>
            <div class="totals">
              <div><span>Subtotal</span><b>{{subtotal | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div *ngIf="paymentType === 'cash'"><span>Discount</span><b>−{{spotDiscount | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div><span>Taxable value</span><b>{{taxableValue | currency:'INR':'symbol':'1.2-2':'en-IN'}}</b></div>
              <div><span>CGST / SGST</span><b>{{cgst | currency:'INR':'symbol':'1.2-2':'en-IN'}} / {{sgst | currency:'INR':'symbol':'1.2-2':'en-IN'}}</b></div>
              <div *ngIf="paymentType !== 'cash'"><span>Interest ({{interestPct}}% × {{months}} months)</span><b>{{creditInterest | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div class="grand-total"><span>Total payable</span><b>{{total | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div><span>Rounding</span><b>{{rounding | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div *ngIf="paymentType !== 'credit'"><span>Paid now</span><b>{{paymentType === 'cash' ? total : boundedPaidNow | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <div *ngIf="paymentType !== 'cash'"><span>Balance to khata</span><b>{{balance | currency:'INR':'symbol':'1.0-0':'en-IN'}}</b></div>
              <p class="interest-copy" *ngIf="paymentType !== 'cash'">Interest: {{interestPct}}% per month for {{months}} months = {{creditInterest | currency:'INR':'symbol':'1.0-0':'en-IN'}}</p>
            </div>
            <p class="error" *ngIf="feedback">{{feedback}}</p>
            <div class="bill-actions">
              <button class="btn btn-primary primary-action" type="button" (click)="saveSale()"><i class="bi bi-check2-circle"></i> Save bill</button>
              <button class="btn secondary-action" type="button" (click)="saveSale(true)">Hold bill</button>
              <button class="btn danger-button" type="button" (click)="cancelDraft()">Cancel draft</button>
            </div>
          </section>
        </div>
      </ng-container>

      <ng-container *ngSwitchCase="'brands'">
        <header class="page-heading"><div><span class="eyebrow">PRODUCT CATALOG</span><h1>Brands</h1><p>Manage the manufacturers and brands carried by your shop.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>{{editingBrandId ? 'Edit brand' : 'Add a brand'}}</h2></div>
          <div class="form-grid">
            <label>Brand name<input class="form-control" [(ngModel)]="brandName" placeholder="e.g. Kisan Gold"></label>
            <label>Manufacturer<input class="form-control" [(ngModel)]="brandManufacturer" placeholder="Company name"></label>
            <label class="wide">Notes<input class="form-control" [(ngModel)]="brandNotes" placeholder="Optional details"></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <div class="button-row">
            <button type="button" class="btn btn-primary primary-action" (click)="saveBrand()">{{editingBrandId ? 'Save changes' : 'Add brand'}}</button>
            <button *ngIf="editingBrandId" type="button" class="btn secondary-action" (click)="resetBrandForm()">Cancel edit</button>
          </div>
        </section>
        <section class="panel table-panel">
          <div class="panel-title"><h2>Brand list</h2><span>{{data.brands().length}} brands</span></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Brand</th><th>Manufacturer</th><th>Products</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                <tr *ngFor="let brand of data.brands()">
                  <td><b>{{brand.name}}</b></td>
                  <td>{{brand.manufacturer || '—'}}</td>
                  <td>{{productCount(brand.id)}}</td>
                  <td><span class="status" [class.inactive]="!brand.active">{{brand.active ? 'Active' : 'Inactive'}}</span></td>
                  <td>
                    <div class="row-actions">
                      <button type="button" class="btn secondary-action" (click)="editBrand(brand.id)">Edit</button>
                      <button *ngIf="brand.active" type="button" class="btn danger-button" (click)="deactivateBrand(brand.id)">Deactivate</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'products'">
        <header class="page-heading"><div><span class="eyebrow">CATALOG</span><h1>Products</h1><p>Products can have several pack sizes with separate prices and stock.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>{{editingProductId ? 'Edit product and packs' : 'Add product and packs'}}</h2></div>
          <div class="form-grid three">
            <label>Product name<input class="form-control" [(ngModel)]="productName" placeholder="e.g. DAP"></label>
            <label>Brand
              <select class="form-select" [(ngModel)]="productBrand">
                <option value="">Choose brand</option>
                <option *ngFor="let brand of activeBrands()" [value]="brand.id">{{brand.name}}</option>
              </select>
            </label>
            <label>Category
              <select class="form-select" [(ngModel)]="productCategory" (ngModelChange)="syncProductType()">
                <option value="">Choose category</option>
                <option *ngFor="let category of activeCategories()" [value]="category.id">{{category.name}}</option>
              </select>
            </label>
            <label>Type
              <select class="form-select" [(ngModel)]="productType">
                <option>Solid</option>
                <option>Liquid</option>
                <option>Item</option>
              </select>
            </label>
            <label>Composition / grade<input class="form-control" [(ngModel)]="productGrade" placeholder="e.g. 18-46-0"></label>
            <label>HSN code<input class="form-control" [(ngModel)]="productHsn"></label>
            <label>GST %<input class="form-control" type="number" min="0" [(ngModel)]="productGst"></label>
            <label>Low stock level ({{baseUnit}})<input class="form-control" type="number" min="0" [(ngModel)]="productLowStock"></label>
          </div>
          <div class="panel-title pack-heading"><h3>Packs</h3></div>
          <div class="pack-form" *ngFor="let pack of draftPacks; let i = index">
            <strong>Pack {{i + 1}}</strong>
            <label>Label<input class="form-control" [(ngModel)]="pack.label" placeholder="Auto-generated"></label>
            <label>Size<input class="form-control" type="number" min="0.01" step="0.01" [(ngModel)]="pack.size"></label>
            <label>Unit
              <select class="form-select" [(ngModel)]="pack.unit">
                <option *ngFor="let unit of allowedUnits()" [value]="unit">{{unit}}</option>
              </select>
            </label>
            <label>MRP (₹)<input class="form-control" type="number" min="0" [(ngModel)]="pack.mrp"></label>
            <label>Cash price (₹)<input class="form-control" type="number" min="0" [(ngModel)]="pack.cashPrice"></label>
            <label>Credit price (₹)<input class="form-control" type="number" min="0" [(ngModel)]="pack.creditPrice"></label>
            <label class="check"><input type="checkbox" [(ngModel)]="pack.looseAllowed"> Allow loose sales</label>
            <button type="button" class="btn danger-button" *ngIf="draftPacks.length > 1" (click)="removeDraftPack(i)">Remove pack</button>
          </div>
          <button type="button" class="btn secondary-action add-pack" (click)="addDraftPack()"><i class="bi bi-plus-lg"></i> Add another pack</button>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <div class="button-row">
            <button type="button" class="btn btn-primary primary-action" (click)="saveProduct()">{{editingProductId ? 'Save product changes' : 'Save product'}}</button>
            <button *ngIf="editingProductId" type="button" class="btn secondary-action" (click)="resetProductForm()">Cancel edit</button>
          </div>
        </section>

        <section class="panel form-panel category-panel">
          <div class="panel-title"><h2>Categories</h2></div>
          <div class="category-form">
            <label>Category name<input class="form-control" [(ngModel)]="categoryName"></label>
            <label>Type
              <select class="form-select" [(ngModel)]="categoryType">
                <option>Solid</option>
                <option>Liquid</option>
                <option>Item</option>
              </select>
            </label>
            <label>Default GST %<input class="form-control" type="number" min="0" [(ngModel)]="categoryGst"></label>
            <div class="category-buttons">
              <button type="button" class="btn secondary-action" (click)="saveCategory()">{{editingCategoryId ? 'Save category' : 'Add category'}}</button>
              <button *ngIf="editingCategoryId" type="button" class="btn secondary-action" (click)="resetCategoryForm()">Cancel edit</button>
            </div>
          </div>
          <div class="category-list">
            <div class="category-row" *ngFor="let category of data.categories()">
              <span>{{category.name}} · {{category.product_type}} · {{category.active ? 'Active' : 'Inactive'}}</span>
              <button *ngIf="category.active" type="button" class="btn secondary-action" (click)="editCategory(category.id)">Edit</button>
              <button *ngIf="category.active" type="button" class="btn danger-button" (click)="deactivateCategory(category.id)">Deactivate</button>
            </div>
          </div>
        </section>

        <section class="panel table-panel">
          <div class="panel-title">
            <h2>Product catalog</h2>
            <div class="filters">
              <input class="form-control" [(ngModel)]="catalogSearch" placeholder="Search products">
              <select class="form-select" [(ngModel)]="catalogCategory">
                <option value="">All categories</option>
                <option *ngFor="let category of data.categories()" [value]="category.id">{{category.name}}</option>
              </select>
              <select class="form-select" [(ngModel)]="catalogBrand">
                <option value="">All brands</option>
                <option *ngFor="let brand of data.brands()" [value]="brand.id">{{brand.name}}</option>
              </select>
              <select class="form-select" [(ngModel)]="catalogStatus">
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <label class="filter-check"><input type="checkbox" [(ngModel)]="lowStockOnly"> Low stock only</label>
            </div>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Product</th><th>Brand / Category</th><th>Packs</th><th>Stock</th><th>Cash price</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>
                <tr *ngFor="let product of filteredProducts()">
                  <td><b>{{product.name}}</b><small class="table-sub">{{product.grade || ''}}</small></td>
                  <td>{{data.brandName(product.brand_id ?? '')}}<small class="table-sub">{{data.categoryName(product.category_id ?? '')}}</small></td>
                  <td>{{(product.packs ?? []).length}} pack(s)<small class="table-sub">{{packSummary(product)}}</small></td>
                  <td>{{data.totalStock(product) | number:'1.0-2'}} {{baseUnitOf(product)}}</td>
                  <td>{{(product.packs?.length ? product.packs[0].cash_price : 0) | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td><span class="status" [class.inactive]="!product.active">{{product.active ? 'Active' : 'Inactive'}}</span></td>
                  <td>
                    <div class="row-actions">
                      <button *ngIf="product.active" type="button" class="btn secondary-action" (click)="editProduct(product)">Edit</button>
                      <button *ngIf="product.active" type="button" class="btn danger-button" (click)="deactivateProduct(product.id)">Deactivate</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'stock'">
        <header class="page-heading"><div><span class="eyebrow">INVENTORY</span><h1>Stock</h1><p>Receive stock, adjust for damage or loss, and review the stock movement ledger.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Record stock movement</h2></div>
          <div class="form-grid three">
            <label>Movement
              <select class="form-select" [(ngModel)]="stockMode">
                <option value="in">Stock in (purchase)</option>
                <option value="adjustment">Adjustment (loss / damage)</option>
              </select>
            </label>
            <label>Product
              <select class="form-select" [(ngModel)]="stockProductId" (ngModelChange)="syncStockPack()">
                <option value="">Choose product</option>
                <option *ngFor="let product of activeProducts()" [value]="product.id">{{product.name}}</option>
              </select>
            </label>
            <label>Pack
              <select class="form-select" [(ngModel)]="stockPackId" (ngModelChange)="syncStockLot()">
                <option *ngFor="let pack of selectedStockProduct()?.packs ?? []" [value]="pack.id">{{packLabel(pack)}}</option>
              </select>
            </label>
            <label *ngIf="stockMode === 'adjustment'">Stock lot
              <select class="form-select" [(ngModel)]="stockLotId">
                <option value="">Choose lot</option>
                <option *ngFor="let lot of lotsForSelectedPack()" [value]="lot.id">
                  {{lot.batch_number || lot.received_date}} · Avail {{lot.available_base}}
                </option>
              </select>
            </label>
            <label>Quantity (packs for stock in; signed for adjustment)<input class="form-control" type="number" step="0.1" [(ngModel)]="stockQuantity"></label>
            <label *ngIf="stockMode === 'in'">Cost price per pack (₹)<input class="form-control" type="number" min="0" [(ngModel)]="stockCost"></label>
            <label *ngIf="stockMode === 'in'">Supplier<input class="form-control" [(ngModel)]="stockSupplier"></label>
            <label *ngIf="stockMode === 'in'">Batch number<input class="form-control" [(ngModel)]="stockBatch"></label>
            <label *ngIf="stockMode === 'in'">Expiry date<input class="form-control" type="date" [(ngModel)]="stockExpiry"></label>
            <label class="wide" *ngIf="stockMode === 'adjustment'">Reason<input class="form-control" [(ngModel)]="stockReason" placeholder="Required: damaged, lost, counted stock..."></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <button type="button" class="btn btn-primary primary-action" (click)="recordStock()">{{stockMode === 'in' ? 'Receive stock' : 'Save adjustment'}}</button>
        </section>
        <section class="panel table-panel">
          <div class="panel-title"><h2>Stock by product and pack</h2></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Product</th><th>Pack</th><th>Pack quantity</th><th>Base-unit stock</th><th>Low-stock level</th></tr></thead>
              <tbody>
                <ng-container *ngFor="let product of data.products()">
                  <tr *ngFor="let pack of product.packs ?? []">
                    <td>{{product.name}}</td>
                    <td>{{packLabel(pack)}}</td>
                    <td>{{data.stockInPacks(product, pack) | number:'1.0-2'}}</td>
                    <td>{{(product.stockBase?.[pack.id] ?? 0) | number:'1.0-2'}} {{baseUnitOf(product)}}</td>
                    <td>{{product.low_stock_level}} {{baseUnitOf(product)}}</td>
                  </tr>
                </ng-container>
              </tbody>
            </table>
          </div>
        </section>
        <section class="panel table-panel">
          <div class="panel-title"><h2>Stock ledger</h2></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Product</th><th>Movement</th><th>Quantity</th><th>Balance</th><th>Batch / reason</th></tr></thead>
              <tbody>
                <tr *ngFor="let entry of data.stockLedger()">
                  <td>{{entry.date | date:'dd MMM yyyy'}}</td>
                  <td>{{entry.productName}}</td>
                  <td>{{entry.type}}</td>
                  <td>{{entry.quantityBase | number:'1.0-2'}}</td>
                  <td>{{entry.balanceBase | number:'1.0-2'}}</td>
                  <td>{{entry.batchNo || entry.reason}}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'farmers'">
        <header class="page-heading"><div><span class="eyebrow">CUSTOMERS</span><h1>Farmers</h1><p>Keep customer contacts, opening balances and credit limits together.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Add farmer</h2></div>
          <div class="form-grid three">
            <label>Name<input class="form-control" [(ngModel)]="farmerName"></label>
            <label>Mobile<input class="form-control" type="tel" maxlength="10" [(ngModel)]="farmerMobile" placeholder="10-digit number"></label>
            <label>Village<input class="form-control" [(ngModel)]="farmerVillage"></label>
            <label>Address<input class="form-control" [(ngModel)]="farmerAddress"></label>
            <label>Land size (acres)<input class="form-control" type="number" min="0" [(ngModel)]="farmerLand"></label>
            <label>Credit limit (₹)<input class="form-control" type="number" min="0" [(ngModel)]="farmerCreditLimit"></label>
            <label>Opening balance (₹)<input class="form-control" type="number" [(ngModel)]="farmerOpening"></label>
            <label class="wide">Notes<input class="form-control" [(ngModel)]="farmerNotes"></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <button type="button" class="btn btn-primary primary-action" (click)="saveFarmer()">Add farmer</button>
        </section>
        <section class="panel table-panel">
          <div class="panel-title">
            <h2>Farmer directory</h2>
            <div class="filters">
              <input class="form-control" [(ngModel)]="farmerSearch" placeholder="Search farmers">
              <label class="filter-check"><input type="checkbox" [(ngModel)]="duesOnly"> Has dues</label>
              <label class="filter-check"><input type="checkbox" [(ngModel)]="overdueOnly"> Overdue</label>
            </div>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Farmer</th><th>Village</th><th>Mobile</th><th>Outstanding</th><th>Last bill</th><th></th></tr></thead>
              <tbody>
                <tr *ngFor="let farmer of filteredFarmers()">
                  <td><b>{{farmer.name}}</b></td>
                  <td>{{farmer.village || '—'}}</td>
                  <td>{{farmer.mobile}}</td>
                  <td [class.danger]="farmerOverdue(farmer.id)">{{data.farmerBalance(farmer.id) | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td>{{farmer.lastBillDate ? (farmer.lastBillDate | date:'dd MMM yyyy') : '—'}}</td>
                  <td><a class="btn secondary-action" routerLink="/app/khata" [queryParams]="{farmer:farmer.id}">View khata</a></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'seasons'">
        <header class="page-heading"><div><span class="eyebrow">PRICING RULES</span><h1>Seasons</h1><p>Set seasonal discounts, credit terms and due dates. Adjust them per bill when needed.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Create a season</h2></div>
          <div class="form-grid three">
            <label>Name<input class="form-control" [(ngModel)]="seasonName" placeholder="Kharif 2026"></label>
            <label>Start date<input class="form-control" type="date" [(ngModel)]="seasonStart"></label>
            <label>End date<input class="form-control" type="date" [(ngModel)]="seasonEnd"></label>
            <label>Default cash discount<input class="form-control" type="number" min="0" [(ngModel)]="seasonDiscount"></label>
            <label>Discount type
              <select class="form-select" [(ngModel)]="seasonDiscountType">
                <option value="amount">Fixed ₹</option>
                <option value="percent">Percent %</option>
              </select>
            </label>
            <label>Credit interest (% / month)<input class="form-control" type="number" min="0" step="0.1" [(ngModel)]="seasonInterest"></label>
            <label>Credit due date<input class="form-control" type="date" [(ngModel)]="seasonDue"></label>
            <label>Grace days<input class="form-control" type="number" min="0" [(ngModel)]="seasonGrace"></label>
            <label>Late interest (% / day)<input class="form-control" type="number" min="0" step="0.1" [(ngModel)]="seasonLateInterest"></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <button type="button" class="btn btn-primary primary-action" (click)="saveSeason()">Save season</button>
        </section>
        <section class="panel table-panel">
          <div class="panel-title"><h2>Season list</h2></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Dates</th><th>Cash discount</th><th>Credit interest</th><th>Due date</th><th>Status</th><th></th></tr></thead>
              <tbody>
                <tr *ngFor="let season of data.seasons()">
                  <td><b>{{season.name}}</b></td>
                  <td>{{season.start_date | date:'dd MMM yyyy'}} – {{season.end_date | date:'dd MMM yyyy'}}</td>
                  <td>{{season.discountType === 'amount' ? (season.default_cash_discount | currency:'INR':'symbol':'1.0-0':'en-IN') : season.default_cash_discount + '%'}}</td>
                  <td>{{season.default_credit_interest_per_month}}% / month</td>
                  <td>{{season.due_date ? (season.due_date | date:'dd MMM yyyy') : '—'}}</td>
                  <td><span class="status" [class.inactive]="season.active === false">{{season.active === false ? 'Inactive' : 'Active'}}</span></td>
                  <td><button class="btn danger-button" *ngIf="season.active !== false" (click)="deactivateSeason(season.id)">Deactivate</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'bills'">
        <header class="page-heading">
          <div><span class="eyebrow">SALES RECORDS</span><h1>Bills</h1><p>Review completed sales and outstanding customer credit.</p></div>
          <a class="btn btn-primary primary-action" routerLink="/app/pos"><i class="bi bi-cart-plus"></i> New Sale</a>
        </header>
        <section class="panel table-panel">
          <div class="panel-title"><h2>Bill register</h2><span>{{data.bills().length}} bills</span></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Bill number</th><th>Date</th><th>Farmer</th><th>Payment / status</th><th>Total</th><th>Paid now</th><th>Balance</th><th>Actions</th></tr></thead>
              <tbody>
                <tr *ngFor="let bill of data.bills()">
                  <td><b>{{bill.bill_number}}</b></td>
                  <td>{{bill.bill_date | date:'dd MMM yyyy'}}</td>
                  <td>{{bill.farmerName || farmerDisplayName(bill.farmer_id)}}</td>
                  <td>{{bill.payment_type}} · {{bill.status}}</td>
                  <td>{{bill.total | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td>{{bill.paid_now | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td [class.danger]="bill.balance > 0">{{bill.balance | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn secondary-action" (click)="printBill(bill.bill_number,'a4')">Print A4</button>
                      <button class="btn secondary-action" (click)="printBill(bill.bill_number,'thermal')">Print 80mm</button>
                      <button *ngIf="bill.status==='credit' || bill.status==='part-paid'" class="btn secondary-action" (click)="shareBill(bill.bill_number)">Share WhatsApp</button>
                      <button *ngIf="bill.status==='held' || (bill.payment_type==='credit' && bill.balance===bill.total)" class="btn danger-button" (click)="voidBill(bill.id)">Void bill</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p *ngIf="!data.bills().length" class="empty">No bills yet. Start a sale to create your first bill.</p>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'khata'">
        <header class="page-heading"><div><span class="eyebrow">CUSTOMER LEDGER</span><h1>Khata</h1><p>Receive payments and review each farmer's running account balance.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Receive payment</h2></div>
          <div class="form-grid three">
            <label>Farmer
              <select class="form-select" [(ngModel)]="paymentFarmerId">
                <option value="">Choose farmer</option>
                <option *ngFor="let farmer of data.farmers()" [value]="farmer.id">{{farmer.name}} · {{data.farmerBalance(farmer.id) | currency:'INR':'symbol':'1.0-0':'en-IN'}}</option>
              </select>
            </label>
            <label>Amount (₹)<input class="form-control" type="number" min="1" [(ngModel)]="paymentAmount"></label>
            <label>Payment mode
              <select class="form-select" [(ngModel)]="khataPaymentMode">
                <option>Cash</option>
                <option>UPI</option>
                <option>Bank</option>
              </select>
            </label>
            <label class="wide">Note<input class="form-control" [(ngModel)]="paymentNote"></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <button class="btn btn-primary primary-action" type="button" (click)="receivePayment()">Receive Payment</button>
        </section>
        <section class="panel table-panel">
          <div class="panel-title">
            <h2>Balances due</h2>
            <div class="button-row">
              <button class="btn secondary-action" type="button" (click)="printLedger()">Export / print ledger</button>
              <button class="btn secondary-action" type="button" (click)="sendReminder()">Send Reminder</button>
            </div>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Farmer</th><th>Mobile</th><th>Outstanding</th><th>Overdue</th><th>Last payment</th><th></th></tr></thead>
              <tbody>
                <tr *ngFor="let farmer of farmersWithDues()">
                  <td><b>{{farmer.name}}</b></td>
                  <td>{{farmer.mobile}}</td>
                  <td>{{data.farmerBalance(farmer.id) | currency:'INR':'symbol':'1.0-0':'en-IN'}}</td>
                  <td [class.danger]="farmerOverdue(farmer.id)">{{farmerOverdue(farmer.id) ? 'Overdue' : '—'}}</td>
                  <td>{{lastPayment(farmer.id) ? (lastPayment(farmer.id) | date:'dd MMM yyyy') : '—'}}</td>
                  <td><button type="button" class="btn secondary-action" (click)="selectPaymentFarmer(farmer.id)">Receive payment</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="panel table-panel">
          <div class="panel-title">
            <h2>Ledger entries</h2>
            <select class="form-select farmer-filter" [(ngModel)]="ledgerFarmerId">
              <option value="">All farmers</option>
              <option *ngFor="let farmer of data.farmers()" [value]="farmer.id">{{farmer.name}}</option>
            </select>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Farmer</th><th>Description</th><th>Bill</th><th>Debit</th><th>Credit</th><th>Balance</th></tr></thead>
              <tbody>
                <tr *ngFor="let entry of filteredLedger()">
                  <td>{{(entry.date || entry.created_at) | date:'dd MMM yyyy'}}</td>
                  <td>{{farmerDisplayName(entry.farmer_id)}}</td>
                  <td>{{entry.description}}</td>
                  <td>{{entry.billNumber || '—'}}</td>
                  <td>{{entry.debit > 0 ? (entry.debit | currency:'INR':'symbol':'1.0-0':'en-IN') : '—'}}</td>
                  <td>{{entry.credit > 0 ? (entry.credit | currency:'INR':'symbol':'1.0-0':'en-IN') : '—'}}</td>
                  <td>{{entry.balanceAfter != null ? (entry.balanceAfter | currency:'INR':'symbol':'1.0-0':'en-IN') : '—'}}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p *ngIf="!filteredLedger().length" class="empty">No ledger entries yet.</p>
        </section>
      </ng-container>

      <ng-container *ngSwitchCase="'settings'">
        <header class="page-heading"><div><span class="eyebrow">SHOP PROFILE</span><h1>Settings</h1><p>Update shop identity, tax preferences and your account details.</p></div></header>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Shop profile</h2></div>
          <div class="form-grid">
            <label>Shop name<input class="form-control" [(ngModel)]="settingsShopName"></label>
            <label>GSTIN<input class="form-control" [(ngModel)]="settingsGstin" placeholder="Optional"></label>
            <label class="wide">Shop address<textarea class="form-control" rows="3" [(ngModel)]="settingsAddress"></textarea></label>
          </div>
          <p class="error" *ngIf="feedback">{{feedback}}</p>
          <button type="button" class="btn btn-primary primary-action" (click)="saveSettings()">Save settings</button>
        </section>
        <section class="panel form-panel">
          <div class="panel-title"><h2>Tax and data</h2></div>
          <label class="settings-toggle"><input type="checkbox" [(ngModel)]="taxExclusive"> Prices are tax-exclusive (default is tax-inclusive)</label>
          <p class="hint">Tax settings are saved with your shop settings. Product GST rates are configured per product in Product Catalog.</p>
        </section>
      </ng-container>
    </ng-container>
    <div class="toast-message" role="status" *ngIf="notice">{{notice}}</div>
  `,
  styles: [`
    :host{display:block;max-width:1600px;margin:0 auto}
    .page-heading{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:0 0 22px}
    h1{font-size:clamp(28px,3vw,36px);margin:4px 0}.page-heading p{margin:0;color:#5c6b62}.eyebrow{font-size:14px;font-weight:800;letter-spacing:.1em;color:#0b6b3a}
    .panel{min-width:0;background:#fff;border:1.5px solid #cbd5ce;border-radius:12px;padding:20px;box-shadow:0 2px 6px #14211a08}
    .panel-title{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:16px}.panel-title h2,.panel-title h3{margin:0;font-size:20px}
    .kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.kpi{display:flex;flex-direction:column;gap:8px}.kpi>span{font-weight:700;color:#46564b}.kpi strong{font:800 30px var(--heading-font);color:#14211a}.kpi small{font-size:14px;color:#5c6b62}.kpi.warning strong{color:#a76a00}
    .quick-actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0}.quick{display:flex;align-items:center;gap:12px;min-height:76px;color:#14211a;text-decoration:none;font-size:17px;font-weight:800}.quick i{font-size:26px;color:#0b6b3a}.quick:hover{border-color:#0b6b3a}
    .dashboard-panels{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.dashboard-panels .panel{min-height:210px}.dashboard-panels .panel-title a{color:#0b6b3a;font-weight:700}
    .list-row{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:center;padding:11px 0;border-top:1px solid #e5eae6}.list-row span,.empty{color:#5c6b62}.empty{padding:10px 0}.danger,.error{color:#b42318!important}
    .primary-action,.secondary-action,.danger-button{min-height:48px;display:inline-flex;align-items:center;justify-content:center;gap:8px;font-size:16px;font-weight:800;white-space:nowrap}
    .primary-action{min-height:56px;font-size:18px}.danger-button{border:1.5px solid #b42318;background:#fff;color:#b42318}.danger-button:hover{background:#fff1f0}
    .form-panel,.table-panel{margin-bottom:16px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.form-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.form-grid label,.category-form label,.bill-options label{display:block;min-width:0;font-weight:700}
    .form-control,.form-select{min-height:52px;margin-top:6px;font-size:16px}.wide{grid-column:1/-1}.button-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
    .table-wrap{overflow:auto;max-height:560px;border:1px solid #d5ddd7;border-radius:8px}table{width:100%;border-collapse:separate;border-spacing:0;min-width:720px}
    th,td{height:56px;padding:10px 12px;border-bottom:1px solid #e0e6e1;text-align:left;vertical-align:middle}thead th{position:sticky;top:0;z-index:1;background:#f7f7f2;font-weight:800;border-bottom:1.5px solid #cbd5ce}tbody tr:nth-child(even){background:#fbfcfa}tbody tr:last-child td{border-bottom:0}
    .table-sub{display:block;color:#5c6b62;font-size:14px}.status{display:inline-block;padding:4px 9px;border-radius:20px;background:#edf7ec;color:#0b6b3a;font-weight:700}.status.inactive{background:#f1f3f1;color:#59635c}
    .row-actions{display:flex;gap:6px}.row-actions .btn{min-height:48px;padding:6px 10px}.filters{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.filters .form-control,.filters .form-select{width:auto;min-width:150px;margin:0}.filter-check,.check{display:flex!important;align-items:center;gap:8px;font-weight:600!important}.filter-check input,.check input{width:20px;height:20px}
    .pack-heading{margin:22px 0 12px}.pack-form{display:grid;grid-template-columns:80px repeat(3,minmax(100px,1fr));gap:10px;align-items:end;padding:14px;margin:10px 0;border:1.5px solid #d5ddd7;border-radius:10px;background:#fbfcfa}
    .pack-form label{font-weight:700}.pack-form .form-control,.pack-form .form-select{margin-top:5px}.pack-form .check{align-self:center}.add-pack{margin:8px 0 16px}
    .category-form{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:end}.category-buttons{display:flex;flex-wrap:wrap;gap:6px}.category-list{display:grid;gap:8px;margin-top:14px}.category-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px;border:1px solid #cbd5ce;border-radius:8px;background:#f7f7f2}.category-row span{flex:1}
    .pos-layout{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(380px,.9fr);gap:16px;align-items:start}.search{display:flex;align-items:center;gap:8px;border:1px solid #cbd5ce;border-radius:8px;padding:0 10px}.search input{height:42px;width:220px;border:0;outline:0;font:inherit}.product-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
    .product-tile{min-height:120px;display:flex;flex-direction:column;align-items:flex-start;justify-content:space-between;gap:6px;padding:12px;border:1.5px solid #cbd5ce;border-radius:10px;background:#fff;text-align:left;font:inherit}.product-tile:hover{border-color:#0b6b3a;background:#f7fbf6}.product-tile span,.product-tile small{color:#5c6b62}.product-tile small{font-size:14px}.tile-actions{display:flex;flex-direction:column;width:100%;gap:6px}.tile-actions .btn{width:100%;min-height:48px;white-space:normal}
    .bill-builder>label{display:block;margin:10px 0 5px;font-weight:700}.bill-builder>.form-select{margin-bottom:8px}.bill-number{color:#5c6b62}.cart-lines{margin:14px 0;border-top:1px solid #d5ddd7}.cart-line{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid #e5eae6}.cart-line small{display:block;color:#5c6b62;font-size:14px}.quantity{display:flex;align-items:center;gap:5px}.quantity button{min-width:48px;min-height:48px;border:1px solid #cbd5ce;border-radius:7px;background:white;font-size:20px}.cart-empty{border:1px dashed #cbd5ce;border-radius:8px;padding:16px}
    .bill-options{display:grid;grid-template-columns:1fr 1fr;gap:10px}.bill-options .form-control,.bill-options .form-select{margin-top:5px}.totals{padding:12px;margin:14px 0;border:1.5px solid #cbd5ce;border-radius:9px;background:#f7f7f2}.totals>div{display:flex;justify-content:space-between;gap:10px;padding:6px 0}.grand-total{border-top:1px solid #cbd5ce;margin-top:4px;padding-top:12px!important;font-size:19px}.interest-copy{margin:8px 0 0;color:#0b6b3a;font-weight:700}.bill-actions{display:flex;flex-wrap:wrap;gap:8px}.bill-actions>*{flex:1}
    .farmer-filter{max-width:220px;margin:0}.settings-toggle{display:flex;align-items:center;gap:10px;font-weight:700}.settings-toggle input{width:22px;height:22px}
    .toast-message{position:fixed;right:24px;bottom:55px;z-index:20;padding:14px 18px;border:1.5px solid #0b6b3a;border-radius:10px;background:#edf7ec;color:#0b6b3a;font-weight:700;box-shadow:0 8px 20px #14211a22}
    @media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.dashboard-panels{grid-template-columns:1fr 1fr}.dashboard-panels .panel:first-child{grid-column:1/-1}.pos-layout{grid-template-columns:minmax(0,1fr) minmax(340px,.9fr)}.pack-form{grid-template-columns:repeat(3,minmax(100px,1fr))}.pack-form>strong{grid-column:1/-1}}
    @media(max-width:760px){.page-heading{align-items:flex-start}.kpi-grid{gap:8px}.kpi{padding:14px}.kpi strong{font-size:24px}.quick-actions{grid-template-columns:1fr 1fr}.dashboard-panels{grid-template-columns:1fr}.dashboard-panels .panel:first-child{grid-column:auto}.pos-layout{grid-template-columns:1fr}.bill-options{grid-template-columns:1fr 1fr}.category-form{grid-template-columns:1fr 1fr}.filters{align-items:stretch}.filters .form-control,.filters .form-select{flex:1;min-width:130px}}
    @media(max-width:500px){.page-heading{flex-direction:column}.page-heading>.btn{width:100%}.panel{padding:14px}.form-grid,.form-grid.three{grid-template-columns:1fr}.wide{grid-column:auto}.pack-form{grid-template-columns:1fr 1fr}.category-form{grid-template-columns:1fr}.bill-options{grid-template-columns:1fr}.cart-line{grid-template-columns:minmax(0,1fr) auto}.cart-line>strong{grid-column:2}.search input{width:120px}.bill-actions{flex-direction:column}.kpi-grid{grid-template-columns:1fr 1fr}.quick{font-size:15px;min-height:66px}.list-row{grid-template-columns:1fr auto}.list-row span{grid-row:2}.list-row strong{grid-column:2;grid-row:1/3}}
    @media print{.page-heading,.form-panel,.button-row,.sidebar,.topbar,.statusbar{display:none!important}.panel{box-shadow:none}}
  `]
})
export class AppFeatureComponent {
  readonly route = inject(ActivatedRoute);
  readonly data = inject(ShopDataService);
  readonly tenant = inject(TenantService);
  readonly auth = inject(AuthService);
  readonly page = String(this.route.snapshot.data['page'] ?? 'dashboard');

  get ownerName(): string { return this.auth.profile()?.name ?? 'shop owner'; }
  readonly dayPart = new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening';
  feedback = '';
  notice = '';

  brandName = '';
  brandManufacturer = '';
  brandNotes = '';
  editingBrandId = '';

  productName = '';
  editingProductId = '';
  productBrand = '';
  productCategory = '';
  productType: ProductType = 'Solid';
  productGrade = '';
  productHsn = '';
  productGst = 5;
  productLowStock = 100;
  draftPacks: DraftPack[] = [this.newPack()];

  categoryName = '';
  editingCategoryId = '';
  categoryType: ProductType = 'Solid';
  categoryGst = 5;

  catalogSearch = '';
  catalogCategory = '';
  catalogBrand = '';
  catalogStatus: 'all' | 'active' | 'inactive' = 'all';
  lowStockOnly = false;

  productSearch = '';
  cart: BillLine[] = [];
  selectedFarmerId = '';
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

  stockMode: 'in' | 'adjustment' = 'in';
  stockProductId = '';
  stockPackId = '';
  stockLotId = '';
  stockQuantity = 1;
  stockCost = 0;
  stockSupplier = '';
  stockBatch = '';
  stockExpiry = '';
  stockReason = '';

  farmerName = '';
  farmerMobile = '';
  farmerVillage = '';
  farmerAddress = '';
  farmerLand: number | null = null;
  farmerCreditLimit: number | null = null;
  farmerOpening = 0;
  farmerNotes = '';
  farmerSearch = '';
  duesOnly = false;
  overdueOnly = false;

  seasonName = '';
  seasonStart = '';
  seasonEnd = '';
  seasonDiscount = 0;
  seasonDiscountType: 'amount' | 'percent' = 'amount';
  seasonInterest = 1;
  seasonDue = '';
  seasonGrace = 0;
  seasonLateInterest = 1;

  paymentFarmerId = '';
  paymentAmount = 0;
  khataPaymentMode = 'Cash';
  paymentNote = '';
  ledgerFarmerId = '';

  settingsShopName = this.tenant.tenant()?.name ?? '';
  settingsGstin = this.tenant.tenant()?.gstin ?? '';
  settingsAddress = String(this.data.settings()?.values?.['address'] ?? '');
  taxExclusive = Boolean(this.data.settings()?.values?.['tax_exclusive'] ?? false);

  readonly farmersWithDues = computed(() =>
    this.data.farmers().filter(farmer => this.data.farmerBalance(farmer.id) > 0)
  );

  // ---- POS derived totals -------------------------------------------------
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

  get principal(): number {
    return this.subtotal - this.spotDiscount + (this.taxExclusive ? this.taxAmount : 0);
  }

  get creditInterest(): number {
    if (this.paymentType === 'cash') return 0;
    return calcCreditTotal(this.principal, this.interestPct, this.months, this.paymentType === 'part' ? this.paidNow : 0).interest;
  }

  get total(): number {
    if (this.paymentType === 'cash') return Math.round(this.principal);
    return calcCreditTotal(this.principal, this.interestPct, this.months, this.paymentType === 'part' ? this.paidNow : 0).total;
  }

  get rounding(): number {
    const beforeRounding = this.paymentType === 'cash'
      ? this.principal
      : this.principal + this.creditInterest;
    return Math.round(beforeRounding) - beforeRounding;
  }

  get boundedPaidNow(): number { return Math.min(this.total, Math.max(0, this.paidNow)); }
  get balance(): number { return Math.max(0, this.total - (this.paymentType === 'part' ? this.boundedPaidNow : 0)); }
  get baseUnit(): 'kg' | 'L' | 'piece' {
    return this.productType === 'Liquid' ? 'L' : this.productType === 'Item' ? 'piece' : 'kg';
  }

  // ---- Display & unit helpers ---------------------------------------------
  baseUnitOf(product: Product): string {
    if (product.unit_type === 'Liquid' || product.unit_type === 'L') return 'L';
    if (product.unit_type === 'Item' || product.unit_type === 'piece') return 'piece';
    return 'kg';
  }

  packLabel(pack: Pack): string {
    return `${pack.size} ${pack.size_unit}`;
  }

  activeBrands() { return this.data.brands().filter(item => item.active); }
  activeCategories() { return this.data.categories().filter(item => item.active); }
  activeProducts() { return this.data.products().filter(item => item.active); }
  activeSeasons() { return this.data.seasons().filter(item => item.active !== false); }

  allowedUnits(): PackUnit[] {
    return this.productType === 'Liquid'
      ? ['ml', 'L']
      : this.productType === 'Item'
        ? ['piece', 'set']
        : ['g', 'kg', 'bag'];
  }

  // ---- Products & Categories ----------------------------------------------
  syncProductType(): void {
    const category = this.data.categories().find(item => item.id === this.productCategory);
    if (category) {
      this.productType = (category.product_type as ProductType) || 'Solid';
    }
    this.draftPacks = this.draftPacks.map(pack => ({ ...pack, unit: this.allowedUnits()[0] }));
  }

  addDraftPack(): void { this.draftPacks.push(this.newPack()); }
  removeDraftPack(index: number): void { this.draftPacks.splice(index, 1); }

  async saveProduct(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.productName.trim() || !this.productBrand || !this.productCategory) {
        throw new Error('Enter a product name and choose its brand and category.');
      }
      if (this.draftPacks.some(pack => pack.size <= 0 || pack.mrp < 0)) {
        throw new Error('Each pack needs a size greater than zero and a valid MRP.');
      }
      const packInputs: ProductPackInput[] = this.draftPacks.map(pack => ({ ...pack }));
      const input: ProductCreate = {
        name: this.productName.trim(),
        brand_id: this.productBrand,
        category_id: this.productCategory,
        unit_type: this.productType,
        grade: this.productGrade.trim() || null,
        hsn: this.productHsn.trim() || null,
        gst_rate: this.productGst,
        low_stock_level: Math.max(0, this.productLowStock),
        active: true,
      };
      if (this.editingProductId) {
        await this.data.updateProduct(this.editingProductId, input, packInputs);
      } else {
        await this.data.addProduct(input, packInputs);
      }
      this.resetProductForm();
      this.showNotice('Product saved with its pack sizes.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  editProduct(product: Product): void {
    this.editingProductId = product.id;
    this.productName = product.name;
    this.productBrand = product.brand_id ?? '';
    this.productCategory = product.category_id ?? '';
    this.productType = (product.unit_type as ProductType) || 'Solid';
    this.productGrade = product.grade ?? '';
    this.productHsn = product.hsn ?? '';
    this.productGst = product.gst_rate;
    this.productLowStock = product.low_stock_level;
    this.draftPacks = (product.packs ?? []).length
      ? (product.packs ?? []).map(pack => ({
          label: this.packLabel(pack),
          size: pack.size,
          unit: pack.size_unit as PackUnit,
          mrp: pack.mrp,
          cashPrice: pack.cash_price,
          creditPrice: pack.credit_price,
          looseAllowed: pack.allow_loose_sale,
        }))
      : [this.newPack()];
    document.querySelector('.form-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  resetProductForm(): void {
    this.editingProductId = '';
    this.productName = '';
    this.productBrand = '';
    this.productCategory = '';
    this.productType = 'Solid';
    this.productGrade = '';
    this.productHsn = '';
    this.productGst = 5;
    this.productLowStock = 100;
    this.draftPacks = [this.newPack()];
    this.feedback = '';
  }

  async saveCategory(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.categoryName.trim()) {
        this.feedback = 'Enter a category name.';
        return;
      }
      if (this.editingCategoryId) {
        const current = this.data.categories().find(category => category.id === this.editingCategoryId);
        if (current && current.product_type !== this.categoryType && this.data.products().some(p => p.active && p.category_id === current.id)) {
          this.feedback = 'Category type cannot change while active products use this category.';
          return;
        }
        await this.data.updateCategory(this.editingCategoryId, this.categoryName, this.categoryType, this.categoryGst);
      } else {
        await this.data.addCategory(this.categoryName, this.categoryType, this.categoryGst);
      }
      this.resetCategoryForm();
      this.showNotice('Category saved.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  editCategory(id: string): void {
    const category = this.data.categories().find(item => item.id === id);
    if (!category) return;
    this.editingCategoryId = id;
    this.categoryName = category.name;
    this.categoryType = (category.product_type as ProductType) || 'Solid';
  }

  resetCategoryForm(): void {
    this.editingCategoryId = '';
    this.categoryName = '';
    this.categoryType = 'Solid';
    this.categoryGst = 5;
  }

  async deactivateCategory(id: string): Promise<void> {
    if (this.data.products().some(product => product.active && product.category_id === id)) {
      this.feedback = 'A category with active products cannot be deactivated.';
      return;
    }
    if (confirm('Deactivate this category?')) {
      try {
        await this.data.deactivateCategory(id);
      } catch (error) {
        this.feedback = this.message(error);
      }
    }
  }

  filteredProducts() {
    const query = this.catalogSearch.trim().toLowerCase();
    return this.data.products().filter(product =>
      (!query || `${product.name} ${product.grade ?? ''}`.toLowerCase().includes(query))
      && (!this.catalogCategory || product.category_id === this.catalogCategory)
      && (!this.catalogBrand || product.brand_id === this.catalogBrand)
      && (this.catalogStatus === 'all' || (this.catalogStatus === 'active' ? product.active : !product.active))
      && (!this.lowStockOnly || this.data.totalStock(product) <= product.low_stock_level)
    );
  }

  packSummary(product: Product): string {
    return (product.packs ?? []).map(pack => this.packLabel(pack)).join(', ');
  }

  productCount(brandId: string): number {
    return this.data.products().filter(product => product.brand_id === brandId).length;
  }

  async deactivateProduct(id: string): Promise<void> {
    if (confirm('Deactivate this product? It will no longer appear in sales.')) {
      try {
        await this.data.deactivateProduct(id);
      } catch (error) {
        this.feedback = this.message(error);
      }
    }
  }

  // ---- Brands -------------------------------------------------------------
  async saveBrand(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.brandName.trim()) {
        this.feedback = 'Enter a brand name.';
        return;
      }
      if (this.editingBrandId) {
        await this.data.updateBrand(this.editingBrandId, this.brandName, this.brandManufacturer, this.brandNotes);
      } else {
        await this.data.addBrand(this.brandName, this.brandManufacturer, this.brandNotes);
      }
      this.resetBrandForm();
      this.showNotice('Brand saved.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  editBrand(id: string): void {
    const brand = this.data.brands().find(item => item.id === id);
    if (!brand) return;
    this.editingBrandId = id;
    this.brandName = brand.name;
    this.brandManufacturer = brand.manufacturer;
    this.brandNotes = brand.notes;
  }

  resetBrandForm(): void {
    this.editingBrandId = '';
    this.brandName = '';
    this.brandManufacturer = '';
    this.brandNotes = '';
    this.feedback = '';
  }

  async deactivateBrand(id: string): Promise<void> {
    const msg = this.productCount(id) > 0
      ? 'This brand has products and cannot be deleted. Deactivate the brand?'
      : 'Deactivate this brand?';
    if (confirm(msg)) {
      try {
        await this.data.deactivateBrand(id);
      } catch (error) {
        this.feedback = this.message(error);
      }
    }
  }

  // ---- POS / Cart ---------------------------------------------------------
  filteredPackOptions() {
    const query = this.productSearch.trim().toLowerCase();
    return this.activeProducts()
      .flatMap(product => (product.packs ?? []).map(pack => ({ product, pack })))
      .filter(option => !query || `${option.product.name} ${this.packLabel(option.pack)}`.toLowerCase().includes(query));
  }

  addToCart(productId: string, packId: string, loose = false): void {
    const product = this.data.product(productId);
    const pack = product?.packs?.find(item => item.id === packId);
    if (!product || !pack) return;
    const stockBase = product.stockBase?.[pack.id] ?? 0;
    const quantityBase = loose ? 1 : pack.size_in_base_unit;
    const lineLabel = loose ? `Loose ${this.baseUnitOf(product)}` : this.packLabel(pack);
    const existing = this.cart.find(line => line.productId === product.id && line.pack_id === pack.id && line.pack_name === lineLabel);

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
        id: '',
        tenant_id: '',
        created_at: now,
        updated_at: now,
        version: 1,
        bill_id: '',
        pack_id: packId,
        product_name: product.name,
        pack_name: lineLabel,
        quantity: 1,
        quantity_base: quantityBase,
        unit_price: unitPrice,
        line_total: Math.round(unitPrice),
        productId,
        gstPercent: product.gst_rate,
      });
    }
  }

  paymentChanged(paymentType: PaymentType): void {
    this.paymentType = paymentType;
    for (const line of this.cart) {
      const pack = this.data.product(line.productId ?? '')?.packs?.find(item => item.id === line.pack_id);
      if (!pack) continue;
      const loose = line.pack_name.startsWith('Loose ');
      line.unit_price = (paymentType === 'credit' ? pack.credit_price : pack.cash_price) / (loose ? pack.size_in_base_unit : 1);
      line.line_total = Math.round(line.unit_price * line.quantity);
    }
  }

  changeCartQuantity(index: number, delta: number): void {
    const line = this.cart[index];
    if (!line) return;
    const product = this.data.product(line.productId ?? '');
    const pack = product?.packs?.find(item => item.id === line.pack_id);
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

  async saveSale(hold = false): Promise<void> {
    this.feedback = '';
    try {
      if (!this.cart.length) throw new Error('Add at least one product to the bill.');
      const bill = await this.data.saveBill({
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
      this.showNotice(hold ? `Bill ${bill.bill_number} held.` : `Bill ${bill.bill_number} saved.`);
      this.clearCart();
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  cancelDraft(): void {
    if (this.cart.length && !confirm('Cancel this unsaved bill and clear its items?')) return;
    this.clearCart();
  }

  seasonChanged(id: string): void {
    const season = this.data.seasons().find(item => item.id === id);
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

  clearCart(): void {
    this.cart = [];
    this.discount = 0;
    this.paidNow = 0;
    this.feedback = '';
  }

  // ---- Stock --------------------------------------------------------------
  selectedStockProduct(): Product | undefined {
    return this.data.product(this.stockProductId);
  }

  lotsForSelectedPack(): StockLot[] {
    return this.data.stockLots().filter(lot => lot.pack_id === this.stockPackId);
  }

  syncStockPack(): void {
    this.stockPackId = this.selectedStockProduct()?.packs?.[0]?.id ?? '';
    this.syncStockLot();
  }

  syncStockLot(): void {
    this.stockLotId = this.lotsForSelectedPack()[0]?.id ?? '';
  }

  async recordStock(): Promise<void> {
    this.feedback = '';
    try {
      const product = this.selectedStockProduct();
      const pack = product?.packs?.find(item => item.id === this.stockPackId);
      if (!product || !pack) throw new Error('Choose a product and pack.');

      const quantityBase = this.stockQuantity * pack.size_in_base_unit;
      if (this.stockMode === 'in') {
        await this.data.stockIn(
          this.stockPackId,
          quantityBase,
          this.stockSupplier,
          this.stockBatch,
          this.stockExpiry,
          this.stockCost,
        );
      } else {
        if (!this.stockLotId) throw new Error('Choose a stock lot to adjust.');
        const wouldGoNegative = (product.stockBase?.[pack.id] ?? 0) + quantityBase < 0;
        if (wouldGoNegative && !confirm('This adjustment will create negative stock. Confirm to continue.')) {
          return;
        }
        await this.data.adjustStock(this.stockLotId, quantityBase, this.stockReason);
      }
      this.showNotice('Stock movement recorded.');
      this.stockQuantity = 1;
      this.stockReason = '';
      this.stockBatch = '';
      this.stockExpiry = '';
      this.stockSupplier = '';
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  // ---- Farmers ------------------------------------------------------------
  async saveFarmer(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.farmerName.trim() || !/^[6-9]\d{9}$/.test(this.farmerMobile)) {
        throw new Error('Enter a farmer name and valid 10-digit mobile number.');
      }
      await this.data.addFarmer({
        name: this.farmerName.trim(),
        mobile: this.farmerMobile,
        village: this.farmerVillage.trim() || null,
        address: this.farmerAddress.trim() || null,
        opening_balance: this.farmerOpening,
        active: true,
      });
      this.farmerName = '';
      this.farmerMobile = '';
      this.farmerVillage = '';
      this.farmerAddress = '';
      this.farmerLand = null;
      this.farmerCreditLimit = null;
      this.farmerOpening = 0;
      this.farmerNotes = '';
      this.showNotice('Farmer added.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  filteredFarmers() {
    const query = this.farmerSearch.trim().toLowerCase();
    return this.data.farmers().filter(farmer =>
      (!query || `${farmer.name} ${farmer.mobile} ${farmer.village ?? ''}`.toLowerCase().includes(query))
      && (!this.duesOnly || this.data.farmerBalance(farmer.id) > 0)
      && (!this.overdueOnly || this.farmerOverdue(farmer.id))
    );
  }

  farmerOverdue(farmerId: string): boolean {
    const grace = Math.max(0, ...this.data.seasons().map(season => season.grace_days));
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - grace);
    return this.data.bills().some(
      bill => bill.farmer_id === farmerId && bill.balance > 0 && !!bill.due_date && new Date(`${bill.due_date}T00:00:00`) < cutoff
    );
  }

  // ---- Seasons ------------------------------------------------------------
  async saveSeason(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.seasonName.trim() || !this.seasonStart || !this.seasonEnd || this.seasonEnd < this.seasonStart) {
        this.feedback = 'Enter a name and a valid season date range.';
        return;
      }
      await this.data.addSeason({
        name: this.seasonName.trim(),
        start_date: this.seasonStart,
        end_date: this.seasonEnd,
        default_cash_discount: this.seasonDiscount,
        default_credit_interest_per_month: this.seasonInterest,
        due_date: this.seasonDue || this.seasonEnd,
        grace_days: this.seasonGrace,
        late_interest_per_day: this.seasonLateInterest,
      });
      this.seasonName = '';
      this.showNotice('Season saved.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  async deactivateSeason(id: string): Promise<void> {
    try {
      await this.data.deactivateSeason(id);
      this.showNotice('Season updated.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  // ---- Khata & Payments ---------------------------------------------------
  async receivePayment(): Promise<void> {
    this.feedback = '';
    try {
      await this.data.receivePayment(this.paymentFarmerId, this.paymentAmount, this.khataPaymentMode, this.paymentNote);
      this.showNotice('Payment received and allocated to oldest unpaid bills.');
      this.paymentAmount = 0;
      this.paymentNote = '';
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  selectPaymentFarmer(id: string): void {
    this.paymentFarmerId = id;
    document.querySelector('.form-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  filteredLedger() {
    return this.data.khataEntries().filter(entry => !this.ledgerFarmerId || entry.farmer_id === this.ledgerFarmerId);
  }

  farmerDisplayName(id: string): string {
    return this.data.farmers().find(item => item.id === id)?.name ?? 'Walk-in customer';
  }

  lastPayment(id: string): string | null {
    const entry = this.data.khataEntries().find(e => e.farmer_id === id && e.description.startsWith('Payment'));
    return entry ? (entry.date ?? entry.created_at) : null;
  }

  printLedger(): void { window.print(); }
  sendReminder(): void { this.showNotice('Reminder sharing can be connected when WhatsApp integration is available.'); }

  // ---- Bills --------------------------------------------------------------
  printBill(billNumber: string, format: 'a4' | 'thermal' = 'a4'): void {
    const bill = this.data.bills().find(item => item.bill_number === billNumber);
    if (!bill) { this.showNotice('Bill not found.'); return; }
    const popup = window.open('', '_blank');
    if (!popup) { this.showNotice('Allow pop-ups to print this invoice.'); return; }
    popup.opener = null;
    const customerName = bill.farmerName || this.farmerDisplayName(bill.farmer_id);
    const rows = (bill.lines ?? []).map(line =>
      `<tr><td>${this.escapeHtml(line.product_name)}<small>${this.escapeHtml(line.pack_name)}</small></td><td>${line.quantity}</td><td>${this.money(line.unit_price)}</td><td>${this.money(line.line_total)}</td></tr>`
    ).join('');
    popup.document.write(`<!doctype html><html><head><title>${this.escapeHtml(bill.bill_number)}</title><style>
      body{font:14px Arial,sans-serif;color:#14211a;margin:24px}main{max-width:780px;margin:auto}h1{font-size:24px;margin:0}p{margin:5px 0}.header{display:flex;justify-content:space-between;border-bottom:1px solid #bbb;padding-bottom:12px}.meta{margin:16px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid #ccc}th{background:#f4f4f4}small{display:block;color:#555}.totals{margin:16px 0 0 auto;width:260px}.totals div{display:flex;justify-content:space-between;padding:5px;border-bottom:1px solid #ddd}.terms{margin-top:16px;padding:12px;border:1px solid #ccc}
      @page{size:${format === 'thermal' ? '80mm auto' : 'A4'};margin:${format === 'thermal' ? '4mm' : '14mm'}}
      @media print{body{margin:0}main{max-width:none}.no-print{display:none}}
    </style></head><body><main><div class="header"><div><h1>${this.escapeHtml(this.tenant.tenant()?.name ?? 'My Shop')}</h1><p>Ferti+ Shop Owner</p>${this.tenant.tenant()?.gstin ? `<p>GSTIN: ${this.escapeHtml(this.tenant.tenant()?.gstin ?? '')}</p>` : ''}</div><div><h2>Invoice</h2><p>${this.escapeHtml(bill.bill_number)}</p><p>${this.escapeHtml(bill.bill_date)}</p></div></div><div class="meta"><b>Customer:</b> ${this.escapeHtml(customerName)}<br><b>Payment:</b> ${this.escapeHtml(bill.payment_type)}</div><table><thead><tr><th>Item / pack</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead><tbody>${rows}</tbody></table><div class="totals"><div><span>Subtotal</span><b>${this.money(bill.subtotal)}</b></div><div><span>Discount</span><b>−${this.money(bill.discount)}</b></div><div><span>Taxable value</span><b>${this.money(bill.taxableValue ?? 0)}</b></div><div><span>CGST</span><b>${this.money(bill.cgst ?? 0)}</b></div><div><span>SGST</span><b>${this.money(bill.sgst ?? 0)}</b></div>${bill.interest_amount ? `<div><span>Interest (${bill.interestPct ?? 0}% × ${bill.months ?? 0} months)</span><b>${this.money(bill.interest_amount)}</b></div>` : ''}<div><span>Rounding</span><b>${this.money(bill.rounding ?? bill.round_off)}</b></div><div><span>Total</span><b>${this.money(bill.total)}</b></div><div><span>Paid now</span><b>${this.money(bill.paid_now)}</b></div><div><span>Balance</span><b>${this.money(bill.balance)}</b></div></div>${bill.due_date ? `<div class="terms">Credit due date: ${this.escapeHtml(bill.due_date)}</div>` : ''}<p style="margin-top:28px">Thank you for your business.</p><button class="no-print" onclick="window.print()">Print / save PDF</button></main></body></html>`);
    popup.document.close();
    popup.focus();
    setTimeout(() => popup.print(), 250);
  }

  shareBill(billNumber: string): void {
    const bill = this.data.bills().find(item => item.bill_number === billNumber);
    if (!bill) { this.showNotice('Bill not found.'); return; }
    const customerName = bill.farmerName || this.farmerDisplayName(bill.farmer_id);
    const text = `${this.tenant.tenant()?.name ?? 'My Shop'}: bill ${bill.bill_number} for ${customerName}. Total ₹${bill.total.toLocaleString('en-IN')}, balance ₹${bill.balance.toLocaleString('en-IN')}.`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
  }

  async voidBill(id: string): Promise<void> {
    const reason = prompt('Reason for voiding this bill:');
    if (!reason?.trim()) return;
    try {
      await this.data.voidBill(id, reason);
      this.showNotice('Bill voided and stock / khata reversed.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  // ---- Settings -----------------------------------------------------------
  async saveSettings(): Promise<void> {
    this.feedback = '';
    if (!this.settingsShopName.trim()) {
      this.feedback = 'Shop name cannot be empty.';
      return;
    }
    try {
      this.tenant.updateName(this.settingsShopName);
      await this.data.saveSettings({
        ...(this.data.settings()?.values ?? {}),
        shop_name: this.settingsShopName.trim(),
        gstin: this.settingsGstin.trim(),
        address: this.settingsAddress.trim(),
        tax_exclusive: this.taxExclusive,
      });
      this.showNotice('Shop profile saved.');
    } catch (error) {
      this.feedback = this.message(error);
    }
  }

  // ---- Helpers ------------------------------------------------------------
  private newPack(): DraftPack {
    return { label: '', size: 1, unit: this.allowedUnits()[0], mrp: 0, cashPrice: 0, creditPrice: 0, looseAllowed: false };
  }

  private money(value: number): string {
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character] ?? character);
  }

  private showNotice(message: string): void {
    this.notice = message;
    setTimeout(() => this.notice = '', 3200);
  }

  private message(error: unknown): string {
    return error instanceof Error ? error.message : 'The requested action could not be completed.';
  }
}