"""Policy service for loading, formatting, and evaluating the machine-readable refund policy."""

import json
from pathlib import Path
from typing import Any

from app.schemas.policy import (
    GeneralRules,
    PolicyDocument,
    PolicyRule,
    RedFlag,
    RuleEvaluationResult,
)


class PolicyService:
    """Service to load, query, format, and evaluate refund policy rules."""

    def __init__(self, policy_path: str | Path | None = None) -> None:
        self.policy_path = self._resolve_policy_path(policy_path)
        self._policy_doc: PolicyDocument | None = None
        self._raw_policy: dict[str, Any] = {}

    def _resolve_policy_path(self, custom_path: str | Path | None) -> Path:
        """Resolve policy JSON file path across development, testing, and container environments."""
        if custom_path:
            p = Path(custom_path)
            if p.exists():
                return p

        # Check relative to backend service directory (repo_root/data/refund_policy.json)
        backend_dir = Path(__file__).resolve().parent.parent.parent
        repo_data_path = backend_dir.parent / "data" / "refund_policy.json"
        if repo_data_path.exists():
            return repo_data_path

        # Check relative to current working directory
        cwd_path = Path.cwd() / "data" / "refund_policy.json"
        if cwd_path.exists():
            return cwd_path

        # Check Docker container root mount
        docker_mount_path = Path("/app/data/refund_policy.json")
        if docker_mount_path.exists():
            return docker_mount_path

        # Fallback to default relative path
        return Path("data/refund_policy.json")

    def load_policy(self) -> dict[str, Any]:
        """Load and parse the refund policy JSON document."""
        if not self.policy_path.exists():
            self._raw_policy = {}
            return {}

        with open(self.policy_path, encoding="utf-8") as f:
            self._raw_policy = json.load(f)

        self._policy_doc = PolicyDocument.model_validate(self._raw_policy)
        return self._raw_policy

    def get_policy(self) -> dict[str, Any]:
        """Return the loaded raw policy dictionary for backwards compatibility."""
        if not self._raw_policy:
            self.load_policy()
        return self._raw_policy

    def get_policy_document(self) -> PolicyDocument:
        """Return the validated PolicyDocument Pydantic model."""
        if self._policy_doc is None:
            self.load_policy()
            if self._policy_doc is None:
                raise FileNotFoundError(f"Policy file not found at {self.policy_path}")
        return self._policy_doc

    def get_general_rules(self) -> GeneralRules:
        """Return the general rules and operational thresholds."""
        return self.get_policy_document().general_rules

    def get_rules(self) -> list[PolicyRule]:
        """Return the list of core policy rules."""
        return self.get_policy_document().rules

    def get_red_flags(self) -> list[RedFlag]:
        """Return the list of fraud and suspicious activity red flags."""
        return self.get_policy_document().red_flags

    def get_rule_by_id(self, rule_id: str) -> PolicyRule | None:
        """Find a policy rule by its unique identifier."""
        for rule in self.get_rules():
            if rule.id == rule_id:
                return rule
        return None

    def get_red_flag_by_id(self, flag_id: str) -> RedFlag | None:
        """Find a red flag definition by its unique identifier."""
        for flag in self.get_red_flags():
            if flag.id == flag_id:
                return flag
        return None

    def format_for_prompt(self) -> str:
        """Format the entire policy into structured markdown text for AI system prompts."""
        doc = self.get_policy_document()
        general = doc.general_rules

        lines = [
            f"# {doc.policy_name} (v{doc.version})",
            "",
            "## Key Thresholds & Parameters",
            f"- Standard Return Window: {general.return_window_days} calendar days from delivery",
            f"- Latent Defect Return Window: {general.damaged_defective_window_days} calendar days",
            f"- Supervisor Escalation Threshold: claims > ${general.require_human_escalation_amount:.2f}",
            f"- Automated Approval Maximum: claims <= ${general.max_auto_approval_amount:.2f}",
            f"- High Risk Customer Return Rate: >= {general.high_risk_return_rate_threshold * 100:.0f}%",
            f"- High Risk Historical Refunds Count: >= {general.excessive_refunds_count_threshold}",
            "",
            "## Non-Refundable Categories",
            f"Strictly non-refundable: {', '.join(doc.categories.non_refundable_categories)}",
            "",
            "## Core Policy Rules",
        ]

        for rule in doc.rules:
            action_desc = (
                f"Action: {rule.action}" if rule.action else f"Violation: {rule.violation_action}"
            )
            lines.append(f"### [{rule.id}] {rule.name}")
            lines.append(f"- Citation: {rule.citation}")
            lines.append(f"- Condition: {rule.condition}")
            lines.append(f"- Result: {action_desc}")
            lines.append(f"- Details: {rule.description}")
            if rule.exception:
                lines.append(f"- Exception: {rule.exception}")
            lines.append("")

        lines.append("## Suspicious Pattern Red Flags (Escalate to Human Agent)")
        for flag in doc.red_flags:
            lines.append(f"### [{flag.id}] {flag.name}")
            lines.append(f"- Risk Level: {flag.risk_level} | Action: {flag.action}")
            lines.append(f"- Trigger: {flag.condition}")
            lines.append(f"- Citation: {flag.citation}")
            lines.append(f"- Details: {flag.description}")
            lines.append("")

        return "\n".join(lines)

    def evaluate_rules(
        self,
        days_since_delivery: int | None,
        total_refund_amount: float,
        is_final_sale: bool = False,
        category: str = "apparel",
        reason: str = "unwanted",
        item_condition: str = "unopened_original_packaging",
        customer_return_rate: float = 0.0,
        customer_refunds_count: int = 0,
        has_prior_refund_for_order: bool = False,
        has_prior_refund_for_item: bool = False,
        carrier_confirmed_delivery: bool = True,
        carrier_signature_present: bool = False,
    ) -> RuleEvaluationResult:
        """Perform deterministic pre-evaluation of refund request against policy rules."""
        doc = self.get_policy_document()
        general = doc.general_rules

        matched_rules: list[str] = []
        triggered_red_flags: list[str] = []
        reasons: list[str] = []
        citations: list[str] = []

        # 1. Check Red Flags (Fraud and Suspicious Activity)
        if has_prior_refund_for_order or has_prior_refund_for_item:
            flag = self.get_red_flag_by_id("FLAG_DUPLICATE_CLAIM")
            triggered_red_flags.append("FLAG_DUPLICATE_CLAIM")
            reasons.append(
                "A refund request was previously submitted or processed for this order item."
            )
            if flag:
                citations.append(flag.citation)

        if (
            reason == "item_not_received"
            and carrier_confirmed_delivery
            and carrier_signature_present
        ):
            flag = self.get_red_flag_by_id("FLAG_CONFLICTING_CLAIMS")
            triggered_red_flags.append("FLAG_CONFLICTING_CLAIMS")
            reasons.append("Claim contradicts carrier proof of delivery signature.")
            if flag:
                citations.append(flag.citation)

        if (
            customer_return_rate >= general.high_risk_return_rate_threshold
            or customer_refunds_count >= general.excessive_refunds_count_threshold
        ):
            flag = self.get_red_flag_by_id("FLAG_HIGH_RISK_RETURN_RATE")
            triggered_red_flags.append("FLAG_HIGH_RISK_RETURN_RATE")
            reasons.append(
                f"Customer account shows elevated return history (rate: {customer_return_rate:.1%}, count: {customer_refunds_count})."
            )
            if flag:
                citations.append(flag.citation)

        # 2. Check Final Sale & Non-Refundable Categories
        is_non_refundable_cat = category in doc.categories.non_refundable_categories
        if is_final_sale or is_non_refundable_cat:
            rule = self.get_rule_by_id("RULE_FINAL_SALE")
            matched_rules.append("RULE_FINAL_SALE")
            reason_text = (
                "Item marked as final sale."
                if is_final_sale
                else f"Category '{category}' is non-refundable."
            )
            reasons.append(reason_text)
            if rule:
                citations.append(rule.citation)
            return RuleEvaluationResult(
                preliminary_decision="Denied",
                matched_rules=matched_rules,
                triggered_red_flags=triggered_red_flags,
                reasons=reasons,
                citations=citations,
                is_denied=True,
            )

        # 3. Check High-Value Threshold Escalation
        if total_refund_amount > general.require_human_escalation_amount:
            rule = self.get_rule_by_id("RULE_HIGH_VALUE_ESCALATION")
            matched_rules.append("RULE_HIGH_VALUE_ESCALATION")
            reasons.append(
                f"Refund total (${total_refund_amount:.2f}) exceeds human supervisor escalation threshold (${general.require_human_escalation_amount:.2f})."
            )
            if rule:
                citations.append(rule.citation)

        # If red flags triggered or high value escalation, result is Escalated
        if triggered_red_flags or "RULE_HIGH_VALUE_ESCALATION" in matched_rules:
            return RuleEvaluationResult(
                preliminary_decision="Escalated",
                matched_rules=matched_rules,
                triggered_red_flags=triggered_red_flags,
                reasons=reasons,
                citations=citations,
                is_escalated=True,
            )

        # 4. Check Return Window (90 Days standard, 120 days for defect/damage)
        is_defect_or_damage = reason in ["damaged_on_arrival", "defective", "wrong_item_sent"]
        effective_window = (
            general.damaged_defective_window_days
            if is_defect_or_damage
            else general.return_window_days
        )

        if days_since_delivery is not None and days_since_delivery > effective_window:
            rule = self.get_rule_by_id("RULE_RETURN_WINDOW")
            matched_rules.append("RULE_RETURN_WINDOW")
            reasons.append(
                f"Request submitted {days_since_delivery} days after delivery, exceeding the {effective_window}-day window."
            )
            if rule:
                citations.append(rule.citation)
            return RuleEvaluationResult(
                preliminary_decision="Denied",
                matched_rules=matched_rules,
                triggered_red_flags=triggered_red_flags,
                reasons=reasons,
                citations=citations,
                is_denied=True,
            )

        # 5. Check Buyer Remorse Condition
        if reason in ["unwanted", "bought_by_mistake", "changed_mind"]:
            if item_condition == "opened_used":
                rule = self.get_rule_by_id("RULE_BUYER_REMORSE")
                matched_rules.append("RULE_BUYER_REMORSE")
                reasons.append("Opened and used items cannot be refunded for buyer remorse.")
                if rule:
                    citations.append(rule.citation)
                return RuleEvaluationResult(
                    preliminary_decision="Denied",
                    matched_rules=matched_rules,
                    triggered_red_flags=triggered_red_flags,
                    reasons=reasons,
                    citations=citations,
                    is_denied=True,
                )

        # 6. Check Damaged / Incorrect Item Approval
        if is_defect_or_damage:
            rule = self.get_rule_by_id("RULE_DAMAGED_INCORRECT_ITEM")
            matched_rules.append("RULE_DAMAGED_INCORRECT_ITEM")
            reasons.append(
                "Damaged, defective, or incorrect merchandise qualifies for refund or replacement."
            )
            if rule:
                citations.append(rule.citation)
            return RuleEvaluationResult(
                preliminary_decision="Approved",
                matched_rules=matched_rules,
                triggered_red_flags=triggered_red_flags,
                reasons=reasons,
                citations=citations,
                is_approved=True,
            )

        # 7. Fast-Track Auto Approval for Good Standing
        if (
            customer_return_rate < 0.10
            and total_refund_amount <= general.max_auto_approval_amount
            and (days_since_delivery is None or days_since_delivery <= general.return_window_days)
        ):
            rule = self.get_rule_by_id("RULE_GOOD_STANDING_FAST_TRACK")
            matched_rules.append("RULE_GOOD_STANDING_FAST_TRACK")
            reasons.append("Account qualifies for fast-track auto-approval.")
            if rule:
                citations.append(rule.citation)
            return RuleEvaluationResult(
                preliminary_decision="Approved",
                matched_rules=matched_rules,
                triggered_red_flags=triggered_red_flags,
                reasons=reasons,
                citations=citations,
                is_approved=True,
            )

        # Default standard approval
        return RuleEvaluationResult(
            preliminary_decision="Approved",
            matched_rules=matched_rules,
            triggered_red_flags=triggered_red_flags,
            reasons=["Standard return request meets all policy criteria."],
            citations=citations,
            is_approved=True,
        )
