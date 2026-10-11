-- Schema for Weekly Orders Collector
-- Run this script in the Supabase SQL Editor (Dashboard > SQL Editor > New query)

-- 1. Create the orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    whatsapp_enc TEXT NOT NULL,
    ripe_chips INT NOT NULL DEFAULT 0 CHECK (ripe_chips >= 0),
    unripe_chips INT NOT NULL DEFAULT 0 CHECK (unripe_chips >= 0),
    CONSTRAINT at_least_one_item CHECK (ripe_chips + unripe_chips > 0),
    total INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Optional: Index on id and created_at for fast queries
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- 3. Supabase Row Level Security (RLS) Configuration
-- Direct PostgreSQL connections (psycopg2 using postgres credentials) bypass RLS automatically.
-- If accessing via Supabase REST API (PostgREST), these policies ensure security:
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Allow anonymous or authenticated clients to insert new orders
DROP POLICY IF EXISTS "Allow public insert" ON orders;
CREATE POLICY "Allow public insert" ON orders
    FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

-- Allow service_role to have full read/write/delete access (for weekly export and cleanup)
DROP POLICY IF EXISTS "Allow service_role full access" ON orders;
CREATE POLICY "Allow service_role full access" ON orders
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Note: By default, anonymous users cannot SELECT or DELETE orders, protecting customer data!
