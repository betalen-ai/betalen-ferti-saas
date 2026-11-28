import { RecordOut, TenantIn, StockEntryType, StockMovementType } from './common.model';

export interface StockLotCreate extends TenantIn {
  pack_id: string;
  supplier?: string | null;
  received_date: string;
  quantity_base: number;
  cost_price: number;
  batch_number?: string | null;
  expiry_date?: string | null;
}
export interface StockLotUpdate extends TenantIn {
  supplier?: string | null;
  cost_price?: number | null;
  batch_number?: string | null;
  expiry_date?: string | null;
}
export interface StockLot extends RecordOut {
  pack_id: string;
  supplier: string | null;
  received_date: string;
  quantity_base: number;
  available_base: number;
  cost_price: number;
  batch_number: string | null;
  expiry_date: string | null;
}
export interface StockMovementCreate extends TenantIn {
  stock_lot_id: string;
  movement_type: StockMovementType;
  quantity_base: number;
  reason: string;
}
export interface StockMovement extends RecordOut {
  pack_id: string;
  stock_lot_id: string | null;
  movement_type: string;
  quantity_base: number;
  reason: string | null;
  source_id: string | null;
  source_type: string | null;
}
export interface StockEntry {
  id: string;
  date: string;
  productId: string;
  productName: string;
  type: StockEntryType;
  quantityBase: number;
  balanceBase: number;
  reason: string;
  batchNo: string;
  expiryDate: string;
  supplier: string;
  costPrice: number;
}
