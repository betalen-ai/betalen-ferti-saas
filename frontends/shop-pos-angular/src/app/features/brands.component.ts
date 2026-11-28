import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrandService } from '../core/brand.service';
import { NoticeService } from '../core/notice.service';
import { ProductService } from '../core/product.service';
import { Brand } from '../models';

@Component({
  selector: 'app-brands-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './brands.component.html',
  styleUrls: ['./brands.component.scss'],
})
export class BrandsPageComponent implements OnInit {
  readonly brandService = inject(BrandService);
  private readonly productService = inject(ProductService);
  private readonly notice = inject(NoticeService);

  brandName = '';
  brandManufacturer = '';
  brandNotes = '';
  editingBrandId = '';
  feedback = '';
  
  ngOnInit(): void {
    this.brandService.refreshBrands();
  }
  get duplicateBrandName(): boolean {
    const name = this.brandName.trim().toLowerCase();
    if (!name) return false;
    return this.brandService.brands().some(
      b => b.id !== this.editingBrandId && b.name.trim().toLowerCase() === name
    );
  }

  get canSaveBrand(): boolean {
    return !!this.brandName.trim() && !this.duplicateBrandName;
  }

  productCount(brandId: string): number {
    return this.productService.products().filter(p => p.brand_id === brandId).length;
  }

  async saveBrand(): Promise<void> {
    this.feedback = '';
    try {
      if (!this.brandName.trim()) {
        this.feedback = 'Enter a brand name.';
        return;
      }
      if (this.editingBrandId) {
        await this.brandService.updateBrand(this.editingBrandId, this.brandName, this.brandManufacturer, this.brandNotes);
      } else {
        await this.brandService.addBrand(this.brandName, this.brandManufacturer, this.brandNotes);
      }
      this.resetBrandForm();
      this.notice.show('Brand saved.');
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not save brand.';
    }
  }

  editBrand(id: string): void {
    const brand = this.brandService.brands().find(item => item.id === id);
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
        await this.brandService.deactivateBrand(id);
        this.notice.show('Brand deactivated.');
      } catch (error) {
        this.feedback = error instanceof Error ? error.message : 'Could not deactivate brand.';
      }
    }
  }

  trackById(_: number, brand: Brand): string { return brand.id; }
}
