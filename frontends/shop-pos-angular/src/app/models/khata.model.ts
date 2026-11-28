import { RecordOut, KhataDirection } from './common.model';

export interface KhataEntry extends RecordOut {
  farmer_id: string;
  bill_id: string | null;
  payment_id: string | null;
  entry_type: string;
  debit: number;
  credit: number;
  description: string;
  reverses_entry_id: string | null;
  date?: string;
  billNumber?: string;
  direction?: KhataDirection;
  amount?: number;
  balanceAfter?: number;
  note?: string;
}
