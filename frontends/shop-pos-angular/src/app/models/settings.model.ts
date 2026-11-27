import { TenantIn } from './common.model';

export interface SettingsIn extends TenantIn {
  values: Record<string, any>;
}
export interface Settings {
  tenant_id: string;
  values: Record<string, any>;
  updated_at: string;
}
