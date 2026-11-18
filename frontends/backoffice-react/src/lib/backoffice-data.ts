import type { Database } from "@/integrations/supabase/types";

export type Tables = Database["public"]["Tables"];
export type TableName = Exclude<keyof Tables, "profiles" | "user_roles">;
export type Row = { [K in TableName]: Tables[K]["Row"] }[TableName];
export const revenue: Array<{ month: string; revenue: number; credit: number }> = [
  { month: "Jun", revenue: 182000, credit: 42000 },
  { month: "Jul", revenue: 236000, credit: 51000 },
  { month: "Aug", revenue: 211000, credit: 38000 },
  { month: "Sep", revenue: 274000, credit: 61000 },
  { month: "Oct", revenue: 318000, credit: 57000 },
  { month: "Nov", revenue: 296000, credit: 49000 },
];
