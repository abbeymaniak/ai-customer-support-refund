-- Database Seed Script for AI Customer Support Refund System
-- Initializes normalized relational schema and seeds 16 realistic profiles, orders, items, audit trails, and security configurations

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Relational Tables

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
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    anomaly_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_context JSONB,
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

CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm VARCHAR(32) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    llm_model VARCHAR(64) NOT NULL,
    api_key VARCHAR(255),
    api_base VARCHAR(255),
    temperature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    timeout_seconds DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    updated_by VARCHAR(128) DEFAULT 'system',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'agent',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS security_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'high',
    source_ip VARCHAR(45),
    endpoint VARCHAR(255) NOT NULL,
    matched_pattern VARCHAR(255),
    payload_preview VARCHAR(500),
    customer_email VARCHAR(255),
    order_number VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Indices for Fast Queries
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
CREATE INDEX IF NOT EXISTS idx_refund_requests_risk_score ON refund_requests(risk_score);
CREATE INDEX IF NOT EXISTS idx_refund_items_refund_request ON refund_items(refund_request_id);
CREATE INDEX IF NOT EXISTS idx_refund_items_order_item ON refund_items(order_item_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_refund_request ON audit_logs(refund_request_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_llm_providers_llm ON llm_providers(llm);
CREATE INDEX IF NOT EXISTS idx_llm_providers_is_active ON llm_providers(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS ix_security_logs_event_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS ix_security_logs_severity ON security_logs(severity);
CREATE INDEX IF NOT EXISTS ix_security_logs_customer_email ON security_logs(customer_email);
CREATE INDEX IF NOT EXISTS ix_security_logs_order_number ON security_logs(order_number);
CREATE INDEX IF NOT EXISTS ix_security_logs_created_at ON security_logs(created_at);

-- 2. Seed Customer Profiles (16 Realistic Personas)
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
ON CONFLICT (id) DO UPDATE SET
    total_spent = EXCLUDED.total_spent,
    orders_count = EXCLUDED.orders_count,
    refunds_count = EXCLUDED.refunds_count,
    return_rate = EXCLUDED.return_rate,
    risk_score = EXCLUDED.risk_score;

-- 3. Seed Realistic Orders Across All 16 Customers
INSERT INTO orders (id, customer_id, order_number, order_date, delivery_date, total_amount, currency, status, items, shipping_address)
VALUES
    -- 1. Sarah Jenkins
    ('01111111-1111-1111-1111-111111111101', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-9001', NOW() - INTERVAL '12 days', NOW() - INTERVAL '10 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-101", "name": "Wireless Ergonomic Mouse", "price": 45.00, "category": "electronics"}, {"id": "item-102", "name": "Mechanical Keyboard Wrist Rest", "price": 40.00, "category": "accessories"}]'::jsonb, '{"city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb),
    ('01111111-1111-1111-1111-111111111102', 'c1111111-1111-1111-1111-111111111111', 'ORD-2026-7840', NOW() - INTERVAL '48 days', NOW() - INTERVAL '45 days', 210.00, 'USD', 'delivered',
     '[{"id": "item-103", "name": "Active Noise Cancelling Earbuds", "price": 210.00, "category": "electronics"}]'::jsonb, '{"city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb),

    -- 2. David Miller
    ('02222222-2222-2222-2222-222222222201', 'c2222222-2222-2222-2222-222222222222', 'ORD-2026-9055', NOW() - INTERVAL '17 days', NOW() - INTERVAL '14 days', 120.00, 'USD', 'delivered',
     '[{"id": "item-201", "name": "Merino Wool Crewneck Sweater", "price": 120.00, "category": "apparel"}]'::jsonb, '{"city": "Austin", "state": "TX", "zip": "73301"}'::jsonb),

    -- 3. Elena Rostova
    ('03333333-3333-3333-3333-333333333301', 'c3333333-3333-3333-3333-333333333333', 'ORD-2026-8812', NOW() - INTERVAL '25 days', NOW() - INTERVAL '22 days', 195.00, 'USD', 'delivered',
     '[{"id": "item-301", "name": "Smart Aroma Diffuser", "price": 75.00, "category": "home_goods"}, {"id": "item-302", "name": "Essential Oils Starter Kit", "price": 120.00, "category": "perishables"}]'::jsonb, '{"city": "Denver", "state": "CO", "zip": "80201"}'::jsonb),

    -- 4. Marcus Vance
    ('04444444-4444-4444-4444-444444444401', 'c4444444-4444-4444-4444-444444444444', 'ORD-2026-9120', NOW() - INTERVAL '10 days', NOW() - INTERVAL '8 days', 350.00, 'USD', 'delivered',
     '[{"id": "item-401", "name": "Pro Gaming Headset", "price": 350.00, "category": "electronics"}]'::jsonb, '{"city": "Chicago", "state": "IL", "zip": "60601"}'::jsonb),

    -- 5. Victoria Sterling
    ('05555555-5555-5555-5555-555555555501', 'c5555555-5555-5555-5555-555555555555', 'ORD-2026-9201', NOW() - INTERVAL '7 days', NOW() - INTERVAL '5 days', 1400.00, 'USD', 'delivered',
     '[{"id": "item-501", "name": "4K Ultra-Wide Curved Monitor 38-inch", "price": 1400.00, "category": "electronics"}]'::jsonb, '{"city": "New York", "state": "NY", "zip": "10001"}'::jsonb),

    -- 6. Alex Rivera
    ('06666666-6666-6666-6666-666666666601', 'c6666666-6666-6666-6666-666666666666', 'ORD-2026-9304', NOW() - INTERVAL '15 days', NOW() - INTERVAL '12 days', 85.00, 'USD', 'delivered',
     '[{"id": "item-601", "name": "Canvas Travel Backpack", "price": 85.00, "category": "accessories"}]'::jsonb, '{"city": "San Francisco", "state": "CA", "zip": "94105"}'::jsonb),

    -- 7. Kevin Chen
    ('07777777-7777-7777-7777-777777777701', 'c7777777-7777-7777-7777-777777777777', 'ORD-2026-7650', NOW() - INTERVAL '43 days', NOW() - INTERVAL '40 days', 450.00, 'USD', 'delivered',
     '[{"id": "item-701", "name": "Robot Vacuum Cleaner", "price": 450.00, "category": "home_goods"}]'::jsonb, '{"city": "Boston", "state": "MA", "zip": "02108"}'::jsonb),

    -- 8. Amanda Price
    ('08888888-8888-8888-8888-888888888801', 'c8888888-8888-8888-8888-888888888888', 'ORD-2026-9040', NOW() - INTERVAL '19 days', NOW() - INTERVAL '16 days', 65.00, 'USD', 'delivered',
     '[{"id": "item-801", "name": "Clearance Winter Parka [Final Sale]", "price": 65.00, "category": "clearance_items"}]'::jsonb, '{"city": "Portland", "state": "OR", "zip": "97201"}'::jsonb),

    -- 9. Chloe Dubois
    ('09999999-9999-9999-9999-999999999901', 'c9999999-9999-9999-9999-999999999999', 'ORD-2026-8710', NOW() - INTERVAL '14 days', NOW() - INTERVAL '11 days', 235.00, 'USD', 'delivered',
     '[{"id": "item-901", "name": "Cashmere Knit Scarf", "price": 95.00, "category": "apparel"}, {"id": "item-902", "name": "Silk Pajama Set", "price": 140.00, "category": "apparel"}]'::jsonb, '{"city": "Los Angeles", "state": "CA", "zip": "90210"}'::jsonb),

    -- 10. Robert Taylor
    ('0aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa01', 'caaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'ORD-2026-8620', NOW() - INTERVAL '22 days', NOW() - INTERVAL '19 days', 185.00, 'USD', 'delivered',
     '[{"id": "item-a01", "name": "Cordless Drill Driver Kit", "price": 130.00, "category": "home_goods"}, {"id": "item-a02", "name": "Heavy Duty Tool Organizer", "price": 55.00, "category": "accessories"}]'::jsonb, '{"city": "Phoenix", "state": "AZ", "zip": "85001"}'::jsonb),

    -- 11. James Wilson
    ('0bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'cbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'ORD-2026-8990', NOW() - INTERVAL '21 days', NOW() - INTERVAL '18 days', 650.00, 'USD', 'delivered',
     '[{"id": "item-b01", "name": "Espresso Machine with Grinder", "price": 650.00, "category": "home_goods"}]'::jsonb, '{"city": "Miami", "state": "FL", "zip": "33101"}'::jsonb),

    -- 12. Maria Santos
    ('0ccccccc-cccc-cccc-cccc-cccccccccc01', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'ORD-2026-8515', NOW() - INTERVAL '16 days', NOW() - INTERVAL '13 days', 350.00, 'USD', 'delivered',
     '[{"id": "item-c01", "name": "Stand Mixer 5-Quart", "price": 320.00, "category": "home_goods"}, {"id": "item-c02", "name": "Silicone Baking Mats Set", "price": 30.00, "category": "home_goods"}]'::jsonb, '{"city": "San Diego", "state": "CA", "zip": "92101"}'::jsonb),

    -- 13. Tyler Brooks
    ('0ddddddd-dddd-dddd-dddd-dddddddddd01', 'cddddddd-dddd-dddd-dddd-dddddddddddd', 'ORD-2026-9410', NOW() - INTERVAL '7 days', NOW() - INTERVAL '5 days', 280.00, 'USD', 'delivered',
     '[{"id": "item-d01", "name": "Designer Leather Jacket", "price": 280.00, "category": "apparel"}]'::jsonb, '{"city": "Atlanta", "state": "GA", "zip": "30301"}'::jsonb),

    -- 14. Emily Watson
    ('0eeeeeee-eeee-eeee-eeee-eeeeeeeeee01', 'ceeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'ORD-2026-8430', NOW() - INTERVAL '28 days', NOW() - INTERVAL '25 days', 430.00, 'USD', 'delivered',
     '[{"id": "item-e01", "name": "Studio Reference Monitor Headphones", "price": 250.00, "category": "electronics"}, {"id": "item-e02", "name": "Desktop USB Audio Interface", "price": 180.00, "category": "electronics"}]'::jsonb, '{"city": "Nashville", "state": "TN", "zip": "37201"}'::jsonb),

    -- 15. Lucas Bennett
    ('0fffffff-ffff-ffff-ffff-ffffffffff01', 'cfffffff-ffff-ffff-ffff-ffffffffffff', 'ORD-2026-8320', NOW() - INTERVAL '11 days', NOW() - INTERVAL '8 days', 110.00, 'USD', 'delivered',
     '[{"id": "item-f01", "name": "Waterproof Fitness Smart Band", "price": 85.00, "category": "electronics"}, {"id": "item-f02", "name": "Breathable Sport Strap", "price": 25.00, "category": "accessories"}]'::jsonb, '{"city": "Minneapolis", "state": "MN", "zip": "55401"}'::jsonb),

    -- 16. Samantha Reed
    ('00000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000000', 'ORD-2026-8210', NOW() - INTERVAL '9 days', NOW() - INTERVAL '6 days', 220.00, 'USD', 'delivered',
     '[{"id": "item-001", "name": "Ultra-Compact Travel Stroller", "price": 220.00, "category": "baby_products"}]'::jsonb, '{"city": "Dallas", "state": "TX", "zip": "75201"}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 4. Seed Dedicated Order Line Items
INSERT INTO order_items (id, order_id, product_id, product_name, category, price, quantity, is_final_sale, serial_number, warranty_status)
VALUES
    -- Sarah Jenkins items
    ('11111111-1111-1111-1111-111111111101', '01111111-1111-1111-1111-111111111101', 'PROD-MOUSE-01', 'Wireless Ergonomic Mouse', 'electronics', 45.00, 1, FALSE, 'SN-MOU-9821', 'standard_1yr'),
    ('11111111-1111-1111-1111-111111111102', '01111111-1111-1111-1111-111111111101', 'PROD-REST-02', 'Mechanical Keyboard Wrist Rest', 'accessories', 40.00, 1, FALSE, NULL, NULL),
    ('11111111-1111-1111-1111-111111111103', '01111111-1111-1111-1111-111111111102', 'PROD-BUDS-03', 'Active Noise Cancelling Earbuds', 'electronics', 210.00, 1, FALSE, 'SN-BUD-4512', 'standard_1yr'),

    -- David Miller items
    ('12222222-2222-2222-2222-222222222201', '02222222-2222-2222-2222-222222222201', 'PROD-SWEATER-01', 'Merino Wool Crewneck Sweater', 'apparel', 120.00, 1, FALSE, NULL, NULL),

    -- Elena Rostova items
    ('13333333-3333-3333-3333-333333333301', '03333333-3333-3333-3333-333333333301', 'PROD-DIFF-01', 'Smart Aroma Diffuser', 'home_goods', 75.00, 1, FALSE, 'SN-DIF-2201', 'standard_1yr'),
    ('13333333-3333-3333-3333-333333333302', '03333333-3333-3333-3333-333333333301', 'PROD-OILS-02', 'Essential Oils Starter Kit', 'perishables', 120.00, 1, FALSE, NULL, NULL),

    -- Marcus Vance items
    ('14444444-4444-4444-4444-444444444401', '04444444-4444-4444-4444-444444444401', 'PROD-HEADSET-01', 'Pro Gaming Headset', 'electronics', 350.00, 1, FALSE, 'SN-GAM-9944', 'extended_2yr'),

    -- Victoria Sterling items
    ('15555555-5555-5555-5555-555555555501', '05555555-5555-5555-5555-555555555501', 'PROD-MON-01', '4K Ultra-Wide Curved Monitor 38-inch', 'electronics', 1400.00, 1, FALSE, 'SN-MON-7718', 'extended_3yr'),

    -- Alex Rivera items
    ('16666666-6666-6666-6666-666666666601', '06666666-6666-6666-6666-666666666601', 'PROD-BAG-01', 'Canvas Travel Backpack', 'accessories', 85.00, 1, FALSE, NULL, NULL),

    -- Kevin Chen items
    ('17777777-7777-7777-7777-777777777701', '07777777-7777-7777-7777-777777777701', 'PROD-VAC-01', 'Robot Vacuum Cleaner', 'home_goods', 450.00, 1, FALSE, 'SN-VAC-3310', 'standard_1yr'),

    -- Amanda Price items
    ('18888888-8888-8888-8888-888888888801', '08888888-8888-8888-8888-888888888801', 'PROD-PARKA-01', 'Clearance Winter Parka [Final Sale]', 'clearance_items', 65.00, 1, TRUE, NULL, NULL),

    -- Chloe Dubois items
    ('19999999-9999-9999-9999-999999999901', '09999999-9999-9999-9999-999999999901', 'PROD-SCARF-01', 'Cashmere Knit Scarf', 'apparel', 95.00, 1, FALSE, NULL, NULL),
    ('19999999-9999-9999-9999-999999999902', '09999999-9999-9999-9999-999999999901', 'PROD-PAJAMA-02', 'Silk Pajama Set', 'apparel', 140.00, 1, FALSE, NULL, NULL),

    -- Robert Taylor items
    ('1aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa01', '0aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa01', 'PROD-DRILL-01', 'Cordless Drill Driver Kit', 'home_goods', 130.00, 1, FALSE, 'SN-DRL-4102', 'standard_1yr'),
    ('1aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa02', '0aaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa01', 'PROD-TOOLBOX-02', 'Heavy Duty Tool Organizer', 'accessories', 55.00, 1, FALSE, NULL, NULL),

    -- James Wilson items
    ('1bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '0bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'PROD-ESPRESSO-01', 'Espresso Machine with Grinder', 'home_goods', 650.00, 1, FALSE, 'SN-ESP-5521', 'standard_1yr'),

    -- Maria Santos items
    ('1ccccccc-cccc-cccc-cccc-cccccccccc01', '0ccccccc-cccc-cccc-cccc-cccccccccc01', 'PROD-MIXER-01', 'Stand Mixer 5-Quart', 'home_goods', 320.00, 1, FALSE, 'SN-MIX-8891', 'standard_1yr'),
    ('1ccccccc-cccc-cccc-cccc-cccccccccc02', '0ccccccc-cccc-cccc-cccc-cccccccccc01', 'PROD-MATS-02', 'Silicone Baking Mats Set', 'home_goods', 30.00, 1, FALSE, NULL, NULL),

    -- Tyler Brooks items
    ('1ddddddd-dddd-dddd-dddd-dddddddddd01', '0ddddddd-dddd-dddd-dddd-dddddddddd01', 'PROD-JACKET-01', 'Designer Leather Jacket', 'apparel', 280.00, 1, FALSE, NULL, NULL),

    -- Emily Watson items
    ('1eeeeeee-eeee-eeee-eeee-eeeeeeeeee01', '0eeeeeee-eeee-eeee-eeee-eeeeeeeeee01', 'PROD-STUDIO-01', 'Studio Reference Monitor Headphones', 'electronics', 250.00, 1, FALSE, 'SN-STU-3329', 'standard_1yr'),
    ('1eeeeeee-eeee-eeee-eeee-eeeeeeeeee02', '0eeeeeee-eeee-eeee-eeee-eeeeeeeeee01', 'PROD-AUDIO-02', 'Desktop USB Audio Interface', 'electronics', 180.00, 1, FALSE, 'SN-AUD-1192', 'standard_1yr'),

    -- Lucas Bennett items
    ('1fffffff-ffff-ffff-ffff-ffffffffff01', '0fffffff-ffff-ffff-ffff-ffffffffff01', 'PROD-BAND-01', 'Waterproof Fitness Smart Band', 'electronics', 85.00, 1, FALSE, 'SN-BND-7711', 'standard_1yr'),
    ('1fffffff-ffff-ffff-ffff-ffffffffff02', '0fffffff-ffff-ffff-ffff-ffffffffff01', 'PROD-STRAP-02', 'Breathable Sport Strap', 'accessories', 25.00, 1, FALSE, NULL, NULL),

    -- Samantha Reed items
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'PROD-STROLL-01', 'Ultra-Compact Travel Stroller', 'baby_products', 220.00, 1, FALSE, 'SN-STR-5541', 'standard_1yr')
ON CONFLICT (id) DO NOTHING;

-- 5. Seed Representative Refund Requests (Approved, Denied, Escalated, Pending)
INSERT INTO refund_requests (id, request_number, customer_id, order_id, item_id, item_name, amount, total_refund_amount, currency, status, reason_category, customer_explanation, decision, decision_reason, confidence_score, policy_checks, ai_decision, ai_confidence, ai_reasoning, risk_score, anomaly_flags, created_at)
VALUES
    -- Approved: Sarah Jenkins
    ('21111111-1111-1111-1111-111111111101', 'REF-2026-0001', 'c1111111-1111-1111-1111-111111111111', '01111111-1111-1111-1111-111111111101', '11111111-1111-1111-1111-111111111101', 'Wireless Ergonomic Mouse', 45.00, 45.00, 'USD', 'approved', 'defective', 'The scroll wheel became unresponsive after three days of normal use.', 'Approved', 'Purchased within return window, verified customer with 0.05 risk score, eligible category.', 0.95, '{"within_return_window": true, "eligible_category": true, "acceptable_risk_score": true}'::jsonb, 'Approved', 0.95, 'Approved: Customer is low risk and order is well within the 30-day window.', 0.05, '[]'::jsonb, NOW() - INTERVAL '2 days'),

    -- Denied: Amanda Price (Clearance Final Sale guardrail override)
    ('28888888-8888-8888-8888-888888888801', 'REF-2026-0002', 'c8888888-8888-8888-8888-888888888888', '08888888-8888-8888-8888-888888888801', '18888888-8888-8888-8888-888888888801', 'Clearance Winter Parka [Final Sale]', 65.00, 65.00, 'USD', 'denied', 'unwanted', 'Did not fit as expected.', 'Denied', 'Non-negotiable policy guardrail: Final sale and clearance items cannot be refunded. AI approval overridden.', 1.0, '{"is_final_sale": true, "guardrail_triggered": "FINAL_SALE_CLEARANCE"}'::jsonb, 'Denied', 1.0, 'Denied by deterministic guardrail override.', 0.15, '[]'::jsonb, NOW() - INTERVAL '1 day'),

    -- Escalated: James Wilson (High value item > $200)
    ('2bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'REF-2026-0003', 'cbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '0bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '1bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'Espresso Machine with Grinder', 650.00, 650.00, 'USD', 'escalated', 'defective', 'Water pump makes grinding noise and fails to pull espresso shots.', 'Escalated', 'Automated anomaly detected: High value cluster detected. Escalating for supervisor manual review.', 0.88, '{"high_value_cluster": true}'::jsonb, 'Escalated', 0.88, 'Escalated due to high item value exceeding threshold.', 0.70, '["high_value_cluster"]'::jsonb, NOW() - INTERVAL '18 hours'),

    -- Pending: Marcus Vance (Awaiting human review)
    ('24444444-4444-4444-4444-444444444401', 'REF-2026-0004', 'c4444444-4444-4444-4444-444444444444', '04444444-4444-4444-4444-444444444401', '14444444-4444-4444-4444-444444444401', 'Pro Gaming Headset', 350.00, 350.00, 'USD', 'escalated', 'unwanted', 'Sound profile is too sharp for my audio setup.', 'Escalated', 'Customer risk score 0.85 requires human review before processing.', 0.80, '{"risk_level": "high"}'::jsonb, 'Escalated', 0.80, 'Customer return frequency exceeds standard limits.', 0.85, '["high_value_cluster"]'::jsonb, NOW() - INTERVAL '6 hours')
ON CONFLICT (id) DO NOTHING;

-- Seed Refund Line Items
INSERT INTO refund_items (id, refund_request_id, order_item_id, quantity, refund_amount, item_condition)
VALUES
    ('31111111-1111-1111-1111-111111111101', '21111111-1111-1111-1111-111111111101', '11111111-1111-1111-1111-111111111101', 1, 45.00, 'opened'),
    ('38888888-8888-8888-8888-888888888801', '28888888-8888-8888-8888-888888888801', '18888888-8888-8888-8888-888888888801', 1, 65.00, 'unopened'),
    ('3bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '2bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '1bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 1, 650.00, 'opened_used'),
    ('34444444-4444-4444-4444-444444444401', '24444444-4444-4444-4444-444444444401', '14444444-4444-4444-4444-444444444401', 1, 350.00, 'unopened')
ON CONFLICT (id) DO NOTHING;

-- 6. Seed Audit Logs
INSERT INTO audit_logs (id, refund_request_id, action, actor, details, timestamp)
VALUES
    ('a1111111-1111-1111-1111-111111111101', '21111111-1111-1111-1111-111111111101', 'request_submitted', 'customer', '{"amount": 45.00, "item": "Wireless Ergonomic Mouse", "order": "ORD-2026-9001"}'::jsonb, NOW() - INTERVAL '2 days'),
    ('a1111111-1111-1111-1111-111111111102', '21111111-1111-1111-1111-111111111101', 'ai_evaluated', 'ai_engine', '{"decision": "Approved", "confidence": 0.95, "model": "gpt-4o-mini", "prompt_tokens": 420, "completion_tokens": 85}'::jsonb, NOW() - INTERVAL '2 days' + INTERVAL '3 seconds'),
    ('a1111111-1111-1111-1111-111111111103', '21111111-1111-1111-1111-111111111101', 'status_updated', 'system', '{"from": "pending", "to": "approved"}'::jsonb, NOW() - INTERVAL '2 days' + INTERVAL '4 seconds'),
    ('a8888888-8888-8888-8888-888888888801', '28888888-8888-8888-8888-888888888801', 'request_submitted', 'customer', '{"amount": 65.00, "item": "Clearance Winter Parka [Final Sale]", "order": "ORD-2026-9040"}'::jsonb, NOW() - INTERVAL '1 day'),
    ('a8888888-8888-8888-8888-888888888802', '28888888-8888-8888-8888-888888888801', 'policy_guardrail_applied', 'policy_service', '{"overridden": true, "reason": "FINAL_SALE_CLEARANCE"}'::jsonb, NOW() - INTERVAL '1 day' + INTERVAL '2 seconds'),
    ('abbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '2bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', 'anomaly_detected', 'anomaly_service', '{"flags": ["high_value_cluster"], "risk_score": 0.70}'::jsonb, NOW() - INTERVAL '18 hours')
ON CONFLICT (id) DO NOTHING;

-- 7. Seed Admin Accounts
-- Default passwords:
-- admin@store.com / admin123
-- admin@refunds.internal / AdminPassword123!
-- lead@store.com / lead123
INSERT INTO admin_users (id, email, password_hash, name, role, is_active, created_at)
VALUES
    ('ba111111-1111-1111-1111-111111111101', 'admin@store.com', '$2b$12$9ua7iO66MzjehMDyrxlAbO6OfcOZhTAJumvPn.fmdCPg/2qvALjBe', 'Store Administrator', 'admin', TRUE, NOW()),
    ('ba111111-1111-1111-1111-111111111102', 'admin@refunds.internal', '$2b$12$IKm8ge0VxgH1UmAZHrLgYeTFzPvSNGLVVxq5pYwDWPwh9vRmppxA2', 'System Administrator', 'admin', TRUE, NOW()),
    ('ba222222-2222-2222-2222-222222222201', 'lead@store.com', '$2b$12$9NoplASyAhvXD8oxxhChJuWLaDB4Paqf6M86VDNoQILwDngTJupqS', 'Support Lead', 'agent', TRUE, NOW())
ON CONFLICT (email) DO NOTHING;

-- 8. Seed Default Multi-Provider LLM Slots
INSERT INTO llm_providers (id, llm, is_active, llm_model, api_key, api_base, temperature, timeout_seconds, updated_by)
VALUES
    ('bb111111-1111-1111-1111-111111111101', 'ollama', TRUE, 'llama3', NULL, 'http://host.docker.internal:11434', 0.0, 60.0, 'system_seed'),
    ('bb222222-2222-2222-2222-222222222201', 'openai', FALSE, 'gpt-4o-mini', NULL, NULL, 0.0, 15.0, 'system_seed'),
    ('bb333333-3333-3333-3333-333333333301', 'gemini', FALSE, 'gemini-1.5-flash', NULL, NULL, 0.0, 15.0, 'system_seed')
ON CONFLICT (llm) DO NOTHING;

-- 9. Initialize Alembic Head Version
INSERT INTO alembic_version (version_num)
VALUES ('0005_security_hardening')
ON CONFLICT (version_num) DO NOTHING;
