import uuid

import pytest


@pytest.mark.asyncio
async def test_lookup_customer_success(async_client):
    """Test retrieving an existing seeded customer by email."""
    response = await async_client.get("/api/customers/lookup?email=sarah.jenkins@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "sarah.jenkins@example.com"
    assert data["name"] == "Sarah Jenkins"
    assert "total_spent" in data
    assert "return_rate" in data
    assert "risk_score" in data


@pytest.mark.asyncio
async def test_lookup_customer_not_found(async_client):
    """Test 404 response for unknown email address."""
    response = await async_client.get("/api/customers/lookup?email=unknown.user@example.com")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_customer_orders_success(async_client):
    """Test retrieving orders and items for a valid customer ID."""
    customer_res = await async_client.get("/api/customers/lookup?email=sarah.jenkins@example.com")
    assert customer_res.status_code == 200
    customer_id = customer_res.json()["id"]

    orders_res = await async_client.get(f"/api/customers/{customer_id}/orders")
    assert orders_res.status_code == 200
    orders = orders_res.json()
    assert len(orders) >= 1
    first_order = orders[0]
    assert "order_number" in first_order
    assert "items" in first_order
    assert len(first_order["items"]) >= 1
    first_item = first_order["items"][0]
    assert "name" in first_item
    assert "price" in first_item
    assert "is_final_sale" in first_item


@pytest.mark.asyncio
async def test_get_customer_orders_not_found(async_client):
    """Test 404 response for unknown customer ID."""
    random_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/customers/{random_id}/orders")
    assert response.status_code == 404
