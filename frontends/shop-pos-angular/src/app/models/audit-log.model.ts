import { RecordOut } from './common.model';

export interface AuditLog extends RecordOut {
  user_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  old_values: Record<string, any> | null;
  new_values: Record<string, any> | null;
}
