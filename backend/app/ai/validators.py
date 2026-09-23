"""Post-AI validation: ensures LLM decisions adhere strictly to hard policy boundaries."""

from typing import Any

import structlog

logger = structlog.get_logger()


def enforce_policy_guardrails(
    preliminary_decision: str,
    ai_decision: dict[str, Any],
    rule_reasons: list[str],
    customer_risk_score: float = 0.0,
    customer_return_rate: float = 0.0,
) -> dict[str, Any]:
    """Safety guardrail: ensures the LLM cannot override hard deterministic policy rules.

    - Hard Denied rules (final sale, expired window) cannot be overturned by the LLM.
    - Escalated rules (high-value >$500, fraud red flags) cannot be auto-approved by the LLM.
    - Confidence scores below 0.75 automatically escalate to human review.
    - High-risk customer profiles cannot be auto-approved.
    """
    validated = dict(ai_decision)
    decision = validated.get("decision", "Escalated")
    confidence = float(validated.get("confidence_score", 0.5))
    guardrails_triggered = list(validated.get("guardrails_triggered", []))

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
        guardrails_triggered.append("OVERRIDE_HARD_DENIAL")
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
        guardrails_triggered.append("OVERRIDE_HARD_ESCALATION")
        reason_suffix = "; ".join(rule_reasons) if rule_reasons else "Requires supervisor review."
        validated["explanation"] = (
            f"Policy guardrail enforced: Request is escalated to human support. {reason_suffix}"
        )

    # 3. Model proposed approval but confidence is below calibrated threshold (AC-4)
    elif validated.get("decision") == "Approved" and confidence < 0.75:
        logger.info(
            "llm_guardrail_low_confidence_escalation",
            confidence_score=confidence,
            threshold=0.75,
        )
        validated["decision"] = "Escalated"
        validated["confidence_score"] = 0.5
        guardrails_triggered.append("LOW_CONFIDENCE_ESCALATION")
        validated["explanation"] = (
            f"Your request has been routed to human support for review (confidence {confidence:.0%} is below 75% automated approval threshold)."
        )

    # 4. Elevated customer risk profile cannot be auto-approved
    elif validated.get("decision") == "Approved" and (customer_risk_score > 0.70 or customer_return_rate > 0.50):
        logger.warning(
            "llm_guardrail_risk_profile_escalation",
            risk_score=customer_risk_score,
            return_rate=customer_return_rate,
        )
        validated["decision"] = "Escalated"
        validated["confidence_score"] = 0.5
        guardrails_triggered.append("SUSPICIOUS_RISK_PROFILE_ESCALATION")
        validated["explanation"] = (
            "Your request has been routed to human support for standard verification due to account history parameters."
        )

    validated["guardrails_triggered"] = guardrails_triggered
    return validated


# Backwards compatibility alias
validate_ai_decision = enforce_policy_guardrails
