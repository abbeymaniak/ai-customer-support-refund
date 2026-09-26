import uuid

import pytest


@pytest.mark.asyncio
async def test_process_refund_final_sale_denial(async_client, db_session):
    """Test AC-4: Final sale item must be immediately Denied with RULE_FINAL_SALE."""
    from sqlalchemy import delete

    from app.models.refund_request import RefundRequest

    # Clean up prior test runs for this item
    await db_session.execute(
        delete(RefundRequest).where(RefundRequest.item_id == "18888888-8888-8888-8888-888888888801")
    )
    await db_session.commit()

    payload = {
        "customer_email": "amanda.price@example.com",
        "order_number": "ORD-2026-9040",
        "item_id": "18888888-8888-8888-8888-888888888801",
        "amount": 65.0,
        "reason_category": "unwanted",
        "customer_explanation": "Customer changed mind on clearance item.",
        "quantity": 1,
        "item_condition": "unopened",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["decision"] == "Denied"
    assert data["status"] == "denied"
    assert data["confidence_score"] == 1.0
    assert "final sale" in data["decision_reason"].lower()
    assert "RULE_FINAL_SALE" in data["policy_checks"]["matched_rules"]


@pytest.mark.asyncio
async def test_process_refund_duplicate_claim_conflict(async_client):
    """Test duplicate claim detection tags conflicting_claim_detected and escalates (AC-4)."""
    # First item of order ORD-2026-9001 was already refunded in seed.sql
    payload = {
        "customer_email": "sarah.jenkins@example.com",
        "order_number": "ORD-2026-9001",
        "item_id": "11111111-1111-1111-1111-111111111101",
        "amount": 45.0,
        "reason_category": "defective",
        "customer_explanation": "Attempting duplicate refund claim.",
        "quantity": 1,
        "item_condition": "opened_used",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["decision"] == "Escalated"
    assert "conflicting_claim_detected" in data["anomaly_flags"]
    assert data["risk_score"] >= 0.3


@pytest.mark.asyncio
async def test_process_refund_order_not_found(async_client):
    """Test 404 when order number does not exist."""
    payload = {
        "customer_email": "sarah.jenkins@example.com",
        "order_number": "ORD-NONEXISTENT",
        "item_id": str(uuid.uuid4()),
        "amount": 50.0,
        "reason_category": "defective",
        "customer_explanation": "Sample explanation",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_refund_detail_not_found(async_client):
    """Test 404 when querying an unknown refund ID."""
    unknown_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/refunds/{unknown_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_process_refund_high_value_escalation_and_audit_trail(async_client, db_session):
    """Test AC-4, AC-5: High-value refund (> $500) escalates to human review and records audit log."""
    from sqlalchemy import delete, select

    from app.models.audit_log import AuditLog
    from app.models.refund_request import RefundRequest

    item_id = "1bbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01"
    # Clean up prior test runs for this item
    await db_session.execute(delete(RefundRequest).where(RefundRequest.item_id == item_id))
    await db_session.commit()

    payload = {
        "customer_email": "james.wilson@example.com",
        "order_number": "ORD-2026-8990",
        "item_id": item_id,
        "amount": 650.0,
        "reason_category": "defective",
        "customer_explanation": "Coffee grinder does not spin",
        "quantity": 1,
        "item_condition": "opened_used",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["decision"] == "Escalated"
    assert data["status"] == "escalated"
    assert data["confidence_score"] == 0.5
    assert "RULE_HIGH_VALUE_ESCALATION" in data["policy_checks"]["matched_rules"]
    assert data["request_number"].startswith("REF-")
    assert "llm_audit_data" in data and bool(data["llm_audit_data"])

    # Verify audit log was recorded in PostgreSQL (covers: AC-5)
    refund_id = uuid.UUID(data["id"])
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.refund_request_id == refund_id)
    )
    audit_entry = result.scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.action == "refund_evaluated"
    assert audit_entry.actor == "system"

    # Verify GET /api/refunds/{id} endpoint retrieves full detail (covers: AC-5, AC-6)
    get_res = await async_client.get(f"/api/refunds/{data['id']}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == data["id"]
    assert detail["request_number"] == data["request_number"]
    assert len(detail["refund_items"]) == 1
    assert detail["refund_items"][0]["order_item_id"] == item_id
