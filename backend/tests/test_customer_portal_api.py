"""Integration tests for scoped customer refund portal, order isolation, and claim validation."""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem


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

