import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.schemas.policy import PolicyDocument  # noqa: E402
from app.services.policy_service import PolicyService  # noqa: E402


class TestPolicyService(unittest.TestCase):
    def setUp(self):
        repo_root = backend_dir.parent
        self.policy_path = repo_root / "data" / "refund_policy.json"
        self.service = PolicyService(self.policy_path)

    def test_load_policy_success(self):
        """Test policy is loaded properly with all required top-level keys."""
        policy = self.service.load_policy()
        self.assertEqual(policy.get("version"), "2.0.0")
        self.assertIn("general_rules", policy)
        self.assertIn("decision_types", policy)
        self.assertIn("categories", policy)
        self.assertIn("rules", policy)
        self.assertIn("red_flags", policy)

    def test_pydantic_policy_document_valid(self):
        """Test policy document is validated and parsed into Pydantic models."""
        doc = self.service.get_policy_document()
        self.assertIsInstance(doc, PolicyDocument)
        self.assertEqual(doc.version, "2.0.0")
        self.assertEqual(doc.general_rules.return_window_days, 90)
        self.assertEqual(doc.general_rules.require_human_escalation_amount, 500.0)
        self.assertEqual(len(doc.rules), 6)
        self.assertEqual(len(doc.red_flags), 5)

    def test_return_window_thresholds(self):
        """Test general return window rules: 90 days standard, 120 days defect."""
        general = self.service.get_general_rules()
        self.assertEqual(general.return_window_days, 90)
        self.assertEqual(general.damaged_defective_window_days, 120)
        self.assertEqual(general.immediate_report_window_days, 7)

    def test_financial_thresholds(self):
        """Test financial thresholds: $500 escalation and $100 auto approval."""
        general = self.service.get_general_rules()
        self.assertEqual(general.require_human_escalation_amount, 500.0)
        self.assertEqual(general.max_auto_approval_amount, 100.0)
        self.assertEqual(general.high_risk_return_rate_threshold, 0.40)
        self.assertEqual(general.excessive_refunds_count_threshold, 3)

    def test_non_refundable_categories_defined(self):
        """Test non-refundable categories contain standard excluded merchandise."""
        doc = self.service.get_policy_document()
        non_refundable = doc.categories.non_refundable_categories
        self.assertIn("gift_cards", non_refundable)
        self.assertIn("perishables", non_refundable)
        self.assertIn("digital_downloads", non_refundable)
        self.assertIn("clearance_items", non_refundable)
        self.assertIn("custom_items", non_refundable)
        self.assertIn("personal_hygiene", non_refundable)

    def test_final_sale_exclusion(self):
        """Test that final sale flag strictly denies refunds under RULE_FINAL_SALE."""
        result = self.service.evaluate_rules(
            days_since_delivery=10,
            total_refund_amount=45.0,
            is_final_sale=True,
            category="apparel",
        )
        self.assertEqual(result.preliminary_decision, "Denied")
        self.assertTrue(result.is_denied)
        self.assertIn("RULE_FINAL_SALE", result.matched_rules)
        self.assertIn("Refund Policy § 1.1", result.citations[0])

    def test_non_refundable_category_denies(self):
        """Test that non-refundable category items are denied even if within return window."""
        result = self.service.evaluate_rules(
            days_since_delivery=5,
            total_refund_amount=25.0,
            is_final_sale=False,
            category="gift_cards",
        )
        self.assertEqual(result.preliminary_decision, "Denied")
        self.assertTrue(result.is_denied)
        self.assertIn("RULE_FINAL_SALE", result.matched_rules)

    def test_return_window_90_days_enforced(self):
        """Test that 90-day return window is enforced strictly."""
        # 45 days: eligible
        result_45 = self.service.evaluate_rules(
            days_since_delivery=45,
            total_refund_amount=60.0,
        )
        self.assertEqual(result_45.preliminary_decision, "Approved")

        # 90 days: boundary eligible
        result_90 = self.service.evaluate_rules(
            days_since_delivery=90,
            total_refund_amount=60.0,
        )
        self.assertEqual(result_90.preliminary_decision, "Approved")

        # 91 days: expired and denied
        result_91 = self.service.evaluate_rules(
            days_since_delivery=91,
            total_refund_amount=60.0,
        )
        self.assertEqual(result_91.preliminary_decision, "Denied")
        self.assertIn("RULE_RETURN_WINDOW", result_91.matched_rules)
        self.assertIn("Refund Policy § 1.2", result_91.citations[0])

    def test_high_value_refund_escalates(self):
        """Test that refund requests exceeding $500 escalate to supervisor review."""
        # $500.00: does not exceed threshold
        result_500 = self.service.evaluate_rules(
            days_since_delivery=14,
            total_refund_amount=500.0,
        )
        self.assertFalse(result_500.is_escalated)

        # $500.01: exceeds threshold
        result_501 = self.service.evaluate_rules(
            days_since_delivery=14,
            total_refund_amount=500.01,
        )
        self.assertEqual(result_501.preliminary_decision, "Escalated")
        self.assertTrue(result_501.is_escalated)
        self.assertIn("RULE_HIGH_VALUE_ESCALATION", result_501.matched_rules)
        self.assertIn("Refund Policy § 2.1", result_501.citations[0])

    def test_damaged_defective_item_extended_window(self):
        """Test damaged or defective items qualify for extended 120-day evaluation."""
        result = self.service.evaluate_rules(
            days_since_delivery=105,  # Exceeds 90 days, within 120 days
            total_refund_amount=150.0,
            reason="defective",
        )
        self.assertEqual(result.preliminary_decision, "Approved")
        self.assertIn("RULE_DAMAGED_INCORRECT_ITEM", result.matched_rules)

        # Exceeds 120 days -> Denied
        result_expired = self.service.evaluate_rules(
            days_since_delivery=125,
            total_refund_amount=150.0,
            reason="defective",
        )
        self.assertEqual(result_expired.preliminary_decision, "Denied")
        self.assertIn("RULE_RETURN_WINDOW", result_expired.matched_rules)

    def test_buyer_remorse_opened_item_denied(self):
        """Test buyer remorse for opened and used item is denied."""
        result = self.service.evaluate_rules(
            days_since_delivery=20,
            total_refund_amount=80.0,
            reason="unwanted",
            item_condition="opened_used",
        )
        self.assertEqual(result.preliminary_decision, "Denied")
        self.assertIn("RULE_BUYER_REMORSE", result.matched_rules)

    def test_duplicate_claim_red_flag_escalation(self):
        """Test that duplicate refund claims trigger FLAG_DUPLICATE_CLAIM and escalate."""
        result = self.service.evaluate_rules(
            days_since_delivery=10,
            total_refund_amount=40.0,
            has_prior_refund_for_order=True,
        )
        self.assertEqual(result.preliminary_decision, "Escalated")
        self.assertIn("FLAG_DUPLICATE_CLAIM", result.triggered_red_flags)
        self.assertIn("Fraud Prevention § 3.1", result.citations[0])

    def test_conflicting_claims_red_flag_escalation(self):
        """Test that claim contradicting carrier proof of delivery triggers FLAG_CONFLICTING_CLAIMS."""
        result = self.service.evaluate_rules(
            days_since_delivery=5,
            total_refund_amount=75.0,
            reason="item_not_received",
            carrier_confirmed_delivery=True,
            carrier_signature_present=True,
        )
        self.assertEqual(result.preliminary_decision, "Escalated")
        self.assertIn("FLAG_CONFLICTING_CLAIMS", result.triggered_red_flags)
        self.assertIn("Fraud Prevention § 3.2", result.citations[0])

    def test_high_risk_customer_return_rate_escalation(self):
        """Test that customer return rate >= 40% triggers FLAG_HIGH_RISK_RETURN_RATE."""
        result = self.service.evaluate_rules(
            days_since_delivery=15,
            total_refund_amount=50.0,
            customer_return_rate=0.42,
        )
        self.assertEqual(result.preliminary_decision, "Escalated")
        self.assertIn("FLAG_HIGH_RISK_RETURN_RATE", result.triggered_red_flags)
        self.assertIn("Fraud Prevention § 3.3", result.citations[0])

    def test_format_for_prompt(self):
        """Test prompt context generation for LiteLLM contains all rules and red flags."""
        prompt_text = self.service.format_for_prompt()
        self.assertIn("E-Commerce Customer Support Refund Policy (v2.0.0)", prompt_text)
        self.assertIn("Standard Return Window: 90 calendar days", prompt_text)
        self.assertIn("Supervisor Escalation Threshold: claims > $500.00", prompt_text)
        self.assertIn("RULE_FINAL_SALE", prompt_text)
        self.assertIn("RULE_RETURN_WINDOW", prompt_text)
        self.assertIn("RULE_HIGH_VALUE_ESCALATION", prompt_text)
        self.assertIn("RULE_DAMAGED_INCORRECT_ITEM", prompt_text)
        self.assertIn("FLAG_DUPLICATE_CLAIM", prompt_text)
        self.assertIn("FLAG_CONFLICTING_CLAIMS", prompt_text)
        self.assertIn("FLAG_HIGH_RISK_RETURN_RATE", prompt_text)


if __name__ == "__main__":
    unittest.main()
