import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NoticeService } from '../core/notice.service';
import { ProductService } from '../core/product.service';
import { StockService } from '../core/stock.service';
import { Pack, Product, StockLot } from '../models';

@Component({
  selector: 'app-stock-page',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePipe, DecimalPipe],
  templateUrl: './stock.component.html',
  styleUrls: ['./stock.component.scss'],
})
export class StockPageComponent {
  readonly stockService = inject(StockService);
  readonly productService = inject(ProductService);
  private readonly notice = inject(NoticeService);

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
  feedback = '';

  activeProducts(): Product[] { return this.productService.products().filter(p => p.active); }
  selectedStockProduct(): Product | undefined { return this.productService.product(this.stockProductId); }

  lotsForSelectedPack(): StockLot[] {
    return this.stockService.stockLots().filter(lot => lot.pack_id === this.stockPackId);
  }

  packLabel(pack: Pack): string { return `${pack.size} ${pack.size_unit}`; }

  baseUnitOf(product: Product): string {
    if (product.unit_type === 'Liquid' || product.unit_type === 'L') return 'L';
    if (product.unit_type === 'Item' || product.unit_type === 'piece') return 'piece';
    return 'kg';
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
      const pack = product?.packs?.find(p => p.id === this.stockPackId);
      if (!product || !pack) throw new Error('Choose a product and pack.');

      const quantityBase = this.stockQuantity * pack.size_in_base_unit;
      if (this.stockMode === 'in') {
        await this.stockService.stockIn(
          this.stockPackId, quantityBase, this.stockSupplier, this.stockBatch, this.stockExpiry, this.stockCost
        );
      } else {
        if (!this.stockLotId) throw new Error('Choose a stock lot to adjust.');
        const wouldGoNegative = (product.stockBase?.[pack.id] ?? 0) + quantityBase < 0;
        if (wouldGoNegative && !confirm('This adjustment will create negative stock. Confirm to continue.')) {
          return;
        }
        await this.stockService.adjustStock(this.stockLotId, quantityBase, this.stockReason);
      }
      this.notice.show('Stock movement recorded.');
      this.stockQuantity = 1;
      this.stockReason = '';
      this.stockBatch = '';
      this.stockExpiry = '';
      this.stockSupplier = '';
    } catch (error) {
      this.feedback = error instanceof Error ? error.message : 'Could not record stock movement.';
    }
  }

  trackById(_: number, item: { id: string }): string { return item.id; }
}
