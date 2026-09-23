-- Database Seed Script for Customer Support Refund System
-- Initializes schema and seeds 16 realistic customer profiles with diverse order histories

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create tables
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    total_spent DOUBLE PRECISION DEFAULT 0.0,
    orders_count INTEGER DEFAULT 0,
    refunds_count INTEGER DEFAULT 0,
    return_rate DOUBLE PRECISION DEFAULT 0.0,
    risk_score DOUBLE PRECISION DEFAULT 0.0,
    account_created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_number VARCHAR(64) UNIQUE NOT NULL,
    order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    total_amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(32) DEFAULT 'delivered',
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS refund_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    order_id UUID NOT NULL REFERENCES orders(id),
    item_id VARCHAR(64),
    item_name VARCHAR(255),
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    reason_category VARCHAR(64) NOT NULL,
    customer_explanation TEXT NOT NULL,
    decision VARCHAR(32) DEFAULT 'pending',
    decision_reason TEXT,
    confidence_score DOUBLE PRECISION,
    policy_checks JSONB DEFAULT '{}'::jsonb,
    llm_audit_data JSONB DEFAULT '{}'::jsonb,
    human_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    override_by VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refund_request_id UUID REFERENCES refund_requests(id) ON DELETE CASCADE,
    action VARCHAR(64) NOT NULL,
    actor VARCHAR(64) DEFAULT 'system',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_refund_requests_customer_id ON refund_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_refund_requests_order_id ON refund_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_refund_requests_decision ON refund_requests(decision);
CREATE INDEX IF NOT EXISTS idx_audit_logs_refund_id ON audit_logs(refund_request_id);

-- 2. Seed Customer Profiles (16 Profiles)
INSERT INTO customers (id, email, name, total_spent, orders_count, refunds_count, return_rate, risk_score, account_created_at)
VALUES
    ('c1111111-1111-1111-1111-111111111111', 'sarah.jenkins@example.com', 'Sarah Jenkins', 3240.50, 18, 0, 0.00, 0.05, NOW() - INTERVAL '400 days'),
    ('c2222222-2222-2222-2222-222222222222', 'david.miller@example.com', 'David Miller', 450.00, 4, 0, 0.00, 0.10, NOW() - INTERVAL '120 days'),
    ('c3333333-3333-3333-3333-333333333333', 'elena.rostova@example.com', 'Elena Rostova', 890.25, 6, 2, 0.33, 0.38, NOW() - INTERVAL '210 days'),
    ('c4444444-4444-4444-4444-444444444444', 'marcus.vance@example.com', 'Marcus Vance', 1200.00, 5, 3, 0.60, 0.85, NOW() - INTERVAL '90 days'),
    ('c5555555-5555-5555-5555-555555555555', 'victoria.sterling@example.com', 'Victoria Sterling', 12450.00, 32, 1, 0.03, 0.02, NOW() - INTERVAL '700 days'),
    ('c6666666-6666-6666-6666-666666666666', 'alex.rivera@example.com', 'Alex Rivera', 85.00, 1, 0, 0.00, 0.15, NOW() - INTERVAL '15 days'),
    ('c7777777-7777-7777-7777-777777777777', 'kevin.chen@example.com', 'Kevin Chen', 2800.75, 9, 1, 0.11, 0.12, NOW() - INTERVAL '300 days'),
    ('c8888888-8888-8888-8888-888888888888', 'amanda.price@example.com', 'Amanda Price', 320.40, 8, 1, 0.12, 0.15, NOW() - INTERVAL '180 days'),
    ('c9999999-9999-9999-9999-999999999999', 'chloe.dubois@example.com', 'Chloe Dubois', 1650.00, 11, 3, 0.27, 0.35, NOW() - INTERVAL '250 days'),
    ('caaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'robert.taylor@example.com', 'Robert Taylor', 620.00, 3, 0, 0.00, 0.10, NOW() - INTERVAL '450 days'),
    ('cbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'james.wilson@example.com', 'James Wilson', 1850.00, 1, 0, 0.00, 0.20, NOW() - INTERVAL '20 days'),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'maria.santos@example.com', 'Maria Santos', 2100.30, 14, 1, 0.07, 0.08, NOW() - INTERVAL '350 days'),
    ('cddddddd-dddd-dddd-dddd-dddddddddddd', 'tyler.brooks@example.com', 'Tyler Brooks', 940.00, 4, 2, 0.50, 0.72, NOW() - INTERVAL '75 days'),
    ('ceeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'emily.watson@example.com', 'Emily Watson', 1400.00, 7, 0, 0.00, 0.05, NOW() - INTERVAL '190 days'),
    ('cfffffff-ffff-ffff-ffff-ffffffffffff', 'lucas.bennett@example.com', 'Lucas Bennett', 210.00, 3, 0, 0.00, 0.10, NOW() - INTERVAL '60 days'),
    ('c0000000-0000-0000-0000-000000000000', 'samantha.reed@example.com', 'Samantha Reed', 780.00, 2, 1, 0.50, 0.65, NOW() - INTERVAL '40 days')
ON CONFLICT (id) DO NOTHING;

-- 3. Seed Orders for Customers
INSERT INTO orders (id, customer_id, order_number, order_date, total_amount, currency, status, items)
VALUES
    -- Sarah Jenkins (Recent order, within 10 days)
    ('o1111111-1111-1111-1111-111111111101', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-9001', NOW() - INTERVAL '10 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-101", "name": "Wireless Ergonomic Mouse", "price": 45.00, "category": "electronics", "condition": "new"}, {"id": "item-102", "name": "Mechanical Keyboard Wrist Rest", "price": 40.00, "category": "accessories", "condition": "new"}]'::jsonb),
    -- Sarah Jenkins (Older delivered order)
    ('o1111111-1111-1111-1111-111111111102', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-7840', NOW() - INTERVAL '45 days', 210.00, 'USD', 'delivered',
     '[{"id": "item-103", "name": "Active Noise Cancelling Earbuds", "price": 210.00, "category": "electronics", "condition": "new"}]'::jsonb),

    -- David Miller (Recent order within 14 days)
    ('o2222222-2222-2222-2222-222222222201', 'c2222222-2222-2222-2222-222222222222', 'ORD-2026-9055', NOW() - INTERVAL '14 days', 120.00, 'USD', 'delivered',
     '[{"id": "item-201", "name": "Merino Wool Crewneck Sweater", "price": 120.00, "category": "apparel", "condition": "new"}]'::jsonb),

    -- Elena Rostova (Order delivered 22 days ago)
    ('o3333333-3333-3333-3333-333333333301', 'c3333333-3333-3333-3333-333333333333', 'ORD-2026-8812', NOW() - INTERVAL '22 days', 195.00, 'USD', 'delivered',
     '[{"id": "item-301", "name": "Smart Aroma Diffuser", "price": 75.00, "category": "home_goods", "condition": "new"}, {"id": "item-302", "name": "Essential Oils Starter Kit", "price": 120.00, "category": "perishables", "condition": "new"}]'::jsonb),

    -- Marcus Vance (High risk customer, order 8 days ago)
    ('o4444444-4444-4444-4444-444444444401', 'c4444444-4444-4444-4444-444444444444', 'ORD-2026-9120', NOW() - INTERVAL '8 days', 350.00, 'USD', 'delivered',
     '[{"id": "item-401", "name": "Pro Gaming Headset", "price": 350.00, "category": "electronics", "condition": "new"}]'::jsonb),

    -- Victoria Sterling (High-value order $1,400 delivered 5 days ago)
    ('o5555555-5555-5555-5555-555555555501', 'c5555555-5555-5555-5555-555555555555', 'ORD-2026-9201', NOW() - INTERVAL '5 days', 1400.00, 'USD', 'delivered',
     '[{"id": "item-501", "name": "4K Ultra-Wide Curved Monitor 38-inch", "price": 1400.00, "category": "electronics", "condition": "new"}]'::jsonb),

    -- Alex Rivera (Delivered 12 days ago)
    ('o6666666-6666-6666-6666-666666666601', 'c6666666-6666-6666-6666-666666666666', 'ORD-2026-9304', NOW() - INTERVAL '12 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-601", "name": "Canvas Travel Backpack", "price": 85.00, "category": "accessories", "condition": "new"}]'::jsonb),

    -- Kevin Chen (Delivered 40 days ago - past standard 30 day return window)
    ('o7777777-7777-7777-7777-777777777701', 'c7777777-7777-7777-7777-777777777777', 'ORD-2026-7650', NOW() - INTERVAL '40 days', 450.00, 'USD', 'delivered',
     '[{"id": "item-701", "name": "Robot Vacuum Cleaner", "price": 450.00, "category": "home_goods", "condition": "new"}]'::jsonb),

    -- Amanda Price (Contains clearance item)
    ('o8888888-8888-8888-8888-888888888801', 'c8888888-8888-8888-8888-888888888888', 'ORD-2026-9040', NOW() - INTERVAL '16 days', 65.00, 'USD', 'delivered',
     '[{"id": "item-801", "name": "Clearance Winter Parka [Final Sale]", "price": 65.00, "category": "clearance_items", "condition": "new"}]'::jsonb),

    -- James Wilson (Delivered 18 days ago, $650 item exceeding $500 threshold)
    ('obbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'cbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'ORD-2026-8990', NOW() - INTERVAL '18 days', 650.00, 'USD', 'delivered',
     '[{"id": "item-b01", "name": "Espresso Machine with Grinder", "price": 650.00, "category": "home_goods", "condition": "new"}]'::jsonb),

    -- Tyler Brooks (Order 5 days ago, high risk user)
    ('oddddddd-dddd-dddd-dddd-dddddddddd01', 'cddddddd-dddd-dddd-dddd-dddddddddddd', 'ORD-2026-9410', NOW() - INTERVAL '5 days', 280.00, 'USD', 'delivered',
     '[{"id": "item-d01", "name": "Designer Leather Jacket", "price": 280.00, "category": "apparel", "condition": "new"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;
