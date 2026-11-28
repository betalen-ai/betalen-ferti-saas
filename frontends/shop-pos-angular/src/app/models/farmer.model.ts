import { RecordOut, TenantIn } from './common.model';

export interface FarmerCreate extends TenantIn {
  name: string;
  mobile: string;
  address?: string | null;
  village?: string | null;
  opening_balance?: number;
  active?: boolean;
}
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
  landSize?: number | null;
  notes?: string;
  creditLimit?: number | null;
  lastBillDate?: string | null;
}
