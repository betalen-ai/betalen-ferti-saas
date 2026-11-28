import { RecordOut, TenantIn } from './common.model';

export interface BrandCreate extends TenantIn {
  name: string;
  manufacturer?: string;
  notes?: string;
  active?: boolean;
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
