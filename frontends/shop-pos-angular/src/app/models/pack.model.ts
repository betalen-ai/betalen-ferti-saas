import { RecordOut, TenantIn } from './common.model';

export interface PackCreate extends TenantIn {
  product_id: string;
  size: number;
  size_unit: string;
  size_in_base_unit: number;
  mrp: number;
  cash_price: number;
  credit_price: number;
  barcode?: string | null;
  allow_loose_sale?: boolean;
  active?: boolean;
}
export interface PackUpdate extends TenantIn {
  mrp?: number | null;
  cash_price?: number | null;
  credit_price?: number | null;
  barcode?: string | null;
  allow_loose_sale?: boolean | null;
  active?: boolean | null;
}
export interface Pack extends RecordOut {
  product_id: string;
  size: number;
  size_unit: string;
  size_in_base_unit: number;
  mrp: number;
  cash_price: number;
  credit_price: number;
  barcode: string | null;
  allow_loose_sale: boolean;
  active: boolean;
}
export interface ProductPackInput {
  label: string;
  size: number;
  unit: import('./common.model').PackUnit;
  mrp: number;
  cashPrice: number;
  creditPrice: number;
  looseAllowed: boolean;
}
