import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "services"))
from policy_service import PolicyService


class TestPolicyService(unittest.TestCase):
    def setUp(self):
        # Locate refund_policy.json relative to repository root
        repo_root = Path(__file__).resolve().parent.parent.parent
        self.policy_path = repo_root / "data" / "refund_policy.json"
        self.service = PolicyService(str(self.policy_path))

    def test_load_policy_success(self):
        """Test policy is loaded properly with all required top-level keys."""
        policy = self.service.load_policy()
        self.assertIn("version", policy)
        self.assertIn("general_rules", policy)
        self.assertIn("decision_types", policy)
        self.assertIn("categories", policy)
        self.assertIn("rules", policy)

    def test_policy_general_rules_thresholds(self):
        """Test key thresholds defined in the refund policy."""
        policy = self.service.get_policy()
        general = policy.get("general_rules", {})
        self.assertEqual(general.get("return_window_days"), 30)
        self.assertEqual(general.get("max_auto_approval_amount"), 100.0)
        self.assertEqual(general.get("require_human_escalation_amount"), 500.0)
        self.assertEqual(general.get("high_risk_return_rate_threshold"), 0.40)

    def test_non_refundable_categories_defined(self):
        """Test non-refundable categories contain standard excluded items."""
        policy = self.service.get_policy()
        non_refundable = policy.get("categories", {}).get("non_refundable_categories", [])
        self.assertIn("gift_cards", non_refundable)
        self.assertIn("perishables", non_refundable)
        self.assertIn("clearance_items", non_refundable)

    def test_decision_types(self):
        """Test policy allows Approved, Denied, and Escalated decisions."""
        policy = self.service.get_policy()
        decisions = policy.get("decision_types", [])
        self.assertIn("Approved", decisions)
        self.assertIn("Denied", decisions)
        self.assertIn("Escalated", decisions)


if __name__ == "__main__":
    unittest.main()
