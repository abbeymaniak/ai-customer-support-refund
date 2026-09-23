import unittest
import uuid
from datetime import datetime, timedelta

try:
    from app.models.audit_log import AuditLog
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.refund_item import RefundItem
    from app.models.refund_request import RefundRequest

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class TestDataModels(unittest.TestCase):
    def setUp(self):
        if not HAS_SQLALCHEMY:
            raise unittest.SkipTest("SQLAlchemy not installed in local environment")

    def test_customer_model_instantiation(self):
        """Test Customer model attributes, defaults, and types."""
        customer_id = uuid.uuid4()
        customer = Customer(
            id=customer_id,
            email="test.user@example.com",
            name="Test User",
            total_spent=500.0,
            orders_count=5,
            refunds_count=1,
            return_rate=0.2,
            risk_score=0.15,
        )
        self.assertEqual(customer.id, customer_id)
        self.assertEqual(customer.email, "test.user@example.com")
        self.assertEqual(customer.orders_count, 5)
        self.assertEqual(customer.return_rate, 0.2)
        self.assertEqual(Customer.__tablename__, "customers")

    def test_order_and_order_item_models(self):
        """Test Order and OrderItem attributes and foreign key ties."""
        order_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        now = datetime.utcnow()
        delivery = now - timedelta(days=2)

        order = Order(
            id=order_id,
            customer_id=customer_id,
            order_number="ORD-TEST-001",
            order_date=now - timedelta(days=5),
            delivery_date=delivery,
            total_amount=150.0,
            currency="USD",
            status="delivered",
        )
        self.assertEqual(order.order_number, "ORD-TEST-001")
        self.assertEqual(order.delivery_date, delivery)
        self.assertEqual(Order.__tablename__, "orders")

        item_id = uuid.uuid4()
        order_item = OrderItem(
            id=item_id,
            order_id=order_id,
            product_id="PROD-TEST-99",
            product_name="Noise Cancelling Headphones",
            category="electronics",
            price=150.0,
            quantity=1,
            is_final_sale=False,
            serial_number="SN-HEAD-001",
            warranty_status="1yr_limited",
        )
        self.assertEqual(order_item.order_id, order_id)
        self.assertEqual(order_item.category, "electronics")
        self.assertFalse(order_item.is_final_sale)
        self.assertEqual(OrderItem.__tablename__, "order_items")

    def test_refund_request_and_refund_item_models(self):
        """Test RefundRequest and RefundItem granularity and lifecycle states."""
        customer_id = uuid.uuid4()
        order_id = uuid.uuid4()
        item_id = uuid.uuid4()
        refund_id = uuid.uuid4()

        request = RefundRequest(
            id=refund_id,
            request_number="REF-TEST-1234",
            customer_id=customer_id,
            order_id=order_id,
            amount=45.0,
            total_refund_amount=45.0,
            currency="USD",
            status="pending",
            reason_category="defective",
            customer_explanation="The left earbud does not produce sound.",
            ai_decision="Approved",
            ai_confidence=0.92,
            policy_evaluations={"within_return_window": True, "eligible_category": True},
        )
        self.assertEqual(request.request_number, "REF-TEST-1234")
        self.assertEqual(request.status, "pending")
        self.assertEqual(request.ai_decision, "Approved")
        self.assertEqual(RefundRequest.__tablename__, "refund_requests")

        refund_item = RefundItem(
            id=uuid.uuid4(),
            refund_request_id=refund_id,
            order_item_id=item_id,
            quantity=1,
            refund_amount=45.0,
            item_condition="opened",
        )
        self.assertEqual(refund_item.refund_request_id, refund_id)
        self.assertEqual(refund_item.refund_amount, 45.0)
        self.assertEqual(refund_item.item_condition, "opened")
        self.assertEqual(RefundItem.__tablename__, "refund_items")

    def test_audit_log_model(self):
        """Test AuditLog persistence fields."""
        refund_id = uuid.uuid4()
        audit = AuditLog(
            id=uuid.uuid4(),
            refund_request_id=refund_id,
            action="policy_evaluated",
            actor="policy_engine",
            details={"rule": "30_day_window", "passed": True},
        )
        self.assertEqual(audit.action, "policy_evaluated")
        self.assertEqual(audit.actor, "policy_engine")
        self.assertTrue(audit.details["passed"])
        self.assertEqual(AuditLog.__tablename__, "audit_logs")


if __name__ == "__main__":
    unittest.main()
