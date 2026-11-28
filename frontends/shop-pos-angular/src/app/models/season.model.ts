import { RecordOut, TenantIn, DiscountType } from './common.model';

export interface SeasonCreate extends TenantIn {
  name: string;
  start_date: string;
  end_date: string;
  default_cash_discount?: number;
  default_credit_interest_per_month?: number;
  due_date?: string | null;
  grace_days?: number;
  late_interest_per_day?: number;
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
  discountType?: DiscountType;
  active?: boolean;
}
