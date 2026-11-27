// ============================================================================
// Enums / Literals
// ============================================================================

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

// ============================================================================
// Base / Common
// ============================================================================

/** Base for every write payload. tenant_id is optional; always checked against caller's tenant. */
export interface TenantIn {
  tenant_id?: string | null;
}

/** Base record output — every persisted entity returns these. */
export interface RecordOut {
  id: string;
  tenant_id: string;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  version: number;
}

// ============================================================================
// Brand
// ============================================================================

export interface BrandCreate extends TenantIn {
  name: string;                 // min 1, max 120
  manufacturer?: string;        // max 180, default ""
  notes?: string;               // default ""
  active?: boolean;             // default true
}

export interface BrandUpdate extends TenantIn {
  name?: string | null;
  manufacturer?: string | null;
  notes?: string | null;
  active?: boolean | null;
}

export interface Brand extends RecordOut {
  name: string;
  manufacturer: string;
  notes: string;
  active: boolean;
}

// ============================================================================
// Category
// ============================================================================

export interface CategoryCreate extends TenantIn {
  name: string;                 // min 1, max 120
  product_type: string;         // min 1, max 16
  active?: boolean;             // default true
}

export interface CategoryUpdate extends TenantIn {
  name?: string | null;
  product_type?: string | null;
  active?: boolean | null;
}

export interface Category extends RecordOut {
  name: string;
  product_type: string;
  active: boolean;
}

// ============================================================================
// Product
// ============================================================================

export interface ProductCreate extends TenantIn {
  brand_id?: string | null;
  category_id?: string | null;
  name: string;                 // min 1, max 180
  grade?: string | null;        // max 80
  hsn?: string | null;          // max 32
  gst_rate?: number;            // 0-100, default 0
  unit_type: string;            // min 1, max 16
  low_stock_level?: number;     // >= 0, default 0
  active?: boolean;             // default true
}

export interface ProductUpdate extends TenantIn {
  brand_id?: string | null;
  category_id?: string | null;
  name?: string | null;
  grade?: string | null;
  hsn?: string | null;
  gst_rate?: number | null;
  unit_type?: string | null;
  low_stock_level?: number | null;
  active?: boolean | null;
}

export interface Product extends RecordOut {
  brand_id: string | null;
  category_id: string | null;
  name: string;
  grade: string | null;
  hsn: string | null;
  gst_rate: number;
  unit_type: string;
  low_stock_level: number;
  active: boolean;
  // Optional client-side enrichment (not from API):
  packs?: Pack[];
  stockBase?: Record<string, number>;
}

// ============================================================================
// Pack
// ============================================================================

export interface PackCreate extends TenantIn {
  product_id: string;
  size: number;                 // > 0
  size_unit: string;            // min 1, max 16
  size_in_base_unit: number;    // > 0
  mrp: number;                  // >= 0
  cash_price: number;           // >= 0
  credit_price: number;         // >= 0
  barcode?: string | null;      // max 80
  allow_loose_sale?: boolean;   // default false
  active?: boolean;             // default true
}

/** product_id / size fields are immutable once stock and bills reference the pack. */
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

// ============================================================================
// Stock
// ============================================================================

export interface StockLotCreate extends TenantIn {
  pack_id: string;
  supplier?: string | null;     // max 180
  received_date: string;        // ISO date
  quantity_base: number;        // > 0
  cost_price: number;           // >= 0
  batch_number?: string | null; // max 80
  expiry_date?: string | null;  // ISO date, must be >= received_date
}

/** available_base is changed only through stock movements. */
export interface StockLotUpdate extends TenantIn {
  supplier?: string | null;
  cost_price?: number | null;
  batch_number?: string | null;
  expiry_date?: string | null;
}

export interface StockLot extends RecordOut {
  pack_id: string;
  supplier: string | null;
  received_date: string;        // ISO date
  quantity_base: number;
  available_base: number;
  cost_price: number;
  batch_number: string | null;
  expiry_date: string | null;
}

export interface StockMovementCreate extends TenantIn {
  stock_lot_id: string;
  movement_type: StockMovementType;
  quantity_base: number;        // signed (+ in, - out), must not be zero
  reason: string;               // min 1, max 500
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

/** UI-friendly stock entry view (maps from StockMovement + lot data). */
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

// ============================================================================
// Farmer
// ============================================================================

export interface FarmerCreate extends TenantIn {
  name: string;                 // min 1, max 180
  mobile: string;               // pattern: ^\+?\d{10,15}$
  address?: string | null;
  village?: string | null;      // max 120
  opening_balance?: number;     // default 0
  active?: boolean;             // default true
}

/** opening_balance is a ledger value and is not editable here. */
export interface FarmerUpdate extends TenantIn {
  name?: string | null;
  mobile?: string | null;
  address?: string | null;
  village?: string | null;
  active?: boolean | null;
}

export interface Farmer extends RecordOut {
  name: string;
  mobile: string;
  address: string | null;
  village: string | null;
  opening_balance: number;
  active: boolean;
  // Optional client-side enrichment (not from API):
  landSize?: number | null;
  notes?: string;
  creditLimit?: number | null;
  lastBillDate?: string | null;
}

// ============================================================================
// Season
// ============================================================================

export interface SeasonCreate extends TenantIn {
  name: string;                         // min 1, max 100
  start_date: string;                   // ISO date
  end_date: string;                     // ISO date, >= start_date
  default_cash_discount?: number;       // 0-100 (pct), default 0
  default_credit_interest_per_month?: number; // pct, default 0
  due_date?: string | null;
  grace_days?: number;                  // >= 0, default 0
  late_interest_per_day?: number;       // >= 0, default 0
}

export interface SeasonUpdate extends TenantIn {
  name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  default_cash_discount?: number | null;
  default_credit_interest_per_month?: number | null;
  due_date?: string | null;
  grace_days?: number | null;
  late_interest_per_day?: number | null;
}

export interface Season extends RecordOut {
  name: string;
  start_date: string;
  end_date: string;
  default_cash_discount: number;
  default_credit_interest_per_month: number;
  due_date: string | null;
  grace_days: number;
  late_interest_per_day: number;
  // Optional client-side enrichment:
  discountType?: DiscountType;
  active?: boolean;
}

// ============================================================================
// Cashbook
// ============================================================================

export interface CashbookCreate extends TenantIn {
  entry_date: string;           // ISO date
  direction: CashbookDirection;
  amount: number;               // > 0
  category: string;             // min 1, max 80
  description?: string | null;
}

export interface CashbookUpdate extends TenantIn {
  entry_date?: string | null;
  direction?: CashbookDirection | null;
  amount?: number | null;
  category?: string | null;
  description?: string | null;
}

export interface Cashbook extends RecordOut {
  entry_date: string;
  direction: CashbookDirection;
  amount: number;
  category: string;
  description: string | null;
}

// ============================================================================
// Settings (one row per tenant)
// ============================================================================

export interface SettingsIn extends TenantIn {
  values: Record<string, any>;
}

export interface Settings {
  tenant_id: string;
  values: Record<string, any>;
  updated_at: string;
}

// ============================================================================
// Read-only ledger outputs
// ============================================================================

export interface Bill extends RecordOut {
  bill_number: string;
  farmer_id: string;
  season_id: string | null;
  bill_date: string;
  due_date: string | null;
  payment_type: string;
  subtotal: number;
  discount: number;
  interest_amount: number;
  gst_amount: number;
  round_off: number;
  total: number;
  paid_now: number;
  balance: number;
  status: string;
  terms: string | null;
  // Optional client-side enrichment:
  farmerName?: string;
  lines?: BillLine[];
  paymentMode?: PaymentMode;
  interestPct?: number;
  months?: number;
  principalBalance?: number;
  interestBalance?: number;
  taxableValue?: number;
  cgst?: number;
  sgst?: number;
  rounding?: number;
}

export interface BillLine extends RecordOut {
  bill_id: string;
  pack_id: string;
  product_name: string;
  pack_name: string;
  quantity: number;
  quantity_base: number;
  unit_price: number;
  line_total: number;
  // Optional client-side enrichment:
  productId?: string;
  gstPercent?: number;
}

export interface Payment extends RecordOut {
  farmer_id: string;
  amount: number;
  mode: string;
  payment_date: string;
  bill_id: string | null;
}

export interface PaymentAllocation {
  billId: string;
  interestPaid: number;
  principalPaid: number;
  amount: number;
}

export interface KhataEntry extends RecordOut {
  farmer_id: string;
  bill_id: string | null;
  payment_id: string | null;
  entry_type: string;
  debit: number;
  credit: number;
  description: string;
  reverses_entry_id: string | null;
  // Optional client-side enrichment:
  date?: string;
  billNumber?: string;
  direction?: KhataDirection;
  amount?: number;
  balanceAfter?: number;
  note?: string;
}

export interface AuditLog extends RecordOut {
  user_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  old_values: Record<string, any> | null;
  new_values: Record<string, any> | null;
}

// ============================================================================
// UI / Form helper types
// ============================================================================

export interface ProductPackInput {
  label: string;
  size: number;
  unit: PackUnit;
  mrp: number;
  cashPrice: number;
  creditPrice: number;
  looseAllowed: boolean;
}