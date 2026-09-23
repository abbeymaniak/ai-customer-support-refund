-- Database Seed Script for Customer Support Refund System
-- Initializes normalized relational schema and seeds realistic profiles, orders, items, and audit trails

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Normalized Tables

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    total_spent DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    orders_count INTEGER NOT NULL DEFAULT 0,
    refunds_count INTEGER NOT NULL DEFAULT 0,
    return_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    account_created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_number VARCHAR(64) UNIQUE NOT NULL,
    order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITHOUT TIME ZONE,
    total_amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(32) NOT NULL DEFAULT 'delivered',
    items JSONB DEFAULT '[]'::jsonb,
    shipping_address JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id VARCHAR(64) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    is_final_sale BOOLEAN NOT NULL DEFAULT FALSE,
    serial_number VARCHAR(128),
    warranty_status VARCHAR(64),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS refund_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_number VARCHAR(64) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    item_id VARCHAR(64),
    item_name VARCHAR(255),
    amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    total_refund_amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    reason_category VARCHAR(64) NOT NULL,
    customer_explanation TEXT NOT NULL,
    decision VARCHAR(32) NOT NULL DEFAULT 'pending',
    decision_reason TEXT,
    confidence_score DOUBLE PRECISION,
    policy_checks JSONB DEFAULT '{}'::jsonb,
    llm_audit_data JSONB DEFAULT '{}'::jsonb,
    ai_decision VARCHAR(32),
    ai_confidence DOUBLE PRECISION,
    ai_reasoning TEXT,
    policy_evaluations JSONB DEFAULT '{}'::jsonb,
    llm_metadata JSONB DEFAULT '{}'::jsonb,
    human_override BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason TEXT,
    override_by VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS refund_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refund_request_id UUID NOT NULL REFERENCES refund_requests(id) ON DELETE CASCADE,
    order_item_id UUID NOT NULL REFERENCES order_items(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1,
    refund_amount DOUBLE PRECISION NOT NULL,
    item_condition VARCHAR(64) NOT NULL DEFAULT 'unopened',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refund_request_id UUID REFERENCES refund_requests(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL DEFAULT 'system',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Performance and Integrity Indices
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_delivery_date ON orders(delivery_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_category ON order_items(category);
CREATE INDEX IF NOT EXISTS idx_order_items_is_final_sale ON order_items(is_final_sale);
CREATE INDEX IF NOT EXISTS idx_refund_requests_request_number ON refund_requests(request_number);
CREATE INDEX IF NOT EXISTS idx_refund_requests_customer_id ON refund_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_refund_requests_order_id ON refund_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_refund_requests_status ON refund_requests(status);
CREATE INDEX IF NOT EXISTS idx_refund_requests_created_at ON refund_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_refund_items_refund_request ON refund_items(refund_request_id);
CREATE INDEX IF NOT EXISTS idx_refund_items_order_item ON refund_items(order_item_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_refund_request ON audit_logs(refund_request_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Partial index preventing concurrent active refunds on the same order item
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_refund_item ON refund_items (order_item_id);

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

-- 3. Seed Orders with Delivery Dates (using valid 0... hex UUIDs)
INSERT INTO orders (id, customer_id, order_number, order_date, delivery_date, total_amount, currency, status, items, shipping_address)
VALUES
    ('01111111-1111-1111-1111-111111111101', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-9001', NOW() - INTERVAL '12 days', NOW() - INTERVAL '10 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-101", "name": "Wireless Ergonomic Mouse", "price": 45.00, "category": "electronics"}, {"id": "item-102", "name": "Mechanical Keyboard Wrist Rest", "price": 40.00, "category": "accessories"}]'::jsonb, '{"city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb),
    
    ('01111111-1111-1111-1111-111111111102', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-7840', NOW() - INTERVAL '48 days', NOW() - INTERVAL '45 days', 210.00, 'USD', 'delivered',
     '[{"id": "item-103", "name": "Active Noise Cancelling Earbuds", "price": 210.00, "category": "electronics"}]'::jsonb, '{"city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb),

    ('02222222-2222-2222-2222-222222222201', 'c2222222-2222-2222-2222-222222222222', 'ORD-2026-9055', NOW() - INTERVAL '17 days', NOW() - INTERVAL '14 days', 120.00, 'USD', 'delivered',
     '[{"id": "item-201", "name": "Merino Wool Crewneck Sweater", "price": 120.00, "category": "apparel"}]'::jsonb, '{"city": "Austin", "state": "TX", "zip": "73301"}'::jsonb),

    ('03333333-3333-3333-3333-333333333301', 'c3333333-3333-3333-3333-333333333333', 'ORD-2026-8812', NOW() - INTERVAL '25 days', NOW() - INTERVAL '22 days', 195.00, 'USD', 'delivered',
     '[{"id": "item-301", "name": "Smart Aroma Diffuser", "price": 75.00, "category": "home_goods"}, {"id": "item-302", "name": "Essential Oils Starter Kit", "price": 120.00, "category": "perishables"}]'::jsonb, '{"city": "Denver", "state": "CO", "zip": "80201"}'::jsonb),

    ('04444444-4444-4444-4444-444444444401', 'c4444444-4444-4444-4444-444444444444', 'ORD-2026-9120', NOW() - INTERVAL '10 days', NOW() - INTERVAL '8 days', 350.00, 'USD', 'delivered',
     '[{"id": "item-401", "name": "Pro Gaming Headset", "price": 350.00, "category": "electronics"}]'::jsonb, '{"city": "Chicago", "state": "IL", "zip": "60601"}'::jsonb),

    ('05555555-5555-5555-5555-555555555501', 'c5555555-5555-5555-5555-555555555555', 'ORD-2026-9201', NOW() - INTERVAL '7 days', NOW() - INTERVAL '5 days', 1400.00, 'USD', 'delivered',
     '[{"id": "item-501", "name": "4K Ultra-Wide Curved Monitor 38-inch", "price": 1400.00, "category": "electronics"}]'::jsonb, '{"city": "New York", "state": "NY", "zip": "10001"}'::jsonb),

    ('06666666-6666-6666-6666-666666666601', 'c6666666-6666-6666-6666-666666666666', 'ORD-2026-9304', NOW() - INTERVAL '15 days', NOW() - INTERVAL '12 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-601", "name": "Canvas Travel Backpack", "price": 85.00, "category": "accessories"}]'::jsonb, '{"city": "San Francisco", "state": "CA", "zip": "94105"}'::jsonb),

    ('07777777-7777-7777-7777-777777777701', 'c7777777-7777-7777-7777-777777777777', 'ORD-2026-7650', NOW() - INTERVAL '43 days', NOW() - INTERVAL '40 days', 450.00, 'USD', 'delivered',
     '[{"id": "item-701", "name": "Robot Vacuum Cleaner", "price": 450.00, "category": "home_goods"}]'::jsonb, '{"city": "Boston", "state": "MA", "zip": "02108"}'::jsonb),

    ('08888888-8888-8888-8888-888888888801', 'c8888888-8888-8888-8888-888888888888', 'ORD-2026-9040', NOW() - INTERVAL '19 days', NOW() - INTERVAL '16 days', 65.00, 'USD', 'delivered',
     '[{"id": "item-801", "name": "Clearance Winter Parka [Final Sale]", "price": 65.00, "category": "clearance_items"}]'::jsonb, '{"city": "Portland", "state": "OR", "zip": "97201"}'::jsonb),

    ('0bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'cbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'ORD-2026-8990', NOW() - INTERVAL '21 days', NOW() - INTERVAL '18 days', 650.00, 'USD', 'delivered',
     '[{"id": "item-b01", "name": "Espresso Machine with Grinder", "price": 650.00, "category": "home_goods"}]'::jsonb, '{"city": "Miami", "state": "FL", "zip": "33101"}'::jsonb),

    ('0ddddddd-dddd-dddd-dddd-dddddddddd01', 'cddddddd-dddd-dddd-dddd-dddddddddddd', 'ORD-2026-9410', NOW() - INTERVAL '7 days', NOW() - INTERVAL '5 days', 280.00, 'USD', 'delivered',
     '[{"id": "item-d01", "name": "Designer Leather Jacket", "price": 280.00, "category": "apparel"}]'::jsonb, '{"city": "Atlanta", "state": "GA", "zip": "30301"}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 4. Seed Dedicated Order Line Items (using valid 1... hex UUIDs)
INSERT INTO order_items (id, order_id, product_id, product_name, category, price, quantity, is_final_sale, serial_number, warranty_status)
VALUES
    ('11111111-1111-1111-1111-111111111101', '01111111-1111-1111-1111-111111111101', 'PROD-MOUSE-01', 'Wireless Ergonomic Mouse', 'electronics', 45.00, 1, FALSE, 'SN-MOU-9821', 'standard_1yr'),
    ('11111111-1111-1111-1111-111111111102', '01111111-1111-1111-1111-111111111101', 'PROD-REST-02', 'Mechanical Keyboard Wrist Rest', 'accessories', 40.00, 1, FALSE, NULL, NULL),
    ('11111111-1111-1111-1111-111111111103', '01111111-1111-1111-1111-111111111102', 'PROD-BUDS-03', 'Active Noise Cancelling Earbuds', 'electronics', 210.00, 1, FALSE, 'SN-BUD-4512', 'standard_1yr'),
    ('12222222-2222-2222-2222-222222222201', '02222222-2222-2222-2222-222222222201', 'PROD-SWEATER-01', 'Merino Wool Crewneck Sweater', 'apparel', 120.00, 1, FALSE, NULL, NULL),
    ('13333333-3333-3333-3333-333333333301', '03333333-3333-3333-3333-333333333301', 'PROD-DIFF-01', 'Smart Aroma Diffuser', 'home_goods', 75.00, 1, FALSE, 'SN-DIF-2201', 'standard_1yr'),
    ('13333333-3333-3333-3333-333333333302', '03333333-3333-3333-3333-333333333301', 'PROD-OILS-02', 'Essential Oils Starter Kit', 'perishables', 120.00, 1, FALSE, NULL, NULL),
    ('14444444-4444-4444-4444-444444444401', '04444444-4444-4444-4444-444444444401', 'PROD-HEADSET-01', 'Pro Gaming Headset', 'electronics', 350.00, 1, FALSE, 'SN-GAM-9944', 'extended_2yr'),
    ('15555555-5555-5555-5555-555555555501', '05555555-5555-5555-5555-555555555501', 'PROD-MON-01', '4K Ultra-Wide Curved Monitor 38-inch', 'electronics', 1400.00, 1, FALSE, 'SN-MON-7718', 'extended_3yr'),
    ('16666666-6666-6666-6666-666666666601', '06666666-6666-6666-6666-666666666601', 'PROD-BAG-01', 'Canvas Travel Backpack', 'accessories', 85.00, 1, FALSE, NULL, NULL),
    ('17777777-7777-7777-7777-777777777701', '07777777-7777-7777-7777-777777777701', 'PROD-VAC-01', 'Robot Vacuum Cleaner', 'home_goods', 450.00, 1, FALSE, 'SN-VAC-3310', 'standard_1yr'),
    ('18888888-8888-8888-8888-888888888801', '08888888-8888-8888-8888-888888888801', 'PROD-PARKA-01', 'Clearance Winter Parka [Final Sale]', 'clearance_items', 65.00, 1, TRUE, NULL, NULL),
    ('1bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '0bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'PROD-ESPRESSO-01', 'Espresso Machine with Grinder', 'home_goods', 650.00, 1, FALSE, 'SN-ESP-5521', 'standard_1yr'),
    ('1ddddddd-dddd-dddd-dddd-dddddddddd01', '0ddddddd-dddd-dddd-dddd-dddddddddd01', 'PROD-JACKET-01', 'Designer Leather Jacket', 'apparel', 280.00, 1, FALSE, NULL, NULL)
ON CONFLICT (id) DO NOTHING;

-- 5. Seed Initial Refund Requests and Matching Line Items (using valid 2... and 3... hex UUIDs)
INSERT INTO refund_requests (id, request_number, customer_id, order_id, item_id, item_name, amount, total_refund_amount, currency, status, reason_category, customer_explanation, decision, decision_reason, confidence_score, policy_checks, ai_decision, ai_confidence, ai_reasoning, created_at)
VALUES
    ('21111111-1111-1111-1111-111111111101', 'REF-2026-0001', 'c1111111-1111-1111-1111-111111111111', '01111111-1111-1111-1111-111111111101', 'PROD-MOUSE-01', 'Wireless Ergonomic Mouse', 45.00, 45.00, 'USD', 'approved', 'defective', 'The scroll wheel became unresponsive after three days of normal use.', 'approved', 'Purchased within 30 days, verified customer with 0.05 risk score, eligible category.', 0.95, '{"within_return_window": true, "eligible_category": true, "acceptable_risk_score": true}'::jsonb, 'Approved', 0.95, 'Approved: Customer is low risk and order is well within the 30-day window.', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO refund_items (id, refund_request_id, order_item_id, quantity, refund_amount, item_condition)
VALUES
    ('31111111-1111-1111-1111-111111111101', '21111111-1111-1111-1111-111111111101', '11111111-1111-1111-1111-111111111101', 1, 45.00, 'opened')
ON CONFLICT (id) DO NOTHING;

-- 6. Seed Audit Logs (using valid a... hex UUIDs)
INSERT INTO audit_logs (id, refund_request_id, action, actor, details, timestamp)
VALUES
    ('a1111111-1111-1111-1111-111111111101', '21111111-1111-1111-1111-111111111101', 'request_submitted', 'customer', '{"amount": 45.00, "item": "Wireless Ergonomic Mouse", "order": "ORD-2026-9001"}'::jsonb, NOW() - INTERVAL '2 days'),
    ('a1111111-1111-1111-1111-111111111102', '21111111-1111-1111-1111-111111111101', 'ai_evaluated', 'ai_engine', '{"decision": "Approved", "confidence": 0.95, "model": "gpt-4o-mini", "prompt_tokens": 420, "completion_tokens": 85}'::jsonb, NOW() - INTERVAL '2 days' + INTERVAL '3 seconds'),
    ('a1111111-1111-1111-1111-111111111103', '21111111-1111-1111-1111-111111111101', 'status_updated', 'system', '{"from": "pending", "to": "approved"}'::jsonb, NOW() - INTERVAL '2 days' + INTERVAL '4 seconds')
ON CONFLICT (id) DO NOTHING;
