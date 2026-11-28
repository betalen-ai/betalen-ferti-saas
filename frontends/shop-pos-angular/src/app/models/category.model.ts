import { RecordOut, TenantIn } from './common.model';

export interface CategoryCreate extends TenantIn {
  name: string;
  product_type: string;
  active?: boolean;
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
