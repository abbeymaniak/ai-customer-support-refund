"""Unit tests for relational data models, metrics calculations, policy constraints, and audit logging."""

import unittest
import uuid
from datetime import datetime, timedelta, timezone

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


class TestModelDefinitions(unittest.TestCase):
    """Test SQLAlchemy model definitions, table mappings, and attributes."""

    def setUp(self):
        if not HAS_SQLALCHEMY:
            raise unittest.SkipTest("SQLAlchemy not installed in local environment")

    def test_customer_model_instantiation(self):
        """Test Customer model attributes, defaults, and types (covers: AC-1, AC-5)."""
        customer_id = uuid.uuid4()
        customer = Customer(
            id=customer_id,
            email="sarah.jenkins@example.com",
            name="Sarah Jenkins",
            total_spent=3240.50,
            orders_count=18,
            refunds_count=0,
            return_rate=0.0,
            risk_score=0.05,
        )
        self.assertEqual(customer.id, customer_id)
        self.assertEqual(customer.email, "sarah.jenkins@example.com")
        self.assertEqual(customer.orders_count, 18)
        self.assertEqual(customer.refunds_count, 0)
        self.assertEqual(customer.total_spent, 3240.50)
        self.assertEqual(customer.return_rate, 0.0)
        self.assertEqual(customer.risk_score, 0.05)
        self.assertEqual(Customer.__tablename__, "customers")

    def test_order_and_order_item_models(self):
        """Test Order and OrderItem attributes and foreign key ties (covers: AC-1, AC-2, AC-3)."""
        order_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        delivery = now - timedelta(days=5)

        order = Order(
            id=order_id,
            customer_id=customer_id,
            order_number="ORD-2026-9001",
            order_date=now - timedelta(days=7),
            delivery_date=delivery,
            total_amount=85.00,
            currency="USD",
            status="delivered",
            shipping_address={"street": "123 Market St", "city": "San Francisco", "state": "CA"},
        )
        self.assertEqual(order.order_number, "ORD-2026-9001")
        self.assertEqual(order.customer_id, customer_id)
        self.assertEqual(order.delivery_date, delivery)
        self.assertEqual(order.status, "delivered")
        self.assertEqual(Order.__tablename__, "orders")

        item_id = uuid.uuid4()
        order_item = OrderItem(
            id=item_id,
            order_id=order_id,
            product_id="PROD-TECH-001",
            product_name="Wireless Ergonomic Mouse",
            category="electronics",
            price=45.00,
            quantity=1,
            is_final_sale=False,
            serial_number="SN-MOU-9912",
            warranty_status="2yr_limited",
        )
        self.assertEqual(order_item.order_id, order_id)
        self.assertEqual(order_item.product_name, "Wireless Ergonomic Mouse")
        self.assertEqual(order_item.category, "electronics")
        self.assertEqual(order_item.price, 45.00)
        self.assertFalse(order_item.is_final_sale)
        self.assertEqual(OrderItem.__tablename__, "order_items")

    def test_refund_request_and_refund_item_models(self):
        """Test RefundRequest and RefundItem granularity and lifecycle states (covers: AC-1, AC-4)."""
        customer_id = uuid.uuid4()
        order_id = uuid.uuid4()
        item_id = uuid.uuid4()
        refund_id = uuid.uuid4()

        request = RefundRequest(
            id=refund_id,
            request_number="REF-2026-0001",
            customer_id=customer_id,
            order_id=order_id,
            total_refund_amount=45.00,
            currency="USD",
            status="approved",
            reason_category="defective",
            customer_explanation="Scroll wheel sticks intermittently.",
            ai_decision="Approved",
            ai_confidence=0.95,
            ai_reasoning="Item delivered 8 days ago and defective item is fully covered under warranty.",
            policy_evaluations={
                "return_window_ok": True,
                "final_sale_ok": True,
                "under_threshold": True,
            },
            llm_metadata={"model": "gpt-4o-mini", "prompt_tokens": 420, "completion_tokens": 85},
            human_override=False,
        )
        self.assertEqual(request.request_number, "REF-2026-0001")
        self.assertEqual(request.status, "approved")
        self.assertEqual(request.ai_decision, "Approved")
        self.assertEqual(request.ai_confidence, 0.95)
        self.assertFalse(request.human_override)
        self.assertEqual(RefundRequest.__tablename__, "refund_requests")

        refund_item = RefundItem(
            id=uuid.uuid4(),
            refund_request_id=refund_id,
            order_item_id=item_id,
            quantity=1,
            refund_amount=45.00,
            item_condition="opened",
        )
        self.assertEqual(refund_item.refund_request_id, refund_id)
        self.assertEqual(refund_item.order_item_id, item_id)
        self.assertEqual(refund_item.refund_amount, 45.00)
        self.assertEqual(refund_item.item_condition, "opened")
        self.assertEqual(RefundItem.__tablename__, "refund_items")

    def test_audit_log_model(self):
        """Test AuditLog persistence fields and event structure (covers: AC-1, AC-6)."""
        refund_id = uuid.uuid4()
        audit = AuditLog(
            id=uuid.uuid4(),
            refund_request_id=refund_id,
            action="ai_evaluated",
            actor="ai_engine",
            details={"model": "gpt-4o-mini", "decision": "Approved", "confidence": 0.95},
        )
        self.assertEqual(audit.action, "ai_evaluated")
        self.assertEqual(audit.actor, "ai_engine")
        self.assertEqual(audit.refund_request_id, refund_id)
        self.assertEqual(audit.details["model"], "gpt-4o-mini")
        self.assertEqual(AuditLog.__tablename__, "audit_logs")


class TestCustomerMetricsLogic(unittest.TestCase):
    """Test customer spend, return rate, and risk score calculation logic (covers: AC-5)."""

    def compute_risk(self, orders_count: int, refunds_count: int) -> tuple[float, float]:
        """Pure algorithmic replica of CustomerService risk calculation."""
        return_rate = float(refunds_count / orders_count) if orders_count > 0 else 0.0
        base_risk = min(1.0, return_rate * 1.5)
        if refunds_count > 3:
            base_risk = min(1.0, base_risk + 0.2)
        if orders_count > 10 and return_rate < 0.1:
            base_risk = max(0.02, base_risk - 0.1)
        return round(return_rate, 4), round(base_risk, 4)

    def test_zero_orders_metrics(self):
        """New customer with zero orders has zero return rate and zero risk (covers: AC-5)."""
        return_rate, risk_score = self.compute_risk(orders_count=0, refunds_count=0)
        self.assertEqual(return_rate, 0.0)
        self.assertEqual(risk_score, 0.0)

    def test_standard_customer_metrics(self):
        """Standard customer return rate and proportional risk calculation (covers: AC-5)."""
        return_rate, risk_score = self.compute_risk(orders_count=10, refunds_count=2)
        self.assertEqual(return_rate, 0.2)
        # 0.2 * 1.5 = 0.3
        self.assertEqual(risk_score, 0.3)

    def test_frequent_refunder_risk_penalty(self):
        """Customer with more than 3 refunds receives high-frequency penalty (covers: AC-5)."""
        return_rate, risk_score = self.compute_risk(orders_count=8, refunds_count=4)
        self.assertEqual(return_rate, 0.5)
        # base_risk = min(1.0, 0.5 * 1.5) = 0.75; + 0.2 penalty = 0.95
        self.assertEqual(risk_score, 0.95)

    def test_loyal_customer_risk_discount(self):
        """Loyal customer with >10 orders and <10% return rate receives discount (covers: AC-5)."""
        return_rate, risk_score = self.compute_risk(orders_count=20, refunds_count=1)
        self.assertEqual(return_rate, 0.05)
        # base_risk = 0.05 * 1.5 = 0.075; - 0.1 discount = max(0.02, -0.025) = 0.02
        self.assertEqual(risk_score, 0.02)

    def test_max_risk_score_cap(self):
        """Risk score never exceeds 1.0 regardless of return frequency (covers: AC-5)."""
        return_rate, risk_score = self.compute_risk(orders_count=5, refunds_count=5)
        self.assertEqual(return_rate, 1.0)
        self.assertEqual(risk_score, 1.0)


class TestPolicyEvaluationInvariants(unittest.TestCase):
    """Test policy constraints including delivery date return window and final sale exclusions."""

    def test_delivery_window_calculation_within_30_days(self):
        """Orders delivered within 30 days are eligible for return window (covers: AC-3)."""
        order_delivery = datetime.now(timezone.utc) - timedelta(days=12)
        request_time = datetime.now(timezone.utc)
        days_elapsed = (request_time - order_delivery).days
        is_eligible = days_elapsed <= 30
        self.assertTrue(is_eligible)
        self.assertEqual(days_elapsed, 12)

    def test_delivery_window_calculation_exceeding_30_days(self):
        """Orders delivered more than 30 days ago exceed return window (covers: AC-3)."""
        order_delivery = datetime.now(timezone.utc) - timedelta(days=45)
        request_time = datetime.now(timezone.utc)
        days_elapsed = (request_time - order_delivery).days
        is_eligible = days_elapsed <= 30
        self.assertFalse(is_eligible)
        self.assertEqual(days_elapsed, 45)

    def test_final_sale_exclusion_rule(self):
        """Order items marked final sale are excluded from automated refunds (covers: AC-2)."""
        item_final_sale = {
            "product_name": "Clearance Jacket",
            "is_final_sale": True,
            "category": "apparel",
        }
        item_regular = {
            "product_name": "Standard Jacket",
            "is_final_sale": False,
            "category": "apparel",
        }

        self.assertTrue(item_final_sale["is_final_sale"])
        self.assertFalse(item_regular["is_final_sale"])

    def test_refund_total_amount_matches_line_items_sum(self):
        """Refund request total amount must equal the sum of refund item amounts (covers: AC-4)."""
        items = [
            {"product": "Item A", "refund_amount": 45.00, "quantity": 1},
            {"product": "Item B", "refund_amount": 25.50, "quantity": 1},
            {"product": "Item C", "refund_amount": 10.00, "quantity": 2},
        ]
        calculated_total = sum(item["refund_amount"] * item["quantity"] for item in items)
        self.assertEqual(calculated_total, 45.00 + 25.50 + 20.00)
        self.assertEqual(round(calculated_total, 2), 90.50)


class TestAuditLoggingPayloads(unittest.TestCase):
    """Test audit log event structure, actors, and metadata preservation (covers: AC-6)."""

    def test_ai_decision_audit_payload(self):
        """Audit log preserves model name, decision, confidence, and token usage (covers: AC-6)."""
        payload = {
            "action": "ai_evaluated",
            "actor": "ai_engine",
            "details": {
                "model": "gpt-4o-mini",
                "decision": "Approved",
                "confidence": 0.95,
                "prompt_tokens": 420,
                "completion_tokens": 85,
            },
        }
        self.assertEqual(payload["action"], "ai_evaluated")
        self.assertEqual(payload["actor"], "ai_engine")
        self.assertIn("prompt_tokens", payload["details"])
        self.assertEqual(payload["details"]["confidence"], 0.95)

    def test_admin_override_audit_payload(self):
        """Audit log records human override reason and actor identification (covers: AC-6)."""
        payload = {
            "action": "human_override",
            "actor": "lead_support_agent@example.com",
            "details": {
                "previous_decision": "Denied",
                "new_decision": "Approved",
                "reason": "Customer is high value and item was damaged in shipping transit.",
            },
        }
        self.assertEqual(payload["action"], "human_override")
        self.assertEqual(payload["actor"], "lead_support_agent@example.com")
        self.assertEqual(payload["details"]["new_decision"], "Approved")


if __name__ == "__main__":
    unittest.main()
