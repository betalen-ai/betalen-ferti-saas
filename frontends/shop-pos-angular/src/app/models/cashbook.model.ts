import { RecordOut, TenantIn, CashbookDirection } from './common.model';

export interface CashbookCreate extends TenantIn {
  entry_date: string;
  direction: CashbookDirection;
  amount: number;
  category: string;
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
