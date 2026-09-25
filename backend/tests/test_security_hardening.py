"""Comprehensive test suite for Feature 11: Security & Edge Case Hardening (Spec 0011).

Covers:
- AC-1: Data model extensions for anomaly metrics
- AC-2: Velocity anomaly detection (>= 3 requests in 24 hours)
- AC-3: High value cluster detection (> $200 item or > $500 7-day sum)
- AC-4: Conflicting claim detection (duplicate item claim within 30 days)
- AC-5: AI service outage resilience and graceful fallback
- AC-6: Non-negotiable deterministic policy guardrail interceptor
- AC-7: Edge case resource validation (structured HTTP 404 responses)
- AC-8: Administrative anomaly and risk visibility
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.ai.engine import AIDecisionEngine, AIProviderError
from app.models.refund_request import RefundRequest
from app.models.security import SecurityLog
from app.services.anomaly_service import AnomalyService
from app.services.policy_service import PolicyService


@pytest.mark.asyncio
async def test_ac1_data_model_anomaly_fields(db_session):
    """Verify refund_requests table has risk_score, anomaly_flags, and error_context columns (AC-1)."""
    stmt = select(RefundRequest).limit(1)
    result = await db_session.execute(stmt)
    req = result.scalar_one_or_none()
    assert req is not None
    assert hasattr(req, "risk_score")
    assert hasattr(req, "anomaly_flags")
    assert hasattr(req, "error_context")
    assert isinstance(req.risk_score, float)
    assert isinstance(req.anomaly_flags, list)


@pytest.mark.asyncio
async def test_ac2_velocity_anomaly_detection(async_client, db_session):
    """Verify customer submitting 3 requests within 24 hours triggers velocity escalation (AC-2)."""
    # Customer David Miller (ORD-2026-9055, item 12222222-2222-2222-2222-222222222201)
    customer_email = "david.miller@example.com"
    order_number = "ORD-2026-9055"
    item_id = "12222222-2222-2222-2222-222222222201"

    from app.models.customer import Customer

    cust_res = (
        await db_session.execute(select(Customer).where(Customer.email == customer_email))
    ).scalar_one()

    from app.models.order import Order

    order_res = (
        await db_session.execute(select(Order).where(Order.order_number == order_number))
    ).scalar_one()

    from sqlalchemy import delete

    # Clean up any prior test records for David Miller to test exact velocity boundary
    await db_session.execute(delete(RefundRequest).where(RefundRequest.customer_id == cust_res.id))
    await db_session.commit()

    # Insert 2 prior requests in the past 2 hours
    for i in range(2):
        prior_req = RefundRequest(
            id=uuid.uuid4(),
            request_number=f"REF-VEL-{uuid.uuid4().hex[:8].upper()}",
            customer_id=cust_res.id,
            order_id=order_res.id,
            item_id=f"item-fake-{i}",
            item_name="Test Product",
            amount=25.0,
            total_refund_amount=25.0,
            currency="USD",
            reason_category="unwanted",
            customer_explanation="Prior test claim for velocity testing.",
            status="approved",
            decision="Approved",
            risk_score=0.0,
            anomaly_flags=[],
        )
        db_session.add(prior_req)
    await db_session.commit()

    # Third submission within 24 hours
    payload = {
        "customer_email": customer_email,
        "order_number": order_number,
        "item_id": item_id,
        "amount": 25.0,
        "reason_category": "unwanted",
        "customer_explanation": "Third submission testing velocity spike anomaly trigger.",
        "quantity": 1,
        "item_condition": "unopened",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["decision"] == "Escalated"
    assert "velocity_limit_exceeded" in data["anomaly_flags"]
    assert data["risk_score"] >= 0.4
    assert (
        "supervisor" in data["decision_reason"].lower()
        or "anomalies" in data["decision_reason"].lower()
    )

    # Check security log
    sec_stmt = select(SecurityLog).where(
        SecurityLog.event_type == "velocity_limit_exceeded",
        SecurityLog.customer_email == customer_email,
    )
    sec_log = (await db_session.execute(sec_stmt)).scalars().first()
    assert sec_log is not None
    assert sec_log.severity == "high"


@pytest.mark.asyncio
async def test_ac3_high_value_cluster_detection(async_client, db_session):
    """Verify claim with amount > $200 triggers high_value_cluster escalation (AC-3)."""
    # Active Noise Cancelling Earbuds: $210.00 in order ORD-2026-7840
    payload = {
        "customer_email": "sarah.jenkins@example.com",
        "order_number": "ORD-2026-7840",
        "item_id": "11111111-1111-1111-1111-111111111103",
        "amount": 210.0,
        "reason_category": "defective",
        "customer_explanation": "Right earbud produces loud static noise and buzz.",
        "quantity": 1,
        "item_condition": "opened_used",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["decision"] == "Escalated"
    assert "high_value_cluster" in data["anomaly_flags"]
    assert data["risk_score"] >= 0.3

    # Check security log
    sec_stmt = select(SecurityLog).where(
        SecurityLog.event_type == "high_value_cluster",
        SecurityLog.customer_email == "sarah.jenkins@example.com",
    )
    sec_log = (await db_session.execute(sec_stmt)).scalars().first()
    assert sec_log is not None


@pytest.mark.asyncio
async def test_ac4_conflicting_claim_detection(async_client, db_session):
    """Verify duplicate submission for same item within 30 days triggers conflicting_claim_detected (AC-4)."""
    # First item of order ORD-2026-9001 was already refunded in seed.sql
    payload = {
        "customer_email": "sarah.jenkins@example.com",
        "order_number": "ORD-2026-9001",
        "item_id": "11111111-1111-1111-1111-111111111101",
        "amount": 45.0,
        "reason_category": "defective",
        "customer_explanation": "Attempting duplicate refund claim on item.",
        "quantity": 1,
        "item_condition": "opened_used",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["decision"] == "Escalated"
    assert "conflicting_claim_detected" in data["anomaly_flags"]
    assert data["risk_score"] >= 0.3

    # Check security log
    sec_stmt = select(SecurityLog).where(
        SecurityLog.event_type == "conflicting_claim_detected",
        SecurityLog.order_number == "ORD-2026-9001",
    )
    sec_log = (await db_session.execute(sec_stmt)).scalars().first()
    assert sec_log is not None


@pytest.mark.asyncio
async def test_ac5_ai_service_outage_graceful_fallback(async_client, db_session):
    """Verify AI provider failure or timeout persists claim with status escalated and error_context (AC-5)."""
    # Customer Alex Rivera (ORD-2026-9304, item 16666666-6666-6666-6666-666666666601: Canvas Travel Backpack, $85.00)
    item_id = "16666666-6666-6666-6666-666666666601"
    item_uuid = uuid.UUID(item_id)

    from sqlalchemy import delete

    from app.models.refund_item import RefundItem

    # Clean up prior test requests for Alex Rivera to test pure AI outage fallback
    await db_session.execute(delete(RefundItem).where(RefundItem.order_item_id == item_uuid))
    await db_session.execute(delete(RefundRequest).where(RefundRequest.item_id == item_id))
    await db_session.commit()

    payload = {
        "customer_email": "alex.rivera@example.com",
        "order_number": "ORD-2026-9304",
        "item_id": item_id,
        "amount": 85.0,
        "reason_category": "defective",
        "customer_explanation": "Zipper mechanism separated after two days of light use.",
        "quantity": 1,
        "item_condition": "opened_used",
    }

    # Simulate AI engine raising an unexpected network timeout or provider outage
    with patch.object(
        AIDecisionEngine,
        "evaluate_refund_request",
        side_effect=AIProviderError("Upstream model connection timed out after 3000ms"),
    ):
        response = await async_client.post("/api/refunds/process", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert data["decision"] == "Escalated"
        assert data["status"] == "escalated"
        assert "temporarily unavailable" in data["decision_reason"].lower()
        assert data["error_context"] is not None
        assert "AIProviderError" in data["error_context"]["error_type"]
        assert "timed out" in data["error_context"]["message"]

        # Check security log
        sec_stmt = select(SecurityLog).where(
            SecurityLog.event_type == "ai_service_outage",
            SecurityLog.customer_email == "alex.rivera@example.com",
        )
        sec_log = (await db_session.execute(sec_stmt)).scalars().first()
        assert sec_log is not None


@pytest.mark.asyncio
async def test_ac6_deterministic_guardrail_override(async_client, db_session):
    """Verify AI approval of a final sale clearance item is forcibly overridden to Denied (AC-6)."""
    # Order ORD-2026-9040, item 18888888-8888-8888-8888-888888888801 is Clearance Winter Parka [Final Sale]
    payload = {
        "customer_email": "amanda.price@example.com",
        "order_number": "ORD-2026-9040",
        "item_id": "18888888-8888-8888-8888-888888888801",
        "amount": 65.0,
        "reason_category": "unwanted",
        "customer_explanation": "The sizing on this winter parka ran significantly smaller than described in the catalog.",
        "quantity": 1,
        "item_condition": "unopened",
    }

    # Mock AI decision engine returning rogue "Approved" recommendation
    rogue_ai_output = {
        "decision": "Approved",
        "confidence_score": 0.99,
        "explanation": "Customer was very polite, approving this clearance return.",
        "policy_citations": [],
        "matched_rules": [],
        "telemetry": {"provider": "mock-rogue"},
    }

    with patch.object(
        AIDecisionEngine,
        "evaluate_refund_request",
        new=AsyncMock(return_value=rogue_ai_output),
    ):
        response = await async_client.post("/api/refunds/process", json=payload)
        assert response.status_code == 201
        data = response.json()

        # Decision MUST be overridden to Denied per AC-6
        assert data["decision"] == "Denied"
        assert data["confidence_score"] == 1.0
        assert (
            "guardrail" in data["decision_reason"].lower()
            or "final sale" in data["decision_reason"].lower()
        )

        # Verify security log
        sec_stmt = select(SecurityLog).where(
            SecurityLog.event_type == "policy_guardrail_breach_prevented",
            SecurityLog.customer_email == "amanda.price@example.com",
        )
        sec_log = (await db_session.execute(sec_stmt)).scalars().first()
        assert sec_log is not None
        assert sec_log.severity == "high"


@pytest.mark.asyncio
async def test_ac7_resource_existence_404_validation(async_client):
    """Verify structured HTTP 404 responses for nonexistent customer, order, or mismatched item (AC-7)."""
    # 1. Nonexistent customer
    res1 = await async_client.post(
        "/api/refunds/process",
        json={
            "customer_email": "nonexistent@store.com",
            "order_number": "ORD-2026-9001",
            "item_id": "11111111-1111-1111-1111-111111111101",
            "amount": 45.0,
            "reason_category": "defective",
            "customer_explanation": "Customer does not exist in store records.",
        },
    )
    assert res1.status_code == 404
    assert "customer" in res1.json()["detail"].lower()
    assert "not found" in res1.json()["detail"].lower()

    # 2. Nonexistent order number
    res2 = await async_client.post(
        "/api/refunds/process",
        json={
            "customer_email": "sarah.jenkins@example.com",
            "order_number": "ORD-NONEXISTENT-9999",
            "item_id": "11111111-1111-1111-1111-111111111101",
            "amount": 45.0,
            "reason_category": "defective",
            "customer_explanation": "Order does not exist in store records.",
        },
    )
    assert res2.status_code == 404
    assert "order" in res2.json()["detail"].lower()
    assert "not found" in res2.json()["detail"].lower()

    # 3. Item not belonging to order
    res3 = await async_client.post(
        "/api/refunds/process",
        json={
            "customer_email": "sarah.jenkins@example.com",
            "order_number": "ORD-2026-9001",
            "item_id": str(uuid.uuid4()),
            "amount": 45.0,
            "reason_category": "defective",
            "customer_explanation": "Item does not exist in the specified order.",
        },
    )
    assert res3.status_code == 404
    assert "item" in res3.json()["detail"].lower()
    assert "not found" in res3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ac8_admin_risk_score_and_anomaly_visibility(admin_auth_client, db_session):
    """Verify admin refunds list and detail endpoints return risk_score and anomaly_flags (AC-8)."""
    # Query with min_risk_score filter
    res = await admin_auth_client.get("/api/admin/refunds?min_risk_score=0.0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    assert "risk_score" in first_item
    assert "anomaly_flags" in first_item
    assert isinstance(first_item["risk_score"], (int, float))
    assert isinstance(first_item["anomaly_flags"], list)

    # Query detail
    detail_res = await admin_auth_client.get(f"/api/admin/refunds/{first_item['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "risk_score" in detail
    assert "anomaly_flags" in detail
    assert "error_context" in detail


def test_guardrail_non_refundable_category():
    """Verify deterministic policy guardrail overrides AI approval for digital or gift card categories."""
    svc = PolicyService()
    decision, reason, overridden = svc.enforce_guardrails(
        ai_decision="Approved",
        is_final_sale=False,
        category="gift_card",
    )
    assert decision == "denied"
    assert overridden is True
    assert "strictly non-refundable" in reason.lower()


def test_guardrail_expired_window():
    """Verify deterministic policy guardrail overrides AI approval when days since delivery exceeds return window."""
    svc = PolicyService()
    decision, reason, overridden = svc.enforce_guardrails(
        ai_decision="Approved",
        is_final_sale=False,
        days_since_delivery=95,
        reason="unwanted",
    )
    assert decision == "denied"
    assert overridden is True
    assert "exceeding" in reason.lower()


def test_anomaly_service_pure_scoring():
    """Verify AnomalyService scoring rules and cap behavior."""
    # Empty flags
    score0 = AnomalyService.calculate_risk_score([])
    assert score0 == 0.0

    # Single flag
    score1 = AnomalyService.calculate_risk_score(["velocity_limit_exceeded"])
    assert score1 == 0.4

    # Multiple flags composite capped at 1.0
    score_all = AnomalyService.calculate_risk_score(
        ["velocity_limit_exceeded", "high_value_cluster", "conflicting_claim_detected"]
    )
    assert score_all == 1.0


@pytest.mark.asyncio
async def test_anomaly_service_7d_cumulative_sum(async_client, db_session):
    """Verify cumulative 7-day refund sum > $500 triggers high_value_cluster anomaly."""
    customer_email = "marcus.vance@example.com"
    order_number = "ORD-2026-9120"
    item_id = "14444444-4444-4444-4444-444444444401"

    from app.models.customer import Customer

    cust_res = (
        await db_session.execute(select(Customer).where(Customer.email == customer_email))
    ).scalar_one()

    from app.models.order import Order

    order_res = (
        await db_session.execute(select(Order).where(Order.order_number == order_number))
    ).scalar_one()

    from sqlalchemy import delete

    # Clean up prior test requests
    await db_session.execute(delete(RefundRequest).where(RefundRequest.customer_id == cust_res.id))
    await db_session.commit()

    # Seed 3 prior approved requests totalling $400 in past 3 days
    for i in range(2):
        prior = RefundRequest(
            id=uuid.uuid4(),
            request_number=f"REF-SUM-{uuid.uuid4().hex[:8].upper()}",
            customer_id=cust_res.id,
            order_id=order_res.id,
            item_id=f"prior-item-{i}",
            item_name="Prior Item",
            amount=200.0,
            total_refund_amount=200.0,
            currency="USD",
            reason_category="unwanted",
            customer_explanation="Prior claim building up 7-day sum.",
            status="approved",
            decision="Approved",
            risk_score=0.0,
            anomaly_flags=[],
        )
        db_session.add(prior)
    await db_session.commit()

    # Now submit another request for $150 (Total 7-day sum = $400 + $150 = $550 > $500 threshold)
    payload = {
        "customer_email": customer_email,
        "order_number": order_number,
        "item_id": item_id,
        "amount": 150.0,
        "reason_category": "defective",
        "customer_explanation": "Defective item pushing past 7-day sum limit.",
        "quantity": 1,
        "item_condition": "opened_used",
    }
    response = await async_client.post("/api/refunds/process", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "high_value_cluster" in data["anomaly_flags"]
    assert data["decision"] == "Escalated"
