"""Pydantic schemas for machine-readable refund policy specification."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DecisionType = Literal["Approved", "Denied", "Escalated"]
RiskLevel = Literal["Low", "Medium", "High"]


class GeneralRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    return_window_days: int = Field(default=90, description="Standard return window in days")
    damaged_defective_window_days: int = Field(
        default=120, description="Window for damaged or defective items"
    )
    immediate_report_window_days: int = Field(
        default=7, description="Notice window for transit damage"
    )
    max_auto_approval_amount: float = Field(
        default=100.0, description="Max amount for auto approval"
    )
    require_human_escalation_amount: float = Field(
        default=500.0, description="Threshold requiring supervisor escalation"
    )
    high_risk_return_rate_threshold: float = Field(
        default=0.40, description="Customer return rate fraud threshold"
    )
    excessive_refunds_count_threshold: int = Field(
        default=3, description="Threshold for previous refund counts"
    )
    rapid_repeat_claims_window_hours: int = Field(
        default=48, description="Time window for rapid repeat checks"
    )


class CategoryRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    eligible_categories: list[str] = Field(default_factory=list)
    non_refundable_categories: list[str] = Field(default_factory=list)


class PolicyRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule human-readable name")
    description: str = Field(..., description="Rule description")
    condition: str = Field(..., description="Boolean rule condition expression")
    action: DecisionType | None = Field(
        default=None, description="Action taken when condition is met"
    )
    violation_action: DecisionType | None = Field(
        default=None, description="Action taken when condition is violated"
    )
    exception: str | None = Field(default=None, description="Exceptions to the rule")
    citation: str = Field(..., description="Formal policy citation")


class RedFlag(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique red flag identifier")
    name: str = Field(..., description="Red flag title")
    description: str = Field(..., description="Description of the risk pattern")
    condition: str = Field(..., description="Condition expression triggering the flag")
    risk_level: RiskLevel = Field(default="High", description="Severity risk level")
    action: DecisionType = Field(default="Escalated", description="Action taken when triggered")
    citation: str = Field(..., description="Formal fraud citation")


class PolicyDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str = Field(..., description="Policy version string")
    policy_name: str = Field(..., description="Official policy document name")
    last_updated: str = Field(..., description="ISO date of last policy modification")
    description: str = Field(default="", description="High level policy summary")
    general_rules: GeneralRules
    decision_types: list[DecisionType] = Field(
        default_factory=lambda: ["Approved", "Denied", "Escalated"]
    )
    categories: CategoryRules
    item_conditions: list[str] = Field(default_factory=list)
    rules: list[PolicyRule]
    red_flags: list[RedFlag]


class RuleEvaluationResult(BaseModel):
    preliminary_decision: DecisionType
    matched_rules: list[str] = Field(default_factory=list)
    triggered_red_flags: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    is_escalated: bool = False
    is_denied: bool = False
    is_approved: bool = False
