"""Integration tests for scoped customer refund portal, order isolation, and claim validation."""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.refund_item import RefundItem
from app.models.refund_request import RefundRequest


@pytest.mark.asyncio
async def test_unauthenticated_portal_endpoints(async_client):
    """Test AC-1, AC-2: Unauthenticated requests to customer portal endpoints return 401."""
    res_orders = await async_client.get("/api/customer/orders")
    assert res_orders.status_code == 401

    res_refunds = await async_client.post(
        "/api/customer/refunds",
        json={
            "order_id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "This is a test explanation with sufficient length.",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert res_refunds.status_code == 401


@pytest.mark.asyncio
async def test_get_customer_orders_scoped_isolation(async_client, db_session):
    """Test AC-1, AC-4: Authenticated customer retrieves only their own orders with line item claim indicators."""
    # 1. Login as Sarah Jenkins
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    assert login_res.status_code == 200
    token = login_res.cookies["customer_access_token"]
    sarah_id = login_res.json()["id"]

    # 2. Fetch scoped orders
    orders_res = await async_client.get(
        "/api/customer/orders",
        cookies={"customer_access_token": token},
    )
    assert orders_res.status_code == 200
    orders_data = orders_res.json()
    assert len(orders_data) > 0

    # Ensure every single returned order belongs to Sarah
    for order in orders_data:
        assert order["customer_id"] == sarah_id
        assert "items" in order
        for item in order["items"]:
            assert "has_active_claim" in item
            assert isinstance(item["has_active_claim"], bool)
            assert "price" in item
            assert "product_name" in item


@pytest.mark.asyncio
async def test_submit_customer_refund_order_ownership_mismatch(async_client, db_session):
    """Test AC-2: Submitting a refund claim against an order belonging to another customer returns 403 Forbidden."""
    # 1. Login as David Miller
    login_david = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "david.miller@example.com", "password": "customer123"},
    )
    assert login_david.status_code == 200
    david_token = login_david.cookies["customer_access_token"]

    # 2. Find an order belonging to Sarah Jenkins
    sarah_stmt = select(Customer).where(Customer.email == "sarah.jenkins@example.com")
    sarah = (await db_session.execute(sarah_stmt)).scalar_one()

    order_stmt = (
        select(Order)
        .where(Order.customer_id == sarah.id)
        .options(selectinload(Order.order_items))
    )
    sarah_order = (await db_session.execute(order_stmt)).scalars().first()
    assert sarah_order is not None
    assert len(sarah_order.order_items) > 0
    sarah_item = sarah_order.order_items[0]

    # 3. David attempts to file a refund claim for Sarah's order
    tamper_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": david_token},
        json={
            "order_id": str(sarah_order.id),
            "item_id": str(sarah_item.id),
            "reason_category": "defective",
            "customer_explanation": "Attempting to claim refund for an order that is not mine.",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert tamper_res.status_code == 403
    assert "Order does not belong to the authenticated customer" in tamper_res.json()["detail"]


@pytest.mark.asyncio
async def test_submit_customer_refund_item_mismatch_and_bounds(async_client, db_session):
    """Test AC-2: Validate that item must belong to order and quantity cannot exceed purchase."""
    # 1. Login as Sarah Jenkins
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    token = login_res.cookies["customer_access_token"]

    # 2. Get Sarah's first order
    sarah_stmt = select(Customer).where(Customer.email == "sarah.jenkins@example.com")
    sarah = (await db_session.execute(sarah_stmt)).scalar_one()
    order_stmt = (
        select(Order)
        .where(Order.customer_id == sarah.id)
        .options(selectinload(Order.order_items))
    )
    sarah_order = (await db_session.execute(order_stmt)).scalars().first()
    sarah_item = sarah_order.order_items[0]

    # Item not in order
    fake_item_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(sarah_order.id),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "Valid length explanation note for test purposes.",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert fake_item_res.status_code == 400
    assert "Specified item does not belong to this order" in fake_item_res.json()["detail"]

    # Excessive quantity
    excess_qty_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(sarah_order.id),
            "item_id": str(sarah_item.id),
            "reason_category": "defective",
            "customer_explanation": "Valid length explanation note for test purposes.",
            "quantity": 9999,
            "item_condition": "unopened",
        },
    )
    assert excess_qty_res.status_code == 400
    assert "exceeds purchased quantity" in excess_qty_res.json()["detail"]


@pytest.mark.asyncio
async def test_submit_customer_refund_success_and_duplicate_prevention(async_client, db_session):
    """Test AC-2, AC-3, AC-4: End-to-end refund submission, AI evaluation, and duplicate claim blocking."""
    # 1. Login as Elena Rostova
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "elena.rostova@example.com", "password": "customer123"},
    )
    assert login_res.status_code == 200
    token = login_res.cookies["customer_access_token"]
    elena_id = login_res.json()["id"]

    # 2. Create a clean test order and unrefunded item for Elena
    elena_stmt = select(Customer).where(Customer.id == uuid.UUID(elena_id))
    elena = (await db_session.execute(elena_stmt)).scalar_one()

    target_order = Order(
        id=uuid.uuid4(),
        customer_id=elena.id,
        order_number=f"ORD-PORTAL-{uuid.uuid4().hex[:8].upper()}",
        order_date=datetime.utcnow() - timedelta(days=3),
        delivery_date=datetime.utcnow() - timedelta(days=2),
        total_amount=150.0,
        currency="USD",
        status="delivered",
    )
    db_session.add(target_order)

    target_item = OrderItem(
        id=uuid.uuid4(),
        order_id=target_order.id,
        product_id="PROD-PORTAL-TEST",
        product_name="Test Noise-Cancelling Headphones",
        category="electronics",
        price=150.0,
        quantity=1,
        is_final_sale=False,
    )
    db_session.add(target_item)
    await db_session.commit()

    # 3. Submit valid refund claim through scoped portal endpoint
    submit_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(target_order.id),
            "item_id": str(target_item.id),
            "reason_category": "defective",
            "customer_explanation": "Device stopped turning on after two days of normal use. Requesting refund.",
            "quantity": 1,
            "item_condition": "opened_used",
        },
    )
    assert submit_res.status_code == 201
    claim_data = submit_res.json()
    assert claim_data["customer_id"] == elena_id
    assert claim_data["order_id"] == str(target_order.id)
    assert "request_number" in claim_data
    assert claim_data["decision"] in ["Approved", "Denied", "Escalated"]
    assert claim_data["amount"] == target_item.price

    # 4. Attempt to submit duplicate claim for the same item immediately
    dup_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(target_order.id),
            "item_id": str(target_item.id),
            "reason_category": "defective",
            "customer_explanation": "Trying to submit duplicate claim for same item.",
            "quantity": 1,
            "item_condition": "opened_used",
        },
    )
    assert dup_res.status_code == 400
    assert "A refund claim has already been filed for this item" in dup_res.json()["detail"]

    # 5. Verify that GET /api/customer/orders now marks that item with has_active_claim=True
    orders_res = await async_client.get(
        "/api/customer/orders",
        cookies={"customer_access_token": token},
    )
    assert orders_res.status_code == 200
    all_orders = orders_res.json()
    matched_order = next((o for o in all_orders if o["id"] == str(target_order.id)), None)
    assert matched_order is not None
    matched_item = next((i for i in matched_order["items"] if i["id"] == str(target_item.id)), None)
    assert matched_item is not None
    assert matched_item["has_active_claim"] is True
    assert matched_item["claim_status"] is not None


@pytest.mark.asyncio
async def test_get_customer_orders_empty_when_no_orders(async_client, db_session):
    """Test AC-1: Customer with zero orders receives empty array with 200 OK."""
    from app.services.customer_auth_service import CustomerAuthService

    unique_email = f"empty.{uuid.uuid4().hex[:8]}@example.com"
    empty_customer = Customer(
        id=uuid.uuid4(),
        email=unique_email,
        name="Empty Cart User",
        password_hash=CustomerAuthService.hash_password("customer123"),
        is_active=True,
    )
    db_session.add(empty_customer)
    await db_session.commit()

    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": unique_email, "password": "customer123"},
    )
    assert login_res.status_code == 200
    token = login_res.cookies["customer_access_token"]

    orders_res = await async_client.get(
        "/api/customer/orders",
        cookies={"customer_access_token": token},
    )
    assert orders_res.status_code == 200
    assert orders_res.json() == []


@pytest.mark.asyncio
async def test_submit_customer_refund_nonexistent_order(async_client):
    """Test AC-2: Submitting a refund claim against a non-existent order ID returns 404."""
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    token = login_res.cookies["customer_access_token"]

    res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "Valid explanation with more than ten characters.",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert res.status_code == 404
    assert "Order not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_submit_customer_refund_validation_boundary_rejection(async_client):
    """Test AC-2, AC-3: Request validation rejects short explanations and zero quantities with 422."""
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    token = login_res.cookies["customer_access_token"]

    # Short explanation (< 10 chars)
    short_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "Too short",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert short_res.status_code == 422

    # Zero quantity
    zero_qty_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
        json={
            "order_id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "Valid explanation note exceeding minimum length requirement.",
            "quantity": 0,
            "item_condition": "unopened",
        },
    )
    assert zero_qty_res.status_code == 422


@pytest.mark.asyncio
async def test_submit_customer_refund_invalid_token_rejection(async_client):
    """Test AC-1, AC-2, AC-6: Requests with invalid or tampered JWT return 401."""
    res = await async_client.get(
        "/api/customer/orders",
        cookies={"customer_access_token": "tampered.or.invalid.token"},
    )
    assert res.status_code == 401

    post_res = await async_client.post(
        "/api/customer/refunds",
        cookies={"customer_access_token": "tampered.or.invalid.token"},
        json={
            "order_id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "reason_category": "defective",
            "customer_explanation": "Valid explanation note exceeding minimum length requirement.",
            "quantity": 1,
            "item_condition": "unopened",
        },
    )
    assert post_res.status_code == 401


@pytest.mark.asyncio
async def test_get_customer_refunds_unauthenticated(async_client):
    """Test AC-1: Unauthenticated request to GET /api/customer/refunds returns 401."""
    res = await async_client.get("/api/customer/refunds")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_customer_refunds_empty_when_no_claims(async_client, db_session):
    """Test AC-1: Authenticated customer with no claims receives empty list with 200 OK."""
    from app.services.customer_auth_service import CustomerAuthService

    unique_email = f"noclaims.{uuid.uuid4().hex[:8]}@example.com"
    customer = Customer(
        id=uuid.uuid4(),
        email=unique_email,
        name="No Claims User",
        password_hash=CustomerAuthService.hash_password("customer123"),
        is_active=True,
    )
    db_session.add(customer)
    await db_session.commit()

    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": unique_email, "password": "customer123"},
    )
    assert login_res.status_code == 200
    token = login_res.cookies["customer_access_token"]

    refunds_res = await async_client.get(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
    )
    assert refunds_res.status_code == 200
    assert refunds_res.json() == []


@pytest.mark.asyncio
async def test_get_customer_refunds_scoped_isolation(async_client, db_session):
    """Test AC-1, AC-2: Claims are strictly isolated to the authenticated customer."""
    from app.services.customer_auth_service import CustomerAuthService

    # Customer A
    email_a = f"cust_a.{uuid.uuid4().hex[:8]}@example.com"
    cust_a = Customer(
        id=uuid.uuid4(),
        email=email_a,
        name="Customer A",
        password_hash=CustomerAuthService.hash_password("customer123"),
        is_active=True,
    )
    # Customer B
    email_b = f"cust_b.{uuid.uuid4().hex[:8]}@example.com"
    cust_b = Customer(
        id=uuid.uuid4(),
        email=email_b,
        name="Customer B",
        password_hash=CustomerAuthService.hash_password("customer123"),
        is_active=True,
    )
    db_session.add_all([cust_a, cust_b])
    await db_session.commit()

    # Create order and refund claim for Customer A
    order_a = Order(
        id=uuid.uuid4(),
        customer_id=cust_a.id,
        order_number=f"ORD-A-{uuid.uuid4().hex[:6].upper()}",
        order_date=datetime.utcnow() - timedelta(days=5),
        total_amount=150.0,
        currency="USD",
        status="delivered",
    )
    db_session.add(order_a)
    await db_session.commit()

    refund_a = RefundRequest(
        id=uuid.uuid4(),
        request_number=f"REF-A-{uuid.uuid4().hex[:6].upper()}",
        customer_id=cust_a.id,
        order_id=order_a.id,
        item_name="Wireless Keyboard",
        amount=75.0,
        currency="USD",
        reason_category="defective",
        customer_explanation="Keys are repeating and jamming.",
        status="approved",
        decision="Approved",
        ai_decision="Approved",
        confidence_score=0.92,
        ai_reasoning="Defective hardware eligible for immediate refund within warranty.",
        created_at=datetime.utcnow(),
    )
    db_session.add(refund_a)
    await db_session.commit()

    # Login as Customer B
    login_b = await async_client.post(
        "/api/customer/auth/login",
        json={"email": email_b, "password": "customer123"},
    )
    token_b = login_b.cookies["customer_access_token"]

    # Customer B calls GET /api/customer/refunds -> receives empty array
    res_b = await async_client.get(
        "/api/customer/refunds",
        cookies={"customer_access_token": token_b},
    )
    assert res_b.status_code == 200
    assert res_b.json() == []

    # Login as Customer A
    login_a = await async_client.post(
        "/api/customer/auth/login",
        json={"email": email_a, "password": "customer123"},
    )
    token_a = login_a.cookies["customer_access_token"]

    # Customer A calls GET /api/customer/refunds -> receives their own claim
    res_a = await async_client.get(
        "/api/customer/refunds",
        cookies={"customer_access_token": token_a},
    )
    assert res_a.status_code == 200
    claims_a = res_a.json()
    assert len(claims_a) == 1
    assert claims_a[0]["request_number"] == refund_a.request_number
    assert claims_a[0]["order_number"] == order_a.order_number
    assert claims_a[0]["item_name"] == "Wireless Keyboard"
    assert claims_a[0]["amount"] == 75.0
    assert claims_a[0]["decision"] == "Approved"
    assert claims_a[0]["ai_reasoning"] == "Defective hardware eligible for immediate refund within warranty."


@pytest.mark.asyncio
async def test_get_customer_refunds_descending_order_and_override_details(async_client, db_session):
    """Test AC-2: Claims are returned in descending chronological order with supervisor override details."""
    from app.services.customer_auth_service import CustomerAuthService

    email = f"history.{uuid.uuid4().hex[:8]}@example.com"
    customer = Customer(
        id=uuid.uuid4(),
        email=email,
        name="History Customer",
        password_hash=CustomerAuthService.hash_password("customer123"),
        is_active=True,
    )
    db_session.add(customer)
    await db_session.commit()

    order = Order(
        id=uuid.uuid4(),
        customer_id=customer.id,
        order_number=f"ORD-H-{uuid.uuid4().hex[:6].upper()}",
        order_date=datetime.utcnow() - timedelta(days=10),
        total_amount=300.0,
        currency="USD",
        status="delivered",
    )
    db_session.add(order)
    await db_session.commit()

    order_item = OrderItem(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id="PROD-HISTORY-TEST",
        product_name="Headphones",
        category="electronics",
        price=120.0,
        quantity=1,
    )
    db_session.add(order_item)
    await db_session.commit()

    older_claim = RefundRequest(
        id=uuid.uuid4(),
        request_number=f"REF-OLD-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        order_id=order.id,
        item_name="Gaming Mouse",
        amount=60.0,
        currency="USD",
        reason_category="unwanted",
        customer_explanation="Did not like ergonomic shape.",
        status="denied",
        decision="Denied",
        ai_decision="Denied",
        confidence_score=0.88,
        ai_reasoning="Return window exceeded standard policy.",
        created_at=datetime.utcnow() - timedelta(days=2),
    )

    newer_claim = RefundRequest(
        id=uuid.uuid4(),
        request_number=f"REF-NEW-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        order_id=order.id,
        item_name="Headphones",
        amount=120.0,
        currency="USD",
        reason_category="damaged_on_arrival",
        customer_explanation="Cracked headband out of box.",
        status="approved",
        decision="Approved",
        ai_decision="Escalated",
        confidence_score=0.65,
        ai_reasoning="Borderline damage claim flagged for review.",
        human_override=True,
        override_reason="Customer sent photos showing clear transit damage.",
        override_by="supervisor@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add_all([older_claim, newer_claim])
    await db_session.commit()

    refund_item = RefundItem(
        id=uuid.uuid4(),
        refund_request_id=newer_claim.id,
        order_item_id=order_item.id,
        quantity=1,
        refund_amount=120.0,
        item_condition="damaged",
    )
    db_session.add(refund_item)
    await db_session.commit()

    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": email, "password": "customer123"},
    )
    token = login_res.cookies["customer_access_token"]

    res = await async_client.get(
        "/api/customer/refunds",
        cookies={"customer_access_token": token},
    )
    assert res.status_code == 200
    claims = res.json()
    assert len(claims) == 2

    # Verify descending order: newer_claim first
    assert claims[0]["request_number"] == newer_claim.request_number
    assert claims[0]["item_name"] == "Headphones"
    assert claims[0]["human_override"] is True
    assert claims[0]["override_reason"] == "Customer sent photos showing clear transit damage."
    assert claims[0]["override_by"] == "supervisor@example.com"
    assert claims[0]["ai_decision"] == "Escalated"
    assert claims[0]["decision"] == "Approved"
    assert claims[0]["items"] == [
        {
            "id": str(refund_item.id),
            "order_item_id": str(order_item.id),
            "product_name": "Headphones",
            "quantity": 1,
            "refund_amount": 120.0,
            "item_condition": "damaged",
        }
    ]

    # Second claim is older_claim
    assert claims[1]["request_number"] == older_claim.request_number
    assert claims[1]["item_name"] == "Gaming Mouse"
    assert claims[1]["human_override"] is False


