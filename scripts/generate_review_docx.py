#!/usr/bin/env python3
"""Generator script for review.docx deliverable.

Generates an executive-grade Word document explaining the AI Customer Support
Refund System architecture, decisions, security models, and database design
with embedded screenshots and formatted tables.
"""

from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

SCREENSHOTS_DIR = Path("docs/assets/screenshots")
OUTPUT_PATH = Path("review.docx")


def set_cell_shading(cell, color_hex: str):
    """Set background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f"<w:tcMar {nsdecls('w')}>"
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tcPr.append(tcMar)


def add_callout(doc, text: str, title: str = "KEY ARCHITECTURAL HIGHLIGHT"):
    """Add a styled callout box to document."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_shading(cell, "F0F9FF")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    # Left border styling in XML
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f"<w:tcBorders {nsdecls('w')}>"
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f"</w:tcBorders>"
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run_title = p.add_run(f"{title}: ")
    run_title.bold = True
    run_title.font.name = "Arial"
    run_title.font.size = Pt(9.5)
    run_title.font.color.rgb = RGBColor(2, 132, 199)

    run_text = p.add_run(text)
    run_text.font.name = "Arial"
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build_docx():
    doc = docx.Document()

    # Configure Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Title & Metadata
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(4)
    title_run = title_p.add_run("AI Customer Support Refund System")
    title_run.bold = True
    title_run.font.name = "Arial"
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(16)
    sub_run = sub_p.add_run("Technical Architecture Review & Engineering Specification")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(14)
    sub_run.font.color.rgb = RGBColor(71, 85, 105)

    meta_table = doc.add_table(rows=2, cols=4)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_headers = ["Stack", "Database", "AI Gateway", "Testing Suite"]
    meta_values = [
        "FastAPI + React 18",
        "PostgreSQL 16",
        "LiteLLM Multi-Provider",
        "194 Tests (112 Pytest + 82 Vitest)",
    ]

    for col_idx, text in enumerate(meta_headers):
        c = meta_table.cell(0, col_idx)
        c.text = text
        set_cell_shading(c, "0F172A")
        p = c.paragraphs[0]
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    for col_idx, text in enumerate(meta_values):
        c = meta_table.cell(1, col_idx)
        c.text = text
        set_cell_shading(c, "F8FAFC")
        p = c.paragraphs[0]
        p.runs[0].font.size = Pt(8.5)
        p.runs[0].font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # 1. Executive Summary
    h1 = doc.add_heading("1. Executive Summary & Problem Space", level=1)
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "Modern e-commerce platforms process thousands of customer refund claims weekly. Traditional approaches "
        "rely either on rigid hard-coded rules that fail to interpret qualitative return justifications or manual human "
        "triage that causes customer friction and high operational overhead. Conversely, naive LLM integrations introduce "
        "significant risk: prompt injection attacks, policy hallucinations, and non-deterministic financial disbursements."
    )
    doc.add_paragraph(
        "The AI Customer Support Refund System resolves this dilemma by pairing a two-phase policy engine with "
        "strict post-evaluation deterministic guardrails, sliding-window anomaly detection, and cryptographic audit logging. "
        "The application evaluates customer claims against store policy, calculates fraud risk metrics, and produces "
        "defensible verdicts: Approved, Denied, or Escalated for human supervisor review."
    )

    add_callout(
        doc,
        "The system achieves sub-second decision latency on clean claims while guaranteeing that non-negotiable rules "
        "(such as final sale exclusions and expired 90-day return windows) cannot be bypassed by adversarial prompt injection "
        "or AI hallucinations.",
        "CORE VALUE PROPOSITION",
    )

    # 2. System Architecture
    h2 = doc.add_heading("2. Full-Stack System Architecture", level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "The platform is organized into clean architectural layers adhering to Clean Architecture principles:"
    )

    arch_bullets = [
        (
            "Presentation Layer (React 18 + Vite + Tailwind CSS v4)",
            "Single Page Application delivering the customer refund wizard, administrative triage dashboard, slide-over detail drawers, and runtime LLM provider settings.",
        ),
        (
            "Gateway & Reverse Proxy (Nginx)",
            "Nginx Alpine container listening on port 3000, serving static web assets and proxying /api/ and /health endpoints to the FastAPI application server.",
        ),
        (
            "Service & Domain Layer (FastAPI + Pydantic v2)",
            "Asynchronous Python backend implementing Clean Architecture. Presentation routes validate DTO schemas and call domain services without raw SQL.",
        ),
        (
            "Persistence Layer (SQLAlchemy 2.0 + PostgreSQL 16)",
            "Fully normalized relational database utilizing JSONB columns for immutable policy snapshots, anomaly telemetry, and audit event logs.",
        ),
        (
            "AI Decision Gateway (LiteLLM)",
            "Unified multi-provider abstraction supporting runtime model switching between OpenAI (gpt-4o-mini), local Ollama (llama3), and Google Gemini (gemini-1.5-flash).",
        ),
    ]

    for title, desc in arch_bullets:
        p = doc.add_paragraph(style="List Bullet")
        r_title = p.add_run(f"{title}: ")
        r_title.bold = True
        p.add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 3. Relational Data Model
    h3 = doc.add_heading("3. Relational Database Schema & Entities", level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "The PostgreSQL 16 database consists of 10 normalized tables. The schema enforces foreign key integrity, "
        "B-tree index optimization on lookups, and JSONB structures for telemetry:"
    )

    tables_info = [
        (
            "customers",
            "Core E-Commerce",
            "id (PK), email (UQ), name, total_spent, orders_count, refunds_count, return_rate, risk_score, account_created_at",
        ),
        (
            "orders",
            "Core E-Commerce",
            "id (PK), customer_id (FK), order_number (UQ), order_date, delivery_date, total_amount, currency, status, items, shipping_address",
        ),
        (
            "order_items",
            "Core E-Commerce",
            "id (PK), order_id (FK), product_id, product_name, category, price, quantity, is_final_sale, serial_number, warranty_status",
        ),
        (
            "refund_requests",
            "Refund Lifecycle",
            "id (PK), customer_id (FK), order_id (FK), status, decision_reason, confidence, refund_amount, policy_checks, risk_score, anomaly_flags, error_context",
        ),
        (
            "refund_items",
            "Refund Lifecycle",
            "id (PK), refund_request_id (FK), order_item_id (FK), reason, item_condition, requested_amount, approved_amount",
        ),
        (
            "audit_logs",
            "Audit & Traceability",
            "id (PK), refund_request_id (FK), actor, action, previous_status, new_status, reason, metadata_snapshot, timestamp",
        ),
        (
            "admin_users",
            "Security & Auth",
            "id (PK), email (UQ), password_hash (Bcrypt), name, role, is_active, last_login_at",
        ),
        (
            "refresh_tokens",
            "Security & Auth",
            "id (PK), user_id (FK), token_hash (SHA-256), expires_at, revoked, created_at",
        ),
        (
            "llm_providers",
            "AI Configuration",
            "id (PK), llm (UQ), is_active, llm_model, api_key, api_base, temperature, timeout_seconds, updated_by",
        ),
        (
            "security_logs",
            "Security & Telemetry",
            "id (PK), event_type, customer_id (FK), refund_request_id (FK), severity, details, client_ip, created_at",
        ),
    ]

    schema_table = doc.add_table(rows=len(tables_info) + 1, cols=3)
    schema_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    schema_headers = ["Table Name", "Domain Category", "Key Columns & Constraints"]

    for col_idx, h_text in enumerate(schema_headers):
        c = schema_table.cell(0, col_idx)
        c.text = h_text
        set_cell_shading(c, "1E293B")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.size = Pt(9)
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, (t_name, t_cat, t_cols) in enumerate(tables_info, start=1):
        c0 = schema_table.cell(row_idx, 0)
        c0.text = t_name
        c0.paragraphs[0].runs[0].bold = True
        c0.paragraphs[0].runs[0].font.name = "Consolas"
        c0.paragraphs[0].runs[0].font.size = Pt(8.5)

        c1 = schema_table.cell(row_idx, 1)
        c1.text = t_cat
        c1.paragraphs[0].runs[0].font.size = Pt(8.5)

        c2 = schema_table.cell(row_idx, 2)
        c2.text = t_cols
        c2.paragraphs[0].runs[0].font.name = "Consolas"
        c2.paragraphs[0].runs[0].font.size = Pt(8)

        shading = "FFFFFF" if row_idx % 2 == 1 else "F8FAFC"
        set_cell_shading(c0, shading)
        set_cell_shading(c1, shading)
        set_cell_shading(c2, shading)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 4. Two Phase Policy Engine
    h4 = doc.add_heading("4. Two-Phase Decision Pipeline & Safety Guardrails", level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "A critical vulnerability in generative AI applications is non-deterministic policy adherence. "
        "The refund engine implements a fail-safe pipeline dividing evaluation into deterministic pre-checks, "
        "contextual AI analysis, and deterministic post-evaluation guardrails:"
    )

    doc.add_paragraph(
        "1. Deterministic Rule Phase: Hard business rules are verified prior to invoking LLMs. Items flagged as final sale "
        "(is_final_sale=True), orders delivered beyond the 90-day absolute ceiling, or items with zero active delivery status "
        "are denied instantly. Clean claims under $100.00 with low customer risk scores are auto-approved immediately."
    )
    doc.add_paragraph(
        "2. Contextual AI Reasoning Phase: Eligible requests are dispatched to LiteLLM with structured Pydantic output schemas. "
        "The system prompt injects exact policy excerpts, customer return history, and item condition notes. The model returns "
        "a verified JSON payload containing decision (Approved, Denied, Escalated), confidence score, and bulleted reasoning."
    )
    doc.add_paragraph(
        "3. Post-Evaluation Guardrail Interceptor: If an AI provider returns an Approved verdict for an ineligible item "
        "(e.g., clearance merchandise), the post-evaluation guardrail intercepts the payload, forcibly overrides the status to Denied, "
        "records a policy_guardrail_breach_prevented event in security_logs, and updates audit records."
    )

    # 5. Security & Anomaly Detection
    h5 = doc.add_heading("5. Security Hardening & Anomaly Detection", level=1)
    h5.paragraph_format.space_before = Pt(16)
    h5.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "To mitigate automated abuse and fraud rings, the system incorporates comprehensive defensive layers:"
    )

    sec_items = [
        (
            "Adversarial Prompt Injection Sanitization",
            "Regular expression pattern matchers scan all free-text customer inputs for instruction override delimiters ('ignore all previous instructions', 'system prompt', '<script>'). Matched payloads are neutralized, logged with client IP, and prevented from reaching model context.",
        ),
        (
            "Velocity Limit Anomaly Detection",
            "Relational sliding-window queries calculate submission frequency. Customers filing 3 or more claims in a rolling 24-hour period are flagged with velocity_limit_exceeded and escalated to human supervisors.",
        ),
        (
            "High-Value Cluster Detection",
            "Claims with single item values over $200.00 or cumulative 7-day refund claims exceeding $500.00 are tagged with high_value_cluster and routed to support leads.",
        ),
        (
            "Conflicting Claim Prevention",
            "Submissions targeting order items with an active or approved claim filed within the previous 30 days trigger conflicting_claim_detected, preventing duplicate disbursements.",
        ),
        (
            "AI Service Outage Resilience",
            "When an external AI provider encounters network timeouts, rate limits, or HTTP 5xx failures, execution degrades gracefully. The claim is persisted as Escalated with error_context saved, returning an empathetic confirmation to the customer without server crashes.",
        ),
    ]

    for title, desc in sec_items:
        p = doc.add_paragraph(style="List Bullet")
        r_title = p.add_run(f"{title}: ")
        r_title.bold = True
        p.add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 6. Visual Walkthrough & Screenshots
    h6 = doc.add_heading("6. Visual End-to-End Walkthrough", level=1)
    h6.paragraph_format.space_before = Pt(16)
    h6.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "The following walkthrough presents live application states captured across the customer portal, "
        "administrative dashboard, and runtime configuration interfaces:"
    )

    walkthrough_steps = [
        (
            "01_customer_portal.png",
            "Figure 1: Customer Identity & Order Verification",
            "Customer initiates refund claim by entering their registered email address. The backend performs profile verification, retrieving purchase history, total spend, and account eligibility.",
        ),
        (
            "02_order_selection.png",
            "Figure 2: Multi-Step Order and Line Item Selection",
            "Displays customer purchase orders, line items, unit prices, delivery dates, and final sale badges. Customers select items and specify return reasons.",
        ),
        (
            "03_ai_decision_verdict.png",
            "Figure 3: Instant AI Evaluation Verdict Card",
            "Defensible decision outcome card displaying approved refund amount ($45.00), policy breakdown checks, AI confidence rating, and timestamped audit log ID.",
        ),
        (
            "04_admin_login.png",
            "Figure 4: Administrative Portal Authentication",
            "Role-protected login interface utilizing bcrypt hashed credentials and issuing secure HTTP-only cookies with JWT refresh token rotation.",
        ),
        (
            "05_admin_dashboard.png",
            "Figure 5: Support Lead Operations Dashboard",
            "Queue management view featuring real-time refund status filtering, customer risk badges (e.g. 0.85 High Risk), and anomaly alerts.",
        ),
        (
            "06_admin_refund_detail.png",
            "Figure 6: Slide-Over Inspection Drawer & Decision Override",
            "Detailed claim drawer exposing customer lifetime metrics, policy checklists, AI reasoning trace, and manual supervisor override controls.",
        ),
        (
            "07_admin_llm_settings.png",
            "Figure 7: Multi-Provider LLM Runtime Settings",
            "Administrative panel enabling dynamic switching between local Ollama (llama3), OpenAI, and Google Gemini with live endpoint test connection probes.",
        ),
        (
            "08_security_prompt_injection.png",
            "Figure 8: Adversarial Prompt Injection Defense",
            "Live defense against adversarial prompt injection. Malicious instructions are sanitized, logged to security telemetry, and returned with neutral policy enforcement.",
        ),
    ]

    for filename, caption, desc in walkthrough_steps:
        img_path = SCREENSHOTS_DIR / filename
        h_fig = doc.add_heading(caption, level=2)
        h_fig.paragraph_format.space_before = Pt(12)
        h_fig.paragraph_format.space_after = Pt(4)

        if img_path.exists():
            doc.add_picture(str(img_path), width=Inches(6.2))
            last_p = doc.paragraphs[-1]
            last_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            p_missing = doc.add_paragraph(
                f"[Screenshot {filename} not found at {img_path}]"
            )
            p_missing.runs[0].font.color.rgb = RGBColor(239, 68, 68)

        p_desc = doc.add_paragraph(desc)
        p_desc.paragraph_format.space_before = Pt(4)
        p_desc.paragraph_format.space_after = Pt(12)
        p_desc.runs[0].font.size = Pt(9.5)
        p_desc.runs[0].font.color.rgb = RGBColor(71, 85, 105)

    # 7. Testing & Verification
    h7 = doc.add_heading("7. Automated Testing Strategy & Reliability", level=1)
    h7.paragraph_format.space_before = Pt(16)
    h7.paragraph_format.space_after = Pt(6)

    doc.add_paragraph("Quality assurance is enforced across 194 automated test suites:")

    doc.add_paragraph(
        "Backend Pytest Suite (112 Tests Passed in 44.28s):\n"
        "- test_admin_api.py: Queue filtering, pagination, statistics, and manual overrides.\n"
        "- test_ai_engine.py: LiteLLM response parsing, mock retries, and fallback transitions.\n"
        "- test_auth_api.py: JWT cookie issuance, token refresh replay detection, and revocation.\n"
        "- test_policy_service.py: 30-day and 90-day return windows, auto-approval thresholds.\n"
        "- test_security_validation.py: Prompt injection sanitization and resource 404 boundaries.\n"
        "- test_security_hardening.py: Velocity scoring, high-value clusters, and conflicting claims."
    )

    doc.add_paragraph(
        "Frontend Vitest Suite (82 Tests Passed in 953ms):\n"
        "- RefundRequest.test.tsx: Form wizard steps, order loading, and outcome rendering.\n"
        "- AdminDashboard.test.tsx: Search filters, risk badges, and detail slide-over drawers.\n"
        "- AdminSettings.test.tsx: Provider selection, credential inputs, and test probes.\n"
        "- AdminRoute.test.tsx: Unauthenticated redirect handling and role authorization.\n"
        "- components.test.tsx: Design system primitives (buttons, modals, cards, badges)."
    )

    doc.save(str(OUTPUT_PATH))
    print(f"Generated {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    build_docx()
