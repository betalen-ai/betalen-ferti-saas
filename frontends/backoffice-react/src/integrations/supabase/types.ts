export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.18"
  }
  public: {
    Tables: {
      backoffice_roles: {
        Row: {
          created_at: string
          description: string
          id: string
          name: string
          permissions: Json
        }
        Insert: {
          created_at?: string
          description?: string
          id?: string
          name: string
          permissions?: Json
        }
        Update: {
          created_at?: string
          description?: string
          id?: string
          name?: string
          permissions?: Json
        }
        Relationships: []
      }
      content_items: {
        Row: {
          body: string
          created_at: string
          id: string
          slug: string
          status: string
          title: string
          type: string
          updated: string
        }
        Insert: {
          body?: string
          created_at?: string
          id?: string
          slug: string
          status?: string
          title: string
          type?: string
          updated?: string
        }
        Update: {
          body?: string
          created_at?: string
          id?: string
          slug?: string
          status?: string
          title?: string
          type?: string
          updated?: string
        }
        Relationships: []
      }
      credit_ledger: {
        Row: {
          balance: number
          created_at: string
          credit_limit: number
          farmer: string
          id: string
          status: string
          tenant_id: string | null
          tenant_name: string
        }
        Insert: {
          balance?: number
          created_at?: string
          credit_limit?: number
          farmer: string
          id?: string
          status?: string
          tenant_id?: string | null
          tenant_name?: string
        }
        Update: {
          balance?: number
          created_at?: string
          credit_limit?: number
          farmer?: string
          id?: string
          status?: string
          tenant_id?: string | null
          tenant_name?: string
        }
        Relationships: [
          {
            foreignKeyName: "credit_ledger_tenant_id_fkey"
            columns: ["tenant_id"]
            isOneToOne: false
            referencedRelation: "tenants"
            referencedColumns: ["id"]
          },
        ]
      }
      invoices: {
        Row: {
          amount: number
          created_at: string
          customer: string
          date: string
          id: string
          invoice_number: string
          status: string
          tenant_id: string | null
          tenant_name: string
          type: string
        }
        Insert: {
          amount?: number
          created_at?: string
          customer: string
          date?: string
          id?: string
          invoice_number: string
          status?: string
          tenant_id?: string | null
          tenant_name?: string
          type?: string
        }
        Update: {
          amount?: number
          created_at?: string
          customer?: string
          date?: string
          id?: string
          invoice_number?: string
          status?: string
          tenant_id?: string | null
          tenant_name?: string
          type?: string
        }
        Relationships: [
          {
            foreignKeyName: "invoices_tenant_id_fkey"
            columns: ["tenant_id"]
            isOneToOne: false
            referencedRelation: "tenants"
            referencedColumns: ["id"]
          },
        ]
      }
      org_users: {
        Row: {
          auth_user_id: string | null
          created_at: string
          email: string
          full_name: string | null
          id: string
          role_id: string | null
          status: string
          tenant_id: string
        }
        Insert: {
          auth_user_id?: string | null
          created_at?: string
          email: string
          full_name?: string | null
          id?: string
          role_id?: string | null
          status?: string
          tenant_id: string
        }
        Update: {
          auth_user_id?: string | null
          created_at?: string
          email?: string
          full_name?: string | null
          id?: string
          role_id?: string | null
          status?: string
          tenant_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "org_users_role_id_fkey"
            columns: ["role_id"]
            isOneToOne: false
            referencedRelation: "backoffice_roles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "org_users_tenant_id_fkey"
            columns: ["tenant_id"]
            isOneToOne: false
            referencedRelation: "tenants"
            referencedColumns: ["id"]
          },
        ]
      }
      payments: {
        Row: {
          amount: number
          created_at: string
          date: string
          id: string
          invoice_id: string | null
          invoice_number: string
          method: string
          status: string
        }
        Insert: {
          amount?: number
          created_at?: string
          date?: string
          id?: string
          invoice_id?: string | null
          invoice_number?: string
          method?: string
          status?: string
        }
        Update: {
          amount?: number
          created_at?: string
          date?: string
          id?: string
          invoice_id?: string | null
          invoice_number?: string
          method?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "payments_invoice_id_fkey"
            columns: ["invoice_id"]
            isOneToOne: false
            referencedRelation: "invoices"
            referencedColumns: ["id"]
          },
        ]
      }
      platform_settings: {
        Row: {
          id: string
          setting_key: string
          setting_value: Json
          updated_at: string
        }
        Insert: {
          id?: string
          setting_key: string
          setting_value?: Json
          updated_at?: string
        }
        Update: {
          id?: string
          setting_key?: string
          setting_value?: Json
          updated_at?: string
        }
        Relationships: []
      }
      products: {
        Row: {
          category: string
          created_at: string
          gst: string
          id: string
          name: string
          price: number
          status: string
          updated_at: string
        }
        Insert: {
          category?: string
          created_at?: string
          gst?: string
          id?: string
          name: string
          price?: number
          status?: string
          updated_at?: string
        }
        Update: {
          category?: string
          created_at?: string
          gst?: string
          id?: string
          name?: string
          price?: number
          status?: string
          updated_at?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          created_at: string
          display_name: string | null
          email: string | null
          id: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          display_name?: string | null
          email?: string | null
          id: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          display_name?: string | null
          email?: string | null
          id?: string
          updated_at?: string
        }
        Relationships: []
      }
      stock_batches: {
        Row: {
          batch: string
          created_at: string
          expiry: string | null
          id: string
          product_id: string | null
          product_name: string
          quantity: number
          warehouse_id: string | null
          warehouse_name: string
        }
        Insert: {
          batch: string
          created_at?: string
          expiry?: string | null
          id?: string
          product_id?: string | null
          product_name: string
          quantity?: number
          warehouse_id?: string | null
          warehouse_name: string
        }
        Update: {
          batch?: string
          created_at?: string
          expiry?: string | null
          id?: string
          product_id?: string | null
          product_name?: string
          quantity?: number
          warehouse_id?: string | null
          warehouse_name?: string
        }
        Relationships: [
          {
            foreignKeyName: "stock_batches_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "stock_batches_warehouse_id_fkey"
            columns: ["warehouse_id"]
            isOneToOne: false
            referencedRelation: "warehouses"
            referencedColumns: ["id"]
          },
        ]
      }
      subscriptions: {
        Row: {
          created_at: string
          id: string
          plan: string
          status: string
          tenant_id: string
          tenant_name: string
          valid_from: string
          valid_to: string
        }
        Insert: {
          created_at?: string
          id?: string
          plan?: string
          status?: string
          tenant_id: string
          tenant_name?: string
          valid_from?: string
          valid_to?: string
        }
        Update: {
          created_at?: string
          id?: string
          plan?: string
          status?: string
          tenant_id?: string
          tenant_name?: string
          valid_from?: string
          valid_to?: string
        }
        Relationships: [
          {
            foreignKeyName: "subscriptions_tenant_id_fkey"
            columns: ["tenant_id"]
            isOneToOne: false
            referencedRelation: "tenants"
            referencedColumns: ["id"]
          },
        ]
      }
      tenants: {
        Row: {
          created_at: string
          id: string
          name: string
          status: string
          subdomain: string | null
          subscription_plan: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          name: string
          status?: string
          subdomain?: string | null
          subscription_plan?: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string
          status?: string
          subdomain?: string | null
          subscription_plan?: string
          updated_at?: string
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          created_at: string
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
      warehouses: {
        Row: {
          capacity: number
          created_at: string
          id: string
          location: string
          name: string
          status: string
        }
        Insert: {
          capacity?: number
          created_at?: string
          id?: string
          location?: string
          name: string
          status?: string
        }
        Update: {
          capacity?: number
          created_at?: string
          id?: string
          location?: string
          name?: string
          status?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "platform_admin" | "shop_owner" | "manager" | "cashier"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["platform_admin", "shop_owner", "manager", "cashier"],
    },
  },
} as const
