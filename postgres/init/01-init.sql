CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE SCHEMA IF NOT EXISTS org;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS email;

CREATE TABLE org.tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  subdomain TEXT UNIQUE,
  subscription_plan TEXT DEFAULT 'free',
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE org.roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL);

CREATE TABLE org.permissions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  resource TEXT NOT NULL, action TEXT NOT NULL, UNIQUE(resource, action));

CREATE TABLE org.role_permissions (
  role_id UUID REFERENCES org.roles(id) ON DELETE CASCADE,
  permission_id UUID REFERENCES org.permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id));

CREATE TABLE org.org_users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  email TEXT NOT NULL, password_hash TEXT NOT NULL, full_name TEXT,
  role_id UUID REFERENCES org.roles(id), status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, email));

CREATE TABLE org.subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  plan TEXT NOT NULL, status TEXT NOT NULL,
  valid_from DATE NOT NULL, valid_to DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.warehouses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, location TEXT, created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, batch_no TEXT, expiry_date DATE,
  unit_price NUMERIC(12,2) NOT NULL DEFAULT 0, gst_rate NUMERIC(5,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.stock (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  warehouse_id UUID REFERENCES inventory.warehouses(id),
  product_id UUID REFERENCES inventory.products(id),
  quantity_on_hand NUMERIC(12,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(warehouse_id, product_id));

CREATE TABLE billing.customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, phone TEXT,
  credit_limit NUMERIC(12,2) DEFAULT 0, balance_due NUMERIC(12,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE billing.invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  invoice_number TEXT NOT NULL, customer_id UUID REFERENCES billing.customers(id),
  total_amount NUMERIC(12,2) NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT',
  created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, invoice_number));

CREATE TABLE billing.invoice_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  invoice_id UUID REFERENCES billing.invoices(id) ON DELETE CASCADE,
  product_id UUID NOT NULL, quantity NUMERIC(12,2) NOT NULL,
  unit_price NUMERIC(12,2) NOT NULL);

CREATE TABLE billing.payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  invoice_id UUID REFERENCES billing.invoices(id),
  amount NUMERIC(12,2) NOT NULL, method TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'RECORDED', created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE billing.credit_ledger (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  customer_id UUID REFERENCES billing.customers(id), type TEXT NOT NULL,
  amount NUMERIC(12,2) NOT NULL, running_balance NUMERIC(12,2) NOT NULL,
  reference_id UUID, created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE shared.sync_outbox (
  id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, terminal_id TEXT NOT NULL,
  doc_type TEXT NOT NULL, doc_id UUID NOT NULL, payload JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(doc_type, doc_id));