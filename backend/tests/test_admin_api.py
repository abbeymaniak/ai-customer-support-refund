"""Tests for administrative refund management, reporting metrics, and supervisor overrides."""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.refund_request import RefundRequest


@pytest.mark.asyncio
async def test_list_refunds_endpoint(async_client):
    """Test AC-1: List refunds endpoint returns paginated response envelope."""
    response = await async_client.get("/api/admin/refunds")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1
    assert data["limit"] == 20
    assert data["offset"] == 0

    first = data["items"][0]
    assert "id" in first
    assert "request_number" in first
    assert "customer_name" in first
    assert "amount" in first
    assert "decision" in first


@pytest.mark.asyncio
async def test_list_refunds_filtering_by_decision(async_client, db_session):
    """Test AC-1: Filtering by decision status returns matched records."""
    # Query approved
    res_approved = await async_client.get("/api/admin/refunds?decision=Approved")
    assert res_approved.status_code == 200
    data_approved = res_approved.json()
    for item in data_approved["items"]:
        assert item["decision"].lower() == "approved"

    # Query all
    res_all = await async_client.get("/api/admin/refunds?decision=all")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total"] >= data_approved["total"]


@pytest.mark.asyncio
async def test_list_refunds_search(async_client):
    """Test AC-1: Keyword search across customer email, name, or order number."""
    response = await async_client.get("/api/admin/refunds?search=sarah")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert any("sarah" in (item["customer_email"] or "").lower() or "sarah" in (item["customer_name"] or "").lower() for item in data["items"])


@pytest.mark.asyncio
async def test_list_refunds_sorting_and_pagination(async_client):
    """Test AC-1: Sorting by amount and pagination with limit and offset."""
    res_asc = await async_client.get("/api/admin/refunds?sort_by=amount&sort_order=asc&limit=2&offset=0")
    assert res_asc.status_code == 200
    data_asc = res_asc.json()
    assert len(data_asc["items"]) <= 2

    res_desc = await async_client.get("/api/admin/refunds?sort_by=amount&sort_order=desc&limit=2&offset=0")
    assert res_desc.status_code == 200
    data_desc = res_desc.json()
    assert len(data_desc["items"]) <= 2


@pytest.mark.asyncio
async def test_list_refunds_date_filtering(async_client):
    """Test AC-1: Date boundary filtering with start_date and end_date."""
    now = datetime.utcnow()
    past_date = (now - timedelta(days=365)).isoformat()
    future_date = (now + timedelta(days=1)).isoformat()

    response = await async_client.get(f"/api/admin/refunds?start_date={past_date}&end_date={future_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_refund_stats(async_client):
    """Test AC-2: Executive KPI metrics endpoint returns operational aggregations."""
    response = await async_client.get("/api/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "approved_count" in data
    assert "denied_count" in data
    assert "escalated_count" in data
    assert "approval_rate" in data
    assert "human_overrides_count" in data
    assert "total_refunded_amount" in data
    assert data["total_requests"] >= 1
    assert isinstance(data["approval_rate"], (int, float))
    assert isinstance(data["total_refunded_amount"], (int, float))


@pytest.mark.asyncio
async def test_get_refund_detail_success(async_client):
    """Test AC-3: Retrieve full claim detail with customer profile and audit history."""
    seeded_id = "21111111-1111-1111-1111-111111111101"
    response = await async_client.get(f"/api/admin/refunds/{seeded_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == seeded_id
    assert data["request_number"] == "REF-2026-0001"
    assert data["customer"] is not None
    assert data["customer"]["email"] == "sarah.jenkins@example.com"
    assert "risk_score" in data["customer"]
    assert data["order"] is not None
    assert len(data["audit_logs"]) >= 1


@pytest.mark.asyncio
async def test_get_refund_detail_not_found(async_client):
    """Test AC-3: Claim not found returns HTTP 404."""
    random_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/admin/refunds/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_override_decision_validation(async_client):
    """Test AC-4: Reason is mandatory and must have minimum length of 5 characters."""
    seeded_id = "21111111-1111-1111-1111-111111111101"

    # Too short reason
    payload = {
        "decision": "Denied",
        "reason": "bad",
        "actor": "lead@store.com",
    }
    response = await async_client.post(f"/api/admin/refunds/{seeded_id}/override", json=payload)
    assert response.status_code == 422

    # Whitespace only reason
    payload_whitespace = {
        "decision": "Denied",
        "reason": "     ",
        "actor": "lead@store.com",
    }
    response_ws = await async_client.post(f"/api/admin/refunds/{seeded_id}/override", json=payload_whitespace)
    assert response_ws.status_code == 422


@pytest.mark.asyncio
async def test_override_decision_success(async_client, db_session):
    """Test AC-4: Valid override updates claim decision, marks human_override, and logs audit."""
    # Create a fresh temporary refund request to override
    new_req = RefundRequest(
        id=uuid.uuid4(),
        request_number=f"REF-TEST-{uuid.uuid4().hex[:6].upper()}",
        customer_id=uuid.UUID("c1111111-1111-1111-1111-111111111111"),
        order_id=uuid.UUID("01111111-1111-1111-1111-111111111101"),
        amount=55.0,
        currency="USD",
        reason_category="defective",
        customer_explanation="Initial submission for override testing.",
        status="pending",
        decision="pending",
        human_override=False,
    )
    db_session.add(new_req)
    await db_session.commit()

    override_payload = {
        "decision": "Approved",
        "reason": "Supervisor courtesy approved due to high customer lifetime value.",
        "actor": "supervisor@store.com",
    }
    response = await async_client.post(f"/api/admin/refunds/{new_req.id}/override", json=override_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "Approved"
    assert data["status"] == "approved"
    assert data["human_override"] is True
    assert data["override_reason"] == override_payload["reason"]
    assert data["override_by"] == "supervisor@store.com"

    # Verify audit log in database
    audit_stmt = select(AuditLog).where(
        AuditLog.refund_request_id == new_req.id,
        AuditLog.action == "human_override",
    )
    audit_result = await db_session.execute(audit_stmt)
    audit_record = audit_result.scalar_one_or_none()
    assert audit_record is not None
    assert audit_record.actor == "supervisor@store.com"
    assert audit_record.details["new_decision"] == "Approved"
    assert audit_record.details["override_reason"] == override_payload["reason"]


@pytest.mark.asyncio
async def test_override_decision_not_found(async_client):
    """Test AC-4: Overriding a non-existent claim returns HTTP 404."""
    random_id = str(uuid.uuid4())
    payload = {
        "decision": "Denied",
        "reason": "Legitimate justification for non-existent claim.",
        "actor": "supervisor@store.com",
    }
    response = await async_client.post(f"/api/admin/refunds/{random_id}/override", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_logs_query(async_client):
    """Test querying audit logs endpoint."""
    response = await async_client.get("/api/admin/audit-logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    assert "action" in logs[0]
    assert "actor" in logs[0]
    assert "timestamp" in logs[0]
