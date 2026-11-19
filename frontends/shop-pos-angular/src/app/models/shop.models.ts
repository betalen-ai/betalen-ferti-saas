export type ProductType = 'Solid' | 'Liquid' | 'Item';
export type PackUnit = 'g' | 'kg' | 'bag' | 'ml' | 'L' | 'piece' | 'set';
export type PaymentType = 'cash' | 'credit' | 'part';

export interface Brand {
  id: string;
  name: string;
  manufacturer: string;
  notes: string;
  active: boolean;
}

export interface Category {
  id: string;
  name: string;
  type: ProductType;
  gstPercent: number;
  active: boolean;
}

export interface Pack {
  id: string;
  label: string;
  size: number;
  unit: PackUnit;
  sizeInBaseUnit: number;
  mrp: number;
  cashPrice: number;
  creditPrice: number;
  barcode: string;
  looseAllowed: boolean;
}

export interface Product {
  id: string;
  name: string;
  brandId: string;
  categoryId: string;
  type: ProductType;
  grade: string;
  hsn: string;
  gstPercent: number;
  baseUnit: 'kg' | 'L' | 'piece';
  lowStockLevel: number;
  active: boolean;
  packs: Pack[];
  stockBase: Record<string, number>;
}

export interface Farmer {
  id: string;
  name: string;
  mobile: string;
  village: string;
  address: string;
  landSize: number | null;
  notes: string;
  openingBalance: number;
  creditLimit: number | null;
  lastBillDate: string | null;
}

export interface Season {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  cashDiscount: number;
  discountType: 'amount' | 'percent';
  creditInterestPct: number;
  dueDate: string;
  graceDays: number;
  lateInterestPct: number;
  active: boolean;
}

export interface BillLine {
  productId: string;
  packId: string;
  productName: string;
  packLabel: string;
  quantity: number;
  unitPrice: number;
  gstPercent: number;
  lineTotal: number;
  quantityBase: number;
}

export interface Bill {
  id: string;
  number: string;
  date: string;
  farmerId: string | null;
  farmerName: string;
  seasonId: string | null;
  paymentType: PaymentType;
  paymentMode: 'cash' | 'UPI' | 'card' | 'credit';
  lines: BillLine[];
  subtotal: number;
  discount: number;
  interestPct: number;
  months: number;
  interestAmount: number;
  total: number;
  paidNow: number;
  balance: number;
  principalBalance: number;
  interestBalance: number;
  taxableValue: number;
  cgst: number;
  sgst: number;
  rounding: number;
  dueDate: string | null;
  status: 'paid' | 'credit' | 'part-paid' | 'held' | 'void';
}

export interface StockEntry {
  id: string;
  date: string;
  productId: string;
  productName: string;
  type: 'in' | 'sale' | 'adjustment' | 'return';
  quantityBase: number;
  balanceBase: number;
  reason: string;
  batchNo: string;
  expiryDate: string;
  supplier: string;
  costPrice: number;
}

export interface KhataEntry {
  id: string;
  farmerId: string;
  date: string;
  description: string;
  billNumber: string;
  direction: 'debit' | 'credit';
  amount: number;
  balanceAfter: number;
  note: string;
}

export interface PaymentAllocation {
  billId: string;
  interestPaid: number;
  principalPaid: number;
  amount: number;
}

export interface ProductPackInput {
  label: string;
  size: number;
  unit: PackUnit;
  mrp: number;
  cashPrice: number;
  creditPrice: number;
  looseAllowed: boolean;
}
