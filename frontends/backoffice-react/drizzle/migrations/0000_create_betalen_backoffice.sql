CREATE TYPE public.app_role AS ENUM ('platform_admin', 'shop_owner', 'manager', 'cashier');

CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  email TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated;
GRANT ALL ON public.profiles TO service_role;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role public.app_role NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);
GRANT SELECT ON public.user_roles TO authenticated;
GRANT ALL ON public.user_roles TO service_role;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public
AS $$ SELECT EXISTS (SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role) $$;
GRANT EXECUTE ON FUNCTION public.has_role(UUID, public.app_role) TO authenticated;
GRANT EXECUTE ON FUNCTION public.has_role(UUID, public.app_role) TO service_role;

CREATE POLICY "Users view own profile or admins view all" ON public.profiles FOR SELECT TO authenticated
USING (id = auth.uid() OR public.has_role(auth.uid(), 'platform_admin'));
CREATE POLICY "Users create own profile" ON public.profiles FOR INSERT TO authenticated
WITH CHECK (id = auth.uid());
CREATE POLICY "Users update own profile or admins update all" ON public.profiles FOR UPDATE TO authenticated
USING (id = auth.uid() OR public.has_role(auth.uid(), 'platform_admin'))
WITH CHECK (id = auth.uid() OR public.has_role(auth.uid(), 'platform_admin'));
CREATE POLICY "Users read own role or admins read all" ON public.user_roles FOR SELECT TO authenticated
USING (user_id = auth.uid() OR public.has_role(auth.uid(), 'platform_admin'));
CREATE POLICY "Admins manage roles" ON public.user_roles FOR ALL TO authenticated
USING (public.has_role(auth.uid(), 'platform_admin'))
WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE OR REPLACE FUNCTION public.handle_backoffice_user_created()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name)
  VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'))
  ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
  IF NOT EXISTS (SELECT 1 FROM public.user_roles WHERE role = 'platform_admin') THEN
    INSERT INTO public.user_roles (user_id, role) VALUES (NEW.id, 'platform_admin') ON CONFLICT DO NOTHING;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER on_backoffice_auth_user_created AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_backoffice_user_created();

CREATE TABLE public.tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  subdomain TEXT UNIQUE,
  subscription_plan TEXT NOT NULL DEFAULT 'free',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.tenants TO authenticated;
GRANT ALL ON public.tenants TO service_role;
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage tenants" ON public.tenants FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.backoffice_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.backoffice_roles TO authenticated;
GRANT ALL ON public.backoffice_roles TO service_role;
ALTER TABLE public.backoffice_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage role catalog" ON public.backoffice_roles FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.org_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  auth_user_id UUID,
  email TEXT NOT NULL,
  full_name TEXT,
  role_id UUID REFERENCES public.backoffice_roles(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, email)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.org_users TO authenticated;
GRANT ALL ON public.org_users TO service_role;
ALTER TABLE public.org_users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage organization users" ON public.org_users FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  plan TEXT NOT NULL DEFAULT 'free',
  status TEXT NOT NULL DEFAULT 'active',
  valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
  valid_to DATE NOT NULL DEFAULT (CURRENT_DATE + INTERVAL '1 year'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.subscriptions TO authenticated;
GRANT ALL ON public.subscriptions TO service_role;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage subscriptions" ON public.subscriptions FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '',
  price NUMERIC(12,2) NOT NULL DEFAULT 0,
  gst TEXT NOT NULL DEFAULT '5%',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.products TO authenticated;
GRANT ALL ON public.products TO service_role;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage products" ON public.products FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.warehouses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  location TEXT NOT NULL DEFAULT '',
  capacity INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.warehouses TO authenticated;
GRANT ALL ON public.warehouses TO service_role;
ALTER TABLE public.warehouses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage warehouses" ON public.warehouses FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.stock_batches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
  product_name TEXT NOT NULL,
  warehouse_id UUID REFERENCES public.warehouses(id) ON DELETE SET NULL,
  warehouse_name TEXT NOT NULL,
  batch TEXT NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  expiry DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.stock_batches TO authenticated;
GRANT ALL ON public.stock_batches TO service_role;
ALTER TABLE public.stock_batches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage stock batches" ON public.stock_batches FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_number TEXT NOT NULL UNIQUE,
  customer TEXT NOT NULL,
  tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
  tenant_name TEXT NOT NULL DEFAULT '',
  amount NUMERIC(12,2) NOT NULL DEFAULT 0,
  type TEXT NOT NULL DEFAULT 'GST',
  status TEXT NOT NULL DEFAULT 'paid',
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.invoices TO authenticated;
GRANT ALL ON public.invoices TO service_role;
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage invoices" ON public.invoices FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id UUID REFERENCES public.invoices(id) ON DELETE SET NULL,
  invoice_number TEXT NOT NULL DEFAULT '',
  method TEXT NOT NULL DEFAULT 'Cash',
  amount NUMERIC(12,2) NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'settled',
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.payments TO authenticated;
GRANT ALL ON public.payments TO service_role;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage payments" ON public.payments FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.credit_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer TEXT NOT NULL,
  tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
  tenant_name TEXT NOT NULL DEFAULT '',
  credit_limit NUMERIC(12,2) NOT NULL DEFAULT 0,
  balance NUMERIC(12,2) NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'within limit',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.credit_ledger TO authenticated;
GRANT ALL ON public.credit_ledger TO service_role;
ALTER TABLE public.credit_ledger ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage credit ledger" ON public.credit_ledger FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.content_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL DEFAULT 'Page',
  body TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'draft',
  updated DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.content_items TO authenticated;
GRANT ALL ON public.content_items TO service_role;
ALTER TABLE public.content_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage content" ON public.content_items FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));

CREATE TABLE public.platform_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  setting_key TEXT NOT NULL UNIQUE,
  setting_value JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.platform_settings TO authenticated;
GRANT ALL ON public.platform_settings TO service_role;
ALTER TABLE public.platform_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admins manage platform settings" ON public.platform_settings FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'platform_admin')) WITH CHECK (public.has_role(auth.uid(), 'platform_admin'));
