import { CommonModule, CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrandService } from '../core/brand.service';
import { CategoryService } from '../core/category.service';
import { NoticeService } from '../core/notice.service';
import { ProductService } from '../core/product.service';
import { Pack, PackUnit, Product, ProductCreate, ProductPackInput, ProductType } from '../models';

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
  selector: 'app-products-page',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyPipe, DecimalPipe],
  templateUrl: './products.component.html',
  styleUrls: ['./products.component.scss'],
})
export class ProductsPageComponent {
  readonly productService = inject(ProductService);
  readonly brandService = inject(BrandService);
  readonly categoryService = inject(CategoryService);
  private readonly notice = inject(NoticeService);

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
  feedback = '';

  get baseUnit(): 'kg' | 'L' | 'piece' {
    return this.productType === 'Liquid' ? 'L' : this.productType === 'Item' ? 'piece' : 'kg';
  }

  activeBrands() { return this.brandService.brands().filter(b => b.active); }
  activeCategories() { return this.categoryService.categories().filter(c => c.active); }

  allowedUnits(): PackUnit[] {
    return this.productType === 'Liquid' ? ['ml', 'L']
      : this.productType === 'Item' ? ['piece', 'set']
      : ['g', 'kg', 'bag'];
  }

  baseUnitOf(product: Product): string {
    if (product.unit_type === 'Liquid' || product.unit_type === 'L') return 'L';
    if (product.unit_type === 'Item' || product.unit_type === 'piece') return 'piece';
    return 'kg';
  }

  packLabel(pack: Pack): string { return `${pack.size} ${pack.size_unit}`; }
  packSummary(product: Product): string { return (product.packs ?? []).map(p => this.packLabel(p)).join(', '); }

  syncProductType(): void {
    const category = this.categoryService.categories().find(c => c.id === this.productCategory);
    if (category) this.productType = (category.product_type as ProductType) || 'Solid';
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
      if (this.draftPacks.some(p => p.size <= 0 || p.mrp < 0)) {
        throw new Error('Each pack needs a size greater than zero and a valid MRP.');
      }
      const packInputs: ProductPackInput[] = this.draftPacks.map(p => ({ ...p }));
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
        await this.productService.updateProduct(this.editingProductId, input, packInputs);
      } else {
        await this.productService.addProduct(input, packInputs);
      }
      this.resetProductForm();
      this.notice.show('Product saved with its pack sizes.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save product.';
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
      ? (product.packs ?? []).map(p => ({
          label: this.packLabel(p),
          size: p.size,
          unit: p.size_unit as PackUnit,
          mrp: p.mrp,
          cashPrice: p.cash_price,
          creditPrice: p.credit_price,
          looseAllowed: p.allow_loose_sale,
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

  async deactivateProduct(id: string): Promise<void> {
    if (confirm('Deactivate this product? It will no longer appear in sales.')) {
      try {
        await this.productService.deactivateProduct(id);
        this.notice.show('Product deactivated.');
      } catch (error) {
        this.feedback = error instanceof Error ? error.message : 'Could not deactivate product.';
      }
    }
  }

  async saveCategory(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.categoryName.trim()) {
        this.feedback = 'Enter a category name.';
        return;
      }
      if (this.editingCategoryId) {
        const current = this.categoryService.categories().find(c => c.id === this.editingCategoryId);
        if (current && current.product_type !== this.categoryType &&
            this.productService.products().some(p => p.active && p.category_id === current.id)) {
          this.feedback = 'Category type cannot change while active products use this category.';
          return;
        }
        await this.categoryService.updateCategory(this.editingCategoryId, this.categoryName, this.categoryType, this.categoryGst);
      } else {
        await this.categoryService.addCategory(this.categoryName, this.categoryType, this.categoryGst);
      }
      this.resetCategoryForm();
      this.notice.show('Category saved.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save category.';
    }
  }

  editCategory(id: string): void {
    const category = this.categoryService.categories().find(c => c.id === id);
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
    if (this.productService.products().some(p => p.active && p.category_id === id)) {
      this.feedback = 'A category with active products cannot be deactivated.';
      return;
    }
    if (confirm('Deactivate this category?')) {
      try {
        await this.categoryService.deactivateCategory(id);
        this.notice.show('Category deactivated.');
      } catch (error) {
        this.feedback = error instanceof Error ? error.message : 'Could not deactivate category.';
      }
    }
  }

  filteredProducts() {
    const query = this.catalogSearch.trim().toLowerCase();
    return this.productService.products().filter(product =>
      (!query || `${product.name} ${product.grade ?? ''}`.toLowerCase().includes(query))
      && (!this.catalogCategory || product.category_id === this.catalogCategory)
      && (!this.catalogBrand || product.brand_id === this.catalogBrand)
      && (this.catalogStatus === 'all' || (this.catalogStatus === 'active' ? product.active : !product.active))
      && (!this.lowStockOnly || this.productService.totalStock(product) <= product.low_stock_level)
    );
  }

  trackById(_: number, item: { id: string }): string { return item.id; }
  private newPack(): DraftPack {
    return { label: '', size: 1, unit: this.allowedUnits()[0], mrp: 0, cashPrice: 0, creditPrice: 0, looseAllowed: false };
  }
}
