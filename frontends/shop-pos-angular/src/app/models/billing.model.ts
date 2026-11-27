import { RecordOut, BillStatus, PaymentMode, PaymentType, TenantIn } from './common.model';

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
export type { BillStatus, PaymentType };
