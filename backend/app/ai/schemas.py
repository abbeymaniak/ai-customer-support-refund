from typing import Any, Literal

from pydantic import BaseModel, Field


class AIOutputSchema(BaseModel):
    """Structured output expected from language model evaluation."""

    decision: Literal["Approved", "Denied", "Escalated"] = Field(
        description="The recommended refund decision"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 calibrated to policy certainty",
    )
    explanation: str = Field(
        description="Clear, empathetic, and professional explanation for the customer"
    )
    policy_citations: list[str] = Field(
        default_factory=list,
        description="Official store policy section citations (e.g. 'Refund Policy § 1.1')",
    )
    matched_rules: list[str] = Field(
        default_factory=list,
        description="Rule identifiers triggered by this claim (e.g. 'RULE_RETURN_WINDOW')",
    )
    audit_notes: str = Field(
        default="",
        description="Internal technical notes for support managers and audit logs",
    )
    suggested_action: str = Field(
        default="process_refund",
        description="Operational action recommendation (e.g. 'process_refund', 'supervisor_review')",
    )


class RefundEvaluationContext(BaseModel):
    """Structured context payload injected into the AI prompt."""

    customer: dict[str, Any] = Field(
        description="Customer profile summary (spend, orders count, return rate, risk score)"
    )
    order: dict[str, Any] = Field(
        description="Order details (number, purchase date, delivery date)"
    )
    refund_item: dict[str, Any] = Field(
        description="Item being refunded (name, price, quantity, condition, is_final_sale)"
    )
    reason_category: str = Field(description="Selected refund reason category")
    customer_explanation: str = Field(
        default="",
        description="Customer provided explanation notes (truncated to max 500 chars)",
    )
    policy_rules: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured summary of applicable store policy rules",
    )
