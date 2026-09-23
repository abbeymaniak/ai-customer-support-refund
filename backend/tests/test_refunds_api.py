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
    """Test duplicate claim prevention returns HTTP 409 Conflict."""
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
    assert response.status_code == 409
    assert "already been submitted" in response.json()["detail"].lower()


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
