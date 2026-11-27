export type ProductType = 'Solid' | 'Liquid' | 'Item';
export type PackUnit = 'g' | 'kg' | 'bag' | 'ml' | 'L' | 'piece' | 'set';
export type PaymentType = 'cash' | 'credit' | 'part';
export type PaymentMode = 'cash' | 'UPI' | 'card' | 'credit';
export type StockMovementType = 'adjustment' | 'damage' | 'return' | 'opening';
export type StockEntryType = 'in' | 'sale' | 'adjustment' | 'return';
export type CashbookDirection = 'in' | 'out';
export type BillStatus = 'paid' | 'credit' | 'part-paid' | 'held' | 'void';
export type KhataDirection = 'debit' | 'credit';
export type DiscountType = 'amount' | 'percent';

export interface TenantIn {
  tenant_id?: string | null;
}

export interface RecordOut {
  id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  version: number;
}
