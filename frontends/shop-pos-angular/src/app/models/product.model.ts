import { RecordOut, TenantIn } from './common.model';
import { Pack } from './pack.model';

export interface ProductCreate extends TenantIn {
  brand_id?: string | null;
  category_id?: string | null;
  name: string;
  grade?: string | null;
  hsn?: string | null;
  gst_rate?: number;
  unit_type: string;
  low_stock_level?: number;
  active?: boolean;
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
  packs?: Pack[];
  stockBase?: Record<string, number>;
}
