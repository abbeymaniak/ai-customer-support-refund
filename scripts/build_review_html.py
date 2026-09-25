#!/usr/bin/env python3
"""Build script for generating review.html with interactive SVG database relationship diagram.

This script creates a self-contained, responsive HTML presentation document
explaining the AI Customer Support Refund System architecture, decisions,
security models, and database design with zero external CDN dependencies.
"""

from pathlib import Path

SCHEMA_DATA = [
    {
        "id": "customers",
        "name": "customers",
        "category": "commerce",
        "description": "Customer account master profile with cumulative purchasing and fraud risk metrics.",
        "x": 60,
        "y": 60,
        "width": 220,
        "height": 260,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "email",
                "type": "VARCHAR(255)",
                "unique": True,
                "desc": "Customer email address (indexed)",
            },
            {
                "name": "name",
                "type": "VARCHAR(255)",
                "desc": "Customer full legal name",
            },
            {
                "name": "total_spent",
                "type": "FLOAT",
                "desc": "Lifetime gross purchase total",
            },
            {
                "name": "orders_count",
                "type": "INTEGER",
                "desc": "Total completed orders count",
            },
            {
                "name": "refunds_count",
                "type": "INTEGER",
                "desc": "Total completed refunds count",
            },
            {
                "name": "return_rate",
                "type": "FLOAT",
                "desc": "Ratio of refunds to orders",
            },
            {
                "name": "risk_score",
                "type": "FLOAT",
                "desc": "Composite fraud risk rating (0.0 - 1.0)",
            },
            {
                "name": "account_created_at",
                "type": "TIMESTAMP",
                "desc": "Initial signup timestamp",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "orders",
        "name": "orders",
        "category": "commerce",
        "description": "E-commerce purchase orders with shipping destinations and delivery confirmation.",
        "x": 360,
        "y": 60,
        "width": 220,
        "height": 260,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "customer_id",
                "type": "UUID",
                "fk": "customers.id",
                "desc": "Reference to purchasing customer",
            },
            {
                "name": "order_number",
                "type": "VARCHAR(64)",
                "unique": True,
                "desc": "Human readable order number (ORD-...)",
            },
            {
                "name": "order_date",
                "type": "TIMESTAMP",
                "desc": "Order checkout timestamp",
            },
            {
                "name": "delivery_date",
                "type": "TIMESTAMP",
                "desc": "Carrier delivery timestamp (null if pending)",
            },
            {
                "name": "total_amount",
                "type": "FLOAT",
                "desc": "Total checkout charge amount",
            },
            {
                "name": "currency",
                "type": "VARCHAR(3)",
                "desc": "ISO currency code (USD)",
            },
            {
                "name": "status",
                "type": "VARCHAR(32)",
                "desc": "Order state (delivered, transit, cancelled)",
            },
            {
                "name": "items",
                "type": "JSONB",
                "desc": "Snapshot of purchased items list",
            },
            {
                "name": "shipping_address",
                "type": "JSONB",
                "desc": "Customer delivery address payload",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "order_items",
        "name": "order_items",
        "category": "commerce",
        "description": "Normalized line items within an order with category and final sale attributes.",
        "x": 660,
        "y": 60,
        "width": 220,
        "height": 260,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "order_id",
                "type": "UUID",
                "fk": "orders.id",
                "desc": "Parent order reference",
            },
            {
                "name": "product_id",
                "type": "VARCHAR(64)",
                "desc": "SKU catalog identifier",
            },
            {
                "name": "product_name",
                "type": "VARCHAR(255)",
                "desc": "Item display title",
            },
            {
                "name": "category",
                "type": "VARCHAR(64)",
                "desc": "Product category (electronics, apparel, clearance)",
            },
            {"name": "price", "type": "FLOAT", "desc": "Unit sale price"},
            {"name": "quantity", "type": "INTEGER", "desc": "Purchased unit count"},
            {
                "name": "is_final_sale",
                "type": "BOOLEAN",
                "desc": "Non-refundable clearance exclusion flag",
            },
            {
                "name": "serial_number",
                "type": "VARCHAR(128)",
                "desc": "Unique device serial if applicable",
            },
            {
                "name": "warranty_status",
                "type": "VARCHAR(64)",
                "desc": "Warranty coverage terms",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "refund_requests",
        "name": "refund_requests",
        "category": "refunds",
        "description": "Customer refund claim lifecycle record containing AI verdicts and anomaly telemetry.",
        "x": 360,
        "y": 400,
        "width": 220,
        "height": 280,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "customer_id",
                "type": "UUID",
                "fk": "customers.id",
                "desc": "Claimant customer reference",
            },
            {
                "name": "order_id",
                "type": "UUID",
                "fk": "orders.id",
                "desc": "Target purchase order reference",
            },
            {
                "name": "status",
                "type": "VARCHAR(32)",
                "desc": "Lifecycle state (approved, denied, escalated, pending)",
            },
            {
                "name": "decision_reason",
                "type": "TEXT",
                "desc": "Detailed policy or AI evaluation explanation",
            },
            {
                "name": "confidence",
                "type": "FLOAT",
                "desc": "AI model certainty metric (0.0 - 1.0)",
            },
            {
                "name": "refund_amount",
                "type": "FLOAT",
                "desc": "Total financial refund value approved",
            },
            {
                "name": "policy_checks",
                "type": "JSONB",
                "desc": "Structured checklist of all evaluated rules",
            },
            {
                "name": "risk_score",
                "type": "FLOAT",
                "desc": "Calculated claim risk rating",
            },
            {
                "name": "anomaly_flags",
                "type": "JSONB",
                "desc": "Detected fraud markers (velocity, high value)",
            },
            {
                "name": "error_context",
                "type": "JSONB",
                "desc": "Captured exception data during AI outage",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "refund_items",
        "name": "refund_items",
        "category": "refunds",
        "description": "Specific line items claimed for refund with claimed condition and approved amounts.",
        "x": 660,
        "y": 400,
        "width": 220,
        "height": 220,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "refund_request_id",
                "type": "UUID",
                "fk": "refund_requests.id",
                "desc": "Parent refund claim reference",
            },
            {
                "name": "order_item_id",
                "type": "UUID",
                "fk": "order_items.id",
                "desc": "Referenced purchased line item",
            },
            {
                "name": "reason",
                "type": "TEXT",
                "desc": "Customer provided return explanation",
            },
            {
                "name": "item_condition",
                "type": "VARCHAR(64)",
                "desc": "Reported condition (unopened, defective, damaged)",
            },
            {
                "name": "requested_amount",
                "type": "FLOAT",
                "desc": "Customer requested dollar amount",
            },
            {
                "name": "approved_amount",
                "type": "FLOAT",
                "desc": "Approved payout dollar amount",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "audit_logs",
        "name": "audit_logs",
        "category": "refunds",
        "description": "Immutable append-only audit trail recording every state transition and supervisor action.",
        "x": 60,
        "y": 400,
        "width": 220,
        "height": 220,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "refund_request_id",
                "type": "UUID",
                "fk": "refund_requests.id",
                "desc": "Target refund claim reference",
            },
            {
                "name": "actor",
                "type": "VARCHAR(64)",
                "desc": "Executing agent (system, ai_agent, supervisor)",
            },
            {
                "name": "action",
                "type": "VARCHAR(64)",
                "desc": "Action performed (created, evaluated, overridden)",
            },
            {
                "name": "previous_status",
                "type": "VARCHAR(32)",
                "desc": "Status prior to transition",
            },
            {
                "name": "new_status",
                "type": "VARCHAR(32)",
                "desc": "Resulting lifecycle status",
            },
            {
                "name": "reason",
                "type": "TEXT",
                "desc": "Justification for status transition",
            },
            {
                "name": "metadata_snapshot",
                "type": "JSONB",
                "desc": "Full contextual state payload",
            },
            {
                "name": "timestamp",
                "type": "TIMESTAMP",
                "desc": "Immutable event timestamp",
            },
        ],
    },
    {
        "id": "admin_users",
        "name": "admin_users",
        "category": "auth",
        "description": "Administrative support agents and system supervisors with bcrypt credentials.",
        "x": 60,
        "y": 700,
        "width": 220,
        "height": 200,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "email",
                "type": "VARCHAR(255)",
                "unique": True,
                "desc": "Admin login username",
            },
            {
                "name": "password_hash",
                "type": "VARCHAR(255)",
                "desc": "Bcrypt salted password hash (12 rounds)",
            },
            {"name": "name", "type": "VARCHAR(255)", "desc": "Staff member full name"},
            {
                "name": "role",
                "type": "VARCHAR(32)",
                "desc": "Authorization role (admin, agent)",
            },
            {
                "name": "is_active",
                "type": "BOOLEAN",
                "desc": "Account activation status",
            },
            {
                "name": "last_login_at",
                "type": "TIMESTAMP",
                "desc": "Most recent session start timestamp",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "refresh_tokens",
        "name": "refresh_tokens",
        "category": "auth",
        "description": "Cryptographically hashed JWT refresh tokens supporting single-use rotation and replay detection.",
        "x": 360,
        "y": 700,
        "width": 220,
        "height": 180,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "user_id",
                "type": "UUID",
                "fk": "admin_users.id",
                "desc": "Associated admin account reference",
            },
            {
                "name": "token_hash",
                "type": "VARCHAR(64)",
                "unique": True,
                "desc": "SHA-256 hash of plaintext refresh token",
            },
            {
                "name": "expires_at",
                "type": "TIMESTAMP",
                "desc": "Token expiration deadline",
            },
            {
                "name": "revoked",
                "type": "BOOLEAN",
                "desc": "Revocation flag on logout or replay",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Token issuance timestamp",
            },
        ],
    },
    {
        "id": "llm_providers",
        "name": "llm_providers",
        "category": "security",
        "description": "Dynamic multi-provider AI model configurations with live runtime switching.",
        "x": 660,
        "y": 700,
        "width": 220,
        "height": 220,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "llm",
                "type": "VARCHAR(64)",
                "desc": "Provider engine (ollama, openai, gemini)",
            },
            {
                "name": "is_active",
                "type": "BOOLEAN",
                "desc": "Active default evaluation provider",
            },
            {
                "name": "llm_model",
                "type": "VARCHAR(128)",
                "desc": "Model identifier (gpt-4o-mini, llama3, gemini-1.5-flash)",
            },
            {
                "name": "api_key",
                "type": "VARCHAR(255)",
                "desc": "Configured provider secret (null for local Ollama)",
            },
            {
                "name": "api_base",
                "type": "VARCHAR(255)",
                "desc": "Custom endpoint base URL (http://ollama:11434)",
            },
            {
                "name": "temperature",
                "type": "FLOAT",
                "desc": "Deterministic sampling temperature (0.0)",
            },
            {
                "name": "timeout_seconds",
                "type": "FLOAT",
                "desc": "HTTP gateway timeout limit",
            },
            {
                "name": "updated_by",
                "type": "VARCHAR(128)",
                "desc": "Last modifier administrator",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Record creation timestamp",
            },
            {
                "name": "updated_at",
                "type": "TIMESTAMP",
                "desc": "Last update timestamp",
            },
        ],
    },
    {
        "id": "security_logs",
        "name": "security_logs",
        "category": "security",
        "description": "Security incident telemetry logging adversarial prompt injection and guardrail breaches.",
        "x": 360,
        "y": 940,
        "width": 220,
        "height": 200,
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "pk": True,
                "desc": "Primary key identifier",
            },
            {
                "name": "event_type",
                "type": "VARCHAR(64)",
                "desc": "Security event classification",
            },
            {
                "name": "customer_id",
                "type": "UUID",
                "fk": "customers.id",
                "desc": "Associated customer if identified",
            },
            {
                "name": "refund_request_id",
                "type": "UUID",
                "fk": "refund_requests.id",
                "desc": "Associated claim if linked",
            },
            {
                "name": "severity",
                "type": "VARCHAR(32)",
                "desc": "Severity rating (low, medium, high, critical)",
            },
            {
                "name": "details",
                "type": "JSONB",
                "desc": "Sanitizer match or guardrail violation details",
            },
            {
                "name": "client_ip",
                "type": "VARCHAR(45)",
                "desc": "Originating client IP address",
            },
            {
                "name": "created_at",
                "type": "TIMESTAMP",
                "desc": "Event detection timestamp",
            },
        ],
    },
]

RELATIONSHIPS = [
    {
        "from": "customers",
        "to": "orders",
        "label": "1:N Orders",
        "coords": "M 280 160 C 320 160, 320 160, 360 160",
    },
    {
        "from": "orders",
        "to": "order_items",
        "label": "1:N Line Items",
        "coords": "M 580 160 C 620 160, 620 160, 660 160",
    },
    {
        "from": "customers",
        "to": "refund_requests",
        "label": "1:N Claims",
        "coords": "M 280 200 C 320 200, 320 460, 360 460",
    },
    {
        "from": "orders",
        "to": "refund_requests",
        "label": "1:N Claims",
        "coords": "M 470 320 C 470 360, 470 360, 470 400",
    },
    {
        "from": "refund_requests",
        "to": "refund_items",
        "label": "1:N Claim Items",
        "coords": "M 580 480 C 620 480, 620 480, 660 480",
    },
    {
        "from": "order_items",
        "to": "refund_items",
        "label": "1:N Claim Items",
        "coords": "M 770 320 C 770 360, 770 360, 770 400",
    },
    {
        "from": "refund_requests",
        "to": "audit_logs",
        "label": "1:N Audit Logs",
        "coords": "M 360 500 C 320 500, 320 500, 280 500",
    },
    {
        "from": "admin_users",
        "to": "refresh_tokens",
        "label": "1:N Sessions",
        "coords": "M 280 780 C 320 780, 320 780, 360 780",
    },
    {
        "from": "customers",
        "to": "security_logs",
        "label": "1:N Incidents",
        "coords": "M 170 320 C 170 980, 320 980, 360 980",
    },
    {
        "from": "refund_requests",
        "to": "security_logs",
        "label": "1:N Incidents",
        "coords": "M 470 680 C 470 800, 470 850, 470 940",
    },
]


def generate_html() -> str:
    """Generate the full HTML document string."""
    import json

    schema_json = json.dumps(SCHEMA_DATA)
    rel_json = json.dumps(RELATIONSHIPS)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Customer Support Refund System — Architectural Review & Specification</title>
  <style>
    :root {{
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-tertiary: #334155;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --success: #34d399;
      --warning: #fbbf24;
      --danger: #f87171;
      --card-bg: rgba(30, 41, 59, 0.7);
      --radius: 12px;
      --font-main: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-main);
      background-color: var(--bg-primary);
      color: var(--text-main);
      line-height: 1.6;
      scroll-behavior: smooth;
    }}

    /* Header & Navigation */
    header {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .logo-area {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .logo-badge {{
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: white;
      font-weight: 700;
      font-size: 0.85rem;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
    }}

    .logo-title {{
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: -0.01em;
    }}

    nav {{
      display: flex;
      gap: 1.25rem;
      align-items: center;
    }}

    nav a {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      transition: color 0.2s;
    }}

    nav a:hover {{
      color: var(--accent);
    }}

    /* Main Container */
    .container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 2.5rem 2rem;
    }}

    /* Hero Section */
    .hero {{
      text-align: center;
      padding: 3rem 1rem 4rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 3rem;
    }}

    .hero-tags {{
      display: flex;
      justify-content: center;
      gap: 0.5rem;
      margin-bottom: 1rem;
      flex-wrap: wrap;
    }}

    .tag {{
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.2rem 0.6rem;
      border-radius: 20px;
      background: var(--bg-tertiary);
      color: var(--text-muted);
      border: 1px solid var(--border);
    }}

    .tag.primary {{
      background: var(--accent-glow);
      color: var(--accent);
      border-color: rgba(56, 189, 248, 0.4);
    }}

    .tag.success {{
      background: rgba(52, 211, 153, 0.15);
      color: var(--success);
      border-color: rgba(52, 211, 153, 0.4);
    }}

    .hero h1 {{
      font-size: 2.75rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: 1.25rem;
      background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .hero p {{
      font-size: 1.15rem;
      color: var(--text-muted);
      max-width: 840px;
      margin: 0 auto 2rem;
    }}

    .metrics-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.25rem;
      margin-top: 2rem;
    }}

    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem;
      text-align: center;
    }}

    .metric-val {{
      font-size: 2rem;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 0.25rem;
    }}

    .metric-lbl {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}

    /* Section Styling */
    section {{
      margin-bottom: 4.5rem;
    }}

    .section-header {{
      margin-bottom: 2rem;
    }}

    .section-header h2 {{
      font-size: 1.85rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .section-header p {{
      color: var(--text-muted);
      font-size: 1rem;
    }}

    /* Cards & Grids */
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 1.5rem;
    }}

    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      transition: transform 0.2s, border-color 0.2s;
    }}

    .card:hover {{
      border-color: rgba(56, 189, 248, 0.4);
    }}

    .card-title {{
      font-size: 1.15rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #fff;
    }}

    /* Callout Alert */
    .callout {{
      border-left: 4px solid var(--accent);
      background: rgba(56, 189, 248, 0.08);
      padding: 1rem 1.25rem;
      border-radius: 0 var(--radius) var(--radius) 0;
      margin: 1.25rem 0;
    }}

    .callout.warning {{
      border-color: var(--warning);
      background: rgba(251, 191, 36, 0.08);
    }}

    .callout.success {{
      border-color: var(--success);
      background: rgba(52, 211, 153, 0.08);
    }}

    /* Interactive Diagram Canvas */
    .diagram-container {{
      background: #090d16;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 750px;
      position: relative;
    }}

    .diagram-toolbar {{
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 0.75rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}

    .diagram-filters {{
      display: flex;
      gap: 0.5rem;
    }}

    .btn {{
      background: var(--bg-tertiary);
      color: var(--text-main);
      border: 1px solid var(--border);
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.2s, border-color 0.2s;
    }}

    .btn:hover {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--accent);
    }}

    .btn.active {{
      background: var(--accent);
      color: #0f172a;
      font-weight: 600;
      border-color: var(--accent);
    }}

    .diagram-controls {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .diagram-canvas-wrap {{
      flex: 1;
      position: relative;
      overflow: hidden;
      cursor: grab;
    }}

    .diagram-canvas-wrap:active {{
      cursor: grabbing;
    }}

    #erd-svg {{
      width: 100%;
      height: 100%;
      user-select: none;
    }}

    /* Table Node Styling */
    .table-node {{
      cursor: pointer;
      transition: filter 0.2s;
    }}

    .table-node:hover {{
      filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));
    }}

    .node-header {{
      fill: #1e293b;
      stroke: #475569;
      stroke-width: 1.5;
    }}

    .node-header.commerce {{
      fill: #0c4a6e;
      stroke: #0284c7;
    }}

    .node-header.refunds {{
      fill: #064e3b;
      stroke: #059669;
    }}

    .node-header.auth {{
      fill: #4c1d95;
      stroke: #7c3aed;
    }}

    .node-header.security {{
      fill: #78350f;
      stroke: #d97706;
    }}

    .node-body {{
      fill: #0f172a;
      stroke: #334155;
      stroke-width: 1;
    }}

    .node-title {{
      fill: #f8fafc;
      font-size: 13px;
      font-weight: 700;
      font-family: var(--font-mono);
    }}

    .col-text {{
      fill: #cbd5e1;
      font-size: 10.5px;
      font-family: var(--font-mono);
    }}

    .col-pk {{
      fill: #fbbf24;
      font-weight: 700;
    }}

    .col-fk {{
      fill: #38bdf8;
      font-weight: 600;
    }}

    .col-type {{
      fill: #64748b;
      font-size: 9.5px;
    }}

    .rel-line {{
      fill: none;
      stroke: #475569;
      stroke-width: 1.5;
      stroke-dasharray: 4;
      transition: stroke 0.3s, stroke-width 0.3s;
    }}

    .rel-line.highlight {{
      stroke: #38bdf8;
      stroke-width: 2.5;
      stroke-dasharray: 0;
    }}

    /* Inspector Drawer */
    .inspector-card {{
      position: absolute;
      right: 1.5rem;
      bottom: 1.5rem;
      width: 340px;
      max-height: 480px;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid var(--accent);
      border-radius: var(--radius);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(12px);
      padding: 1.25rem;
      display: none;
      flex-direction: column;
      z-index: 50;
      overflow-y: auto;
    }}

    .inspector-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.5rem;
    }}

    .inspector-title {{
      font-family: var(--font-mono);
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--accent);
    }}

    .inspector-close {{
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 1.2rem;
    }}

    .inspector-desc {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }}

    .col-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}

    .col-item {{
      background: var(--bg-secondary);
      padding: 0.4rem 0.6rem;
      border-radius: 6px;
      font-size: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--font-mono);
    }}

    /* Screenshots Walkthrough Gallery */
    .screenshot-card {{
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      margin-bottom: 2.5rem;
    }}

    .screenshot-header {{
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .screenshot-caption {{
      font-weight: 600;
      font-size: 1.05rem;
    }}

    .screenshot-img-wrap {{
      background: #000;
      text-align: center;
      padding: 1rem;
    }}

    .screenshot-img-wrap img {{
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
      border: 1px solid #334155;
    }}

    .screenshot-footer {{
      padding: 1rem 1.5rem;
      font-size: 0.9rem;
      color: var(--text-muted);
      background: rgba(15, 23, 42, 0.6);
    }}

    /* Table Component */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.5rem 0;
      font-size: 0.9rem;
    }}

    th, td {{
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}

    th {{
      background: var(--bg-secondary);
      color: var(--text-main);
      font-weight: 600;
    }}

    tr:hover td {{
      background: rgba(56, 189, 248, 0.04);
    }}

    code {{
      font-family: var(--font-mono);
      font-size: 0.85em;
      background: var(--bg-tertiary);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      color: var(--accent);
    }}

    pre {{
      background: #090d16;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem;
      overflow-x: auto;
      margin: 1rem 0;
    }}

    pre code {{
      background: none;
      padding: 0;
      color: #e2e8f0;
      font-size: 0.9rem;
    }}

    footer {{
      text-align: center;
      padding: 3rem 1rem;
      border-top: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>

  <header>
    <div class="logo-area">
      <span class="logo-badge">SYSTEM REVIEW</span>
      <span class="logo-title">AI Customer Support Refund System</span>
    </div>
    <nav>
      <a href="#overview">Overview</a>
      <a href="#architecture">Architecture</a>
      <a href="#database">Interactive Schema</a>
      <a href="#policy-engine">AI Policy Engine</a>
      <a href="#security">Security</a>
      <a href="#walkthrough">Visual Walkthrough</a>
      <a href="#testing">Testing</a>
    </nav>
  </header>

  <div class="container">

    <!-- Hero Section -->
    <div class="hero" id="overview">
      <div class="hero-tags">
        <span class="tag primary">FastAPI 3.11</span>
        <span class="tag primary">React 18 + Vite</span>
        <span class="tag primary">Tailwind CSS v4</span>
        <span class="tag success">PostgreSQL 16</span>
        <span class="tag success">LiteLLM Unified Gateway</span>
        <span class="tag">Docker Compose</span>
      </div>
      <h1>Automated Refund Decision Engine &amp; Anomaly Hardening</h1>
      <p>
        A production ready full stack web application that evaluates e-commerce customer refund claims against machine readable policy documents, customer transaction histories, and real time fraud metrics. Delivers defensible, auditable refund decisions with sub-second response times.
      </p>

      <div class="metrics-bar">
        <div class="metric-card">
          <div class="metric-val">194</div>
          <div class="metric-lbl">Automated Tests (112 Backend + 82 Frontend)</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">10</div>
          <div class="metric-lbl">Normalized PostgreSQL Tables</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">16</div>
          <div class="metric-lbl">Seeded Persona Edge Cases</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">3</div>
          <div class="metric-lbl">Runtime Multi-Provider LLMs</div>
        </div>
      </div>
    </div>

    <!-- Chapter 1: Architecture -->
    <section id="architecture">
      <div class="section-header">
        <h2>1. System Architecture &amp; Clean Boundaries</h2>
        <p>Layered separation of presentation routes, domain services, data models, and reverse proxy networking.</p>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-title">Backend Architecture (FastAPI &amp; SQLAlchemy 2.0)</div>
          <p>
            The backend implements Clean Architecture principles. HTTP route handlers perform Pydantic request validation and delegate directly to isolated application services:
          </p>
          <ul style="margin: 0.75rem 0 0 1.25rem; color: var(--text-muted);">
            <li><strong>CustomerService:</strong> Profile lookup and historical order aggregations.</li>
            <li><strong>PolicyService:</strong> Two phase evaluation and deterministic guardrails.</li>
            <li><strong>AnomalyService:</strong> Sliding window velocity and fraud cluster detection.</li>
            <li><strong>SecurityService:</strong> Multi-pattern prompt injection and XSS sanitization.</li>
            <li><strong>AuthService:</strong> Bcrypt password verification and cryptographic JWT rotation.</li>
          </ul>
        </div>

        <div class="card">
          <div class="card-title">Frontend Architecture (React 18 &amp; Tailwind v4)</div>
          <p>
            The frontend uses modern React 18 with TanStack Query for cache invalidation and state synchronization:
          </p>
          <ul style="margin: 0.75rem 0 0 1.25rem; color: var(--text-muted);">
            <li><strong>Customer Refund Wizard:</strong> Multi-step step-by-step submission with instant visual outcome cards.</li>
            <li><strong>Support Lead Dashboard:</strong> Sortable, filterable table with composite risk badges.</li>
            <li><strong>Slide-Over Drawer:</strong> Inspection drawer for customer order history and supervisor overrides.</li>
            <li><strong>Admin AI Settings:</strong> Dynamic model switching, temperature tuning, and test connection probes.</li>
          </ul>
        </div>
      </div>

      <div class="callout" style="margin-top: 1.5rem;">
        <strong>Zero Touch Docker Orchestration:</strong> A single command (<code>docker compose up --build</code>) starts PostgreSQL 16, runs Alembic migrations, verifies seed records, launches the Uvicorn application server, and initializes the Nginx reverse proxy using container healthchecks.
      </div>
    </section>

    <!-- Chapter 2: Interactive Database Diagram -->
    <section id="database">
      <div class="section-header">
        <h2>2. Relational Data Model &amp; Interactive Schema</h2>
        <p>Interactive schema visualization. Click any table to inspect column types, primary keys, and foreign key dependencies.</p>
      </div>

      <div class="diagram-container">
        <div class="diagram-toolbar">
          <div class="diagram-filters">
            <button class="btn active" onclick="filterSchema('all', this)">All Tables (10)</button>
            <button class="btn" onclick="filterSchema('commerce', this)">Core E-Commerce</button>
            <button class="btn" onclick="filterSchema('refunds', this)">Refund Lifecycle</button>
            <button class="btn" onclick="filterSchema('auth', this)">Auth &amp; Admin</button>
            <button class="btn" onclick="filterSchema('security', this)">Security &amp; LLM</button>
          </div>
          <div class="diagram-controls">
            <button class="btn" onclick="zoomIn()">Zoom In (+)</button>
            <button class="btn" onclick="zoomOut()">Zoom Out (-)</button>
            <button class="btn" onclick="resetZoom()">Reset</button>
          </div>
        </div>

        <div class="diagram-canvas-wrap" id="canvas-wrapper">
          <svg id="erd-svg" viewBox="0 0 960 1180">
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 8 5 L 0 9 z" fill="#475569" />
              </marker>
              <marker id="arrow-active" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 8 5 L 0 9 z" fill="#38bdf8" />
              </marker>
            </defs>

            <!-- Connector Lines -->
            <g id="rel-lines-group">
              <!-- Dynamically populated -->
            </g>

            <!-- Table Nodes -->
            <g id="table-nodes-group">
              <!-- Dynamically populated -->
            </g>
          </svg>

          <!-- Schema Inspector Card -->
          <div class="inspector-card" id="inspector">
            <div class="inspector-header">
              <span class="inspector-title" id="insp-name">table_name</span>
              <button class="inspector-close" onclick="closeInspector()">&times;</button>
            </div>
            <div class="inspector-desc" id="insp-desc">Table description goes here.</div>
            <ul class="col-list" id="insp-cols">
              <!-- Columns inserted via JS -->
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- Chapter 3: Policy Engine & AI -->
    <section id="policy-engine">
      <div class="section-header">
        <h2>3. Two-Phase Decision Pipeline &amp; Guardrails</h2>
        <p>How the system combines deterministic policy guardrails with multi-provider AI reasoning.</p>
      </div>

      <div class="grid-3">
        <div class="card">
          <div class="card-title">Phase 1: Deterministic Rules</div>
          <p>
            Evaluates strict business boundaries before invoking AI models:
          </p>
          <ul style="margin: 0.5rem 0 0 1.25rem; font-size: 0.9rem; color: var(--text-muted);">
            <li><strong>Delivery Date:</strong> Orders not delivered cannot be refunded.</li>
            <li><strong>Window Expiration:</strong> Orders delivered &gt; 90 days ago denied immediately.</li>
            <li><strong>Clearance Items:</strong> Items marked <code>is_final_sale</code> denied automatically.</li>
            <li><strong>Auto-Approval:</strong> Clean claims under $100 approved with zero latency.</li>
          </ul>
        </div>

        <div class="card">
          <div class="card-title">Phase 2: AI Reasoning</div>
          <p>
            Eligible claims pass to the AI decision engine:
          </p>
          <ul style="margin: 0.5rem 0 0 1.25rem; font-size: 0.9rem; color: var(--text-muted);">
            <li><strong>Context Assembly:</strong> Injects policy rules, customer risk profile, and order metadata.</li>
            <li><strong>Structured Output:</strong> LiteLLM forces JSON schema returning decision, reasoning, and confidence.</li>
            <li><strong>Model Agnostic:</strong> Compatible with OpenAI gpt-4o-mini, local Ollama, or Gemini.</li>
          </ul>
        </div>

        <div class="card">
          <div class="card-title">Post-Evaluation Guardrails</div>
          <p>
            Prevents model hallucinations or adversarial prompt overrides:
          </p>
          <ul style="margin: 0.5rem 0 0 1.25rem; font-size: 0.9rem; color: var(--text-muted);">
            <li><strong>Hard Rule Re-Check:</strong> Verifies AI approval against non-negotiable policy terms.</li>
            <li><strong>Forced Override:</strong> Overrides illegal AI approvals to <code>denied</code>.</li>
            <li><strong>Security Telemetry:</strong> Logs <code>policy_guardrail_breach_prevented</code> in security audit log.</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Chapter 4: Security & Hardening -->
    <section id="security">
      <div class="section-header">
        <h2>4. Security Hardening &amp; Anomaly Detection</h2>
        <p>Defensive perimeter shielding the system from automated abuse and adversarial attacks.</p>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-title">Prompt Injection &amp; Input Sanitization</div>
          <p>
            Incoming customer text passes through multi-layer regex sanitization before LLM prompt injection:
          </p>
          <pre><code># Multi-pattern regex defense
INJECTION_PATTERNS = [
    r"(?i)ignore\\s+(all\\s+)?(previous|prior)\\s+instructions",
    r"(?i)system\\s*prompt",
    r"(?i)you\\s+are\\s+now\\s+(a|an)",
    r"(?i)assistant\\s*:",
    r"(?i)<\\s*script[^>]*>"
]</code></pre>
          <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.5rem;">
            Matches neutralize jailbreak attempts, sanitize raw text, and persist incident logs with client IP addresses.
          </p>
        </div>

        <div class="card">
          <div class="card-title">Sliding-Window Anomaly Scoring</div>
          <p>
            Real time relational queries detect fraud rings and abusive return velocities:
          </p>
          <ul style="margin: 0.75rem 0 0 1.25rem; color: var(--text-muted); font-size: 0.9rem;">
            <li><strong>Velocity Spikes:</strong> &ge; 3 claims in 24 hours tags <code>velocity_limit_exceeded</code>.</li>
            <li><strong>High-Value Clusters:</strong> Claim &gt; $200 or 7-day cumulative total &gt; $500 tags <code>high_value_cluster</code>.</li>
            <li><strong>Duplicate Claims:</strong> Re-submitting on the same item within 30 days tags <code>conflicting_claim_detected</code>.</li>
            <li><strong>Outage Resilience:</strong> Provider network failure persists claim as <code>escalated</code> with error context for human review.</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Chapter 5: Visual Walkthrough -->
    <section id="walkthrough">
      <div class="section-header">
        <h2>5. Visual End-to-End Walkthrough</h2>
        <p>Live user interface states captured across customer and administrative surfaces.</p>
      </div>

      <!-- Screenshot 1 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">1. Customer Refund Portal — Identity Verification</span>
          <span class="tag primary">Customer Flow</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/01_customer_portal.png" alt="Customer Portal Identity Lookup">
        </div>
        <div class="screenshot-footer">
          Customers initiate claims by entering their verified purchase email. The backend performs customer lookups, retrieves historical purchase volumes, and validates return eligibility.
        </div>
      </div>

      <!-- Screenshot 2 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">2. Order and Item Selection Wizard</span>
          <span class="tag primary">Customer Flow</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/02_order_selection.png" alt="Order and Item Selection">
        </div>
        <div class="screenshot-footer">
          Displays past purchase orders, delivery statuses, product photos, line items, and final sale badges. Customers select individual items and describe return reasons.
        </div>
      </div>

      <!-- Screenshot 3 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">3. Instant AI Verdict and Decision Card</span>
          <span class="tag success">Decision Engine</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/03_ai_decision_verdict.png" alt="AI Decision Result Card">
        </div>
        <div class="screenshot-footer">
          Immediate, customer-friendly outcome card showing the verified status (Approved), refund dollar amount ($45.00), policy breakdown checks, and timestamped audit record.
        </div>
      </div>

      <!-- Screenshot 4 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">4. Administrative Login with HTTP-Only JWT Protection</span>
          <span class="tag">Security</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/04_admin_login.png" alt="Admin Authentication">
        </div>
        <div class="screenshot-footer">
          Role-protected authentication portal. Sets secure HTTP-only cookies and prevents XSS token theft via strict refresh token rotation.
        </div>
      </div>

      <!-- Screenshot 5 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">5. Support Lead Operations Dashboard</span>
          <span class="tag primary">Admin Operations</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/05_admin_dashboard.png" alt="Admin Operations Dashboard">
        </div>
        <div class="screenshot-footer">
          Operational triage view displaying refund queue metrics, anomaly tags, risk ratings (e.g. 0.85 High Risk), and instant customer filter search.
        </div>
      </div>

      <!-- Screenshot 6 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">6. Slide-Over Detail Drawer &amp; Manual Override</span>
          <span class="tag primary">Admin Operations</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/06_admin_refund_detail.png" alt="Refund Detail Inspection Drawer">
        </div>
        <div class="screenshot-footer">
          Full claim investigation drawer showing customer risk metrics, AI reasoning trace, policy checklists, and supervisor override buttons (Force Approve / Deny).
        </div>
      </div>

      <!-- Screenshot 7 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">7. Multi-Provider LLM Runtime Settings</span>
          <span class="tag success">AI Orchestration</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/07_admin_llm_settings.png" alt="Admin LLM Settings">
        </div>
        <div class="screenshot-footer">
          Administrators can activate, configure, and probe live model endpoints (Ollama, OpenAI, Gemini) dynamically without rebuilding or restarting containers.
        </div>
      </div>

      <!-- Screenshot 8 -->
      <div class="screenshot-card">
        <div class="screenshot-header">
          <span class="screenshot-caption">8. Adversarial Prompt Injection Defense</span>
          <span class="tag">Security</span>
        </div>
        <div class="screenshot-img-wrap">
          <img src="docs/assets/screenshots/08_security_prompt_injection.png" alt="Prompt Injection Security Defense">
        </div>
        <div class="screenshot-footer">
          Demonstrates adversarial jailbreak interception. The system sanitizes malicious delimiters, flags security logs, and returns a neutral, policy-bound decision.
        </div>
      </div>
    </section>

    <!-- Chapter 6: Testing & Verification -->
    <section id="testing">
      <div class="section-header">
        <h2>6. Verification and Automated Testing Strategy</h2>
        <p>194 comprehensive automated unit, integration, and UI tests.</p>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-title">Backend Pytest Suite (112 Tests)</div>
          <p>
            Executes full-stack integration and unit tests against live PostgreSQL:
          </p>
          <pre><code># Run pytest inside Docker
docker compose exec backend pytest

# Results:
# 112 passed, 8 warnings in 44.28s</code></pre>
          <ul style="margin: 0.5rem 0 0 1.25rem; font-size: 0.85rem; color: var(--text-muted);">
            <li><strong>test_admin_api.py:</strong> Queue filters, stats, decision overrides.</li>
            <li><strong>test_ai_engine.py:</strong> LiteLLM parsing, retries, and schema validation.</li>
            <li><strong>test_auth_api.py:</strong> Token rotation, replay detection, revocation.</li>
            <li><strong>test_policy_service.py:</strong> Window checks, category exclusions, limits.</li>
            <li><strong>test_security_validation.py:</strong> Injection sanitizer, boundary tests.</li>
            <li><strong>test_security_hardening.py:</strong> Velocity limits, outage fallbacks.</li>
          </ul>
        </div>

        <div class="card">
          <div class="card-title">Frontend Vitest Suite (82 Tests)</div>
          <p>
            Tests UI component contracts, user state interactions, and API mocks:
          </p>
          <pre><code># Run Vitest suite
cd frontend && npm test -- --run

# Results:
# 12 test files passed, 82 passed in 953ms</code></pre>
          <ul style="margin: 0.5rem 0 0 1.25rem; font-size: 0.85rem; color: var(--text-muted);">
            <li><strong>RefundRequest.test.tsx:</strong> Form wizard steps, order loading, submission.</li>
            <li><strong>AdminDashboard.test.tsx:</strong> Risk indicators, search filters, drawers.</li>
            <li><strong>AdminSettings.test.tsx:</strong> Provider switching, probe testing.</li>
            <li><strong>AdminRoute.test.tsx:</strong> Protected route redirects on 401.</li>
            <li><strong>components.test.tsx:</strong> Design system buttons, dialogs, cards, alerts.</li>
          </ul>
        </div>
      </div>
    </section>

  </div>

  <footer>
    <p>AI Customer Support Refund System &bull; Technical Review &amp; Architecture Specification</p>
    <p style="margin-top: 0.25rem; color: #64748b;">Built with FastAPI, React 18, PostgreSQL 16, and LiteLLM.</p>
  </footer>

  <script>
    const schemaData = {schema_json};
    const relationships = {rel_json};

    let zoom = 1;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;

    const svg = document.getElementById('erd-svg');
    const nodesGroup = document.getElementById('table-nodes-group');
    const linesGroup = document.getElementById('rel-lines-group');
    const wrapper = document.getElementById('canvas-wrapper');
    const inspector = document.getElementById('inspector');

    function renderDiagram(filter = 'all') {{
      nodesGroup.innerHTML = '';
      linesGroup.innerHTML = '';

      // Draw Lines
      relationships.forEach((rel, idx) => {{
        const fromTable = schemaData.find(t => t.id === rel.from);
        const toTable = schemaData.find(t => t.id === rel.to);

        if (filter !== 'all') {{
          if (fromTable.category !== filter && toTable.category !== filter) return;
        }}

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', rel.coords);
        path.setAttribute('class', 'rel-line');
        path.setAttribute('id', `rel-${{idx}}`);
        path.setAttribute('data-from', rel.from);
        path.setAttribute('data-to', rel.to);
        path.setAttribute('marker-end', 'url(#arrow)');
        linesGroup.appendChild(path);
      }});

      // Draw Nodes
      schemaData.forEach(table => {{
        if (filter !== 'all' && table.category !== filter) return;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'table-node');
        g.setAttribute('transform', `translate(${{table.x}}, ${{table.y}})`);
        g.setAttribute('onclick', `inspectTable('${{table.id}}')`);

        // Node Container Rect
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('width', table.width);
        bg.setAttribute('height', table.height);
        bg.setAttribute('rx', '8');
        bg.setAttribute('class', 'node-body');
        g.appendChild(bg);

        // Header Rect
        const header = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        header.setAttribute('width', table.width);
        header.setAttribute('height', '32');
        header.setAttribute('rx', '8');
        header.setAttribute('class', `node-header ${{table.category}}`);
        g.appendChild(header);

        // Title Text
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        title.setAttribute('x', '12');
        title.setAttribute('y', '21');
        title.setAttribute('class', 'node-title');
        title.textContent = table.name;
        g.appendChild(title);

        // Render Columns
        const maxCols = 8;
        table.columns.slice(0, maxCols).forEach((col, cIdx) => {{
          const yPos = 52 + (cIdx * 20);

          const colText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          colText.setAttribute('x', '12');
          colText.setAttribute('y', yPos);
          colText.setAttribute('class', 'col-text');

          if (col.pk) {{
            colText.innerHTML = `<tspan class="col-pk">PK </tspan>${{col.name}}`;
          }} else if (col.fk) {{
            colText.innerHTML = `<tspan class="col-fk">FK </tspan>${{col.name}}`;
          }} else {{
            colText.textContent = col.name;
          }}
          g.appendChild(colText);

          // Type Text
          const typeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          typeText.setAttribute('x', table.width - 12);
          typeText.setAttribute('y', yPos);
          typeText.setAttribute('text-anchor', 'end');
          typeText.setAttribute('class', 'col-type');
          typeText.textContent = col.type.split('(')[0];
          g.appendChild(typeText);
        }});

        if (table.columns.length > maxCols) {{
          const moreText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          moreText.setAttribute('x', '12');
          moreText.setAttribute('y', 52 + (maxCols * 20));
          moreText.setAttribute('class', 'col-type');
          moreText.textContent = `+ ${{table.columns.length - maxCols}} more attributes...`;
          g.appendChild(moreText);
        }}

        nodesGroup.appendChild(g);
      }});
    }}

    function inspectTable(tableId) {{
      const table = schemaData.find(t => t.id === tableId);
      if (!table) return;

      document.getElementById('insp-name').textContent = table.name;
      document.getElementById('insp-desc').textContent = table.description;

      const colsList = document.getElementById('insp-cols');
      colsList.innerHTML = '';

      table.columns.forEach(col => {{
        const li = document.createElement('li');
        li.className = 'col-item';

        let badge = '';
        if (col.pk) badge = '<span style="color:#fbbf24;font-weight:700;">[PK]</span> ';
        if (col.fk) badge = `<span style="color:#38bdf8;font-weight:600;">[FK &rarr; ${{col.fk}}]</span> `;

        li.innerHTML = `<span>${{badge}}${{col.name}}</span><span style="color:#94a3b8;">${{col.type}}</span>`;
        colsList.appendChild(li);
      }});

      inspector.style.display = 'flex';

      // Highlight connections
      document.querySelectorAll('.rel-line').forEach(line => {{
        if (line.getAttribute('data-from') === tableId || line.getAttribute('data-to') === tableId) {{
          line.classList.add('highlight');
          line.setAttribute('marker-end', 'url(#arrow-active)');
        }} else {{
          line.classList.remove('highlight');
          line.setAttribute('marker-end', 'url(#arrow)');
        }}
      }});
    }}

    function closeInspector() {{
      inspector.style.display = 'none';
      document.querySelectorAll('.rel-line').forEach(line => {{
        line.classList.remove('highlight');
        line.setAttribute('marker-end', 'url(#arrow)');
      }});
    }}

    function filterSchema(category, btn) {{
      document.querySelectorAll('.diagram-filters .btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderDiagram(category);
      closeInspector();
    }}

    function updateTransform() {{
      nodesGroup.setAttribute('transform', `translate(${{panX}}, ${{panY}}) scale(${{zoom}})`);
      linesGroup.setAttribute('transform', `translate(${{panX}}, ${{panY}}) scale(${{zoom}})`);
    }}

    function zoomIn() {{
      zoom = Math.min(zoom * 1.2, 2.5);
      updateTransform();
    }}

    function zoomOut() {{
      zoom = Math.max(zoom * 0.8, 0.4);
      updateTransform();
    }}

    function resetZoom() {{
      zoom = 1;
      panX = 0;
      panY = 0;
      updateTransform();
    }}

    // Panning Event Listeners
    wrapper.addEventListener('mousedown', (e) => {{
      if (e.target.closest('#inspector') || e.target.closest('button')) return;
      isDragging = true;
      startX = e.clientX - panX;
      startY = e.clientY - panY;
    }});

    window.addEventListener('mousemove', (e) => {{
      if (!isDragging) return;
      panX = e.clientX - startX;
      panY = e.clientY - startY;
      updateTransform();
    }});

    window.addEventListener('mouseup', () => {{
      isDragging = false;
    }});

    // Wheel Zoom
    wrapper.addEventListener('wheel', (e) => {{
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      zoom = Math.min(Math.max(zoom * zoomFactor, 0.4), 2.5);
      updateTransform();
    }}, {{ passive: false }});

    // Initial Render
    renderDiagram();
  </script>
</body>
</html>
"""
    return html


def main():
    out_path = Path("review.html")
    html_content = generate_html()
    out_path.write_text(html_content, encoding="utf-8")
    print(f"Generated {out_path} ({len(html_content)} bytes)")


if __name__ == "__main__":
    main()
