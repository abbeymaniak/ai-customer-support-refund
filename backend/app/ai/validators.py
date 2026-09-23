"""Post-AI validation: ensures LLM decisions adhere strictly to hard policy boundaries."""

from typing import Any

import structlog

logger = structlog.get_logger()


def enforce_policy_guardrails(
    preliminary_decision: str,
    ai_decision: dict[str, Any],
    rule_reasons: list[str],
) -> dict[str, Any]:
    """Safety guardrail: ensures the LLM cannot override hard deterministic policy rules.

    - Hard Denied rules (e.g. final sale, expired window) cannot be overturned by the LLM.
    - Escalated rules (e.g. high-value >$500, fraud red flags) cannot be auto-approved by the LLM.
    """
    validated = dict(ai_decision)
    decision = validated.get("decision", "Escalated")

    # 1. Final sale or expired window cannot be approved or escalated
    if preliminary_decision == "Denied" and decision != "Denied":
        logger.warning(
            "llm_guardrail_override_denied",
            original_decision=decision,
            enforced="Denied",
            reasons=rule_reasons,
        )
        validated["decision"] = "Denied"
        validated["confidence_score"] = 1.0
        reason_suffix = (
            "; ".join(rule_reasons) if rule_reasons else "Violates non-negotiable policy."
        )
        validated["explanation"] = f"Policy guardrail enforced: Request is denied. {reason_suffix}"

    # 2. High value threshold or fraud red flags cannot be approved
    elif preliminary_decision == "Escalated" and decision == "Approved":
        logger.warning(
            "llm_guardrail_override_escalated",
            original_decision=decision,
            enforced="Escalated",
            reasons=rule_reasons,
        )
        validated["decision"] = "Escalated"
        validated["confidence_score"] = 0.5
        reason_suffix = "; ".join(rule_reasons) if rule_reasons else "Requires supervisor review."
        validated["explanation"] = (
            f"Policy guardrail enforced: Request is escalated to human support. {reason_suffix}"
        )

    return validated


# Backwards compatibility alias
validate_ai_decision = enforce_policy_guardrails
