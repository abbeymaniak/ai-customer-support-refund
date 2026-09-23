"""AI decision engine using LiteLLM for multi-provider support."""

import json
import time
from typing import Any

import litellm
import structlog
from pydantic import ValidationError

from app.ai.prompts import build_evaluation_prompt
from app.ai.schemas import AIOutputSchema, RefundEvaluationContext
from app.config import settings

logger = structlog.get_logger()


class AIProviderError(Exception):
    """Exception raised when all configured AI providers fail or are unreachable."""

    pass


class AIDecisionEngine:
    """Wrapper around LiteLLM providing multi-provider LLM access with fallback."""

    def __init__(self) -> None:
        self.primary_model = settings.llm_provider
        self.fallback_model = settings.llm_fallback_provider
        self.timeout_seconds = getattr(settings, "llm_timeout_seconds", 3.0)
        self.temperature = getattr(settings, "llm_temperature", 0.0)

    async def evaluate_refund_request(
        self,
        customer_info: dict[str, Any],
        order_info: dict[str, Any],
        request_info: dict[str, Any],
        policy_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate a refund request against policy using LLM."""
        context = RefundEvaluationContext(
            customer=customer_info,
            order=order_info,
            refund_item=request_info,
            reason_category=request_info.get("reason_category", "other"),
            customer_explanation=request_info.get("customer_explanation", ""),
            policy_rules=policy_info.get("rules", []),
        )

        messages = build_evaluation_prompt(context)

        # Handle mock mode or unconfigured API key
        if "mock" in self.primary_model.lower() or (
            not settings.openai_api_key and "mock" not in (self.fallback_model or "").lower()
        ):
            if not settings.openai_api_key and "mock" not in self.primary_model.lower():
                logger.info("llm_api_key_missing_using_deterministic_fallback", model=self.primary_model)
                raise AIProviderError("OpenAI API key is not configured; AI evaluation unavailable.")
            return self._generate_mock_evaluation(context)

        # 1. Primary Provider with single retry (AC-5)
        for attempt in range(2):
            start_time = time.perf_counter()
            try:
                response = await litellm.acompletion(
                    model=self.primary_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    timeout=self.timeout_seconds,
                    temperature=self.temperature,
                    api_key=settings.openai_api_key,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                raw_text = response.choices[0].message.content
                tokens = {
                    "prompt": getattr(response.usage, "prompt_tokens", 0) if hasattr(response, "usage") else 0,
                    "completion": getattr(response.usage, "completion_tokens", 0) if hasattr(response, "usage") else 0,
                    "total": getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0,
                }
                return self._parse_and_validate_response(
                    raw_text=raw_text,
                    provider=self.primary_model,
                    latency_ms=latency_ms,
                    tokens=tokens,
                )
            except Exception as primary_err:
                logger.warning(
                    "primary_llm_attempt_failed",
                    attempt=attempt + 1,
                    model=self.primary_model,
                    error=str(primary_err),
                )
                if attempt == 0:
                    continue

        # 2. Secondary / Fallback Provider (AC-5)
        if self.fallback_model:
            start_time = time.perf_counter()
            try:
                response = await litellm.acompletion(
                    model=self.fallback_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    timeout=self.timeout_seconds * 1.5,
                    temperature=self.temperature,
                    api_base=settings.ollama_api_base if "ollama" in self.fallback_model else None,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                raw_text = response.choices[0].message.content
                tokens = {
                    "prompt": getattr(response.usage, "prompt_tokens", 0) if hasattr(response, "usage") else 0,
                    "completion": getattr(response.usage, "completion_tokens", 0) if hasattr(response, "usage") else 0,
                    "total": getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0,
                }
                return self._parse_and_validate_response(
                    raw_text=raw_text,
                    provider=self.fallback_model,
                    latency_ms=latency_ms,
                    tokens=tokens,
                )
            except Exception as fallback_err:
                logger.warning(
                    "fallback_llm_evaluation_failed",
                    model=self.fallback_model,
                    error=str(fallback_err),
                )

        raise AIProviderError("All configured AI evaluation providers failed or timed out.")

    def _parse_and_validate_response(
        self,
        raw_text: str,
        provider: str,
        latency_ms: int,
        tokens: dict[str, int],
    ) -> dict[str, Any]:
        """Validate LLM output against Pydantic schema with graceful recovery (AC-1, AC-6)."""
        try:
            parsed_json = json.loads(raw_text)
            schema = AIOutputSchema.model_validate(parsed_json)
            result = schema.model_dump()
            result["provider"] = provider
            result["telemetry"] = {
                "provider": provider,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "raw_response": parsed_json,
                "fallback": False,
            }
            return result
        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.error("llm_response_schema_validation_failed", error=str(parse_err), raw=raw_text)
            # Safe recovery: escalate claim to human support without service crash (AC-6)
            return {
                "decision": "Escalated",
                "confidence_score": 0.5,
                "explanation": "Your request has been routed to human support for review due to automated processing recovery.",
                "policy_citations": ["Refund Policy § 2.1 (Manager Escalation Thresholds)"],
                "matched_rules": ["RULE_SCHEMA_PARSE_RECOVERY"],
                "audit_notes": f"Model output schema validation failed: {str(parse_err)}",
                "suggested_action": "supervisor_review",
                "provider": provider,
                "telemetry": {
                    "provider": provider,
                    "latency_ms": latency_ms,
                    "tokens": tokens,
                    "raw_response": {"raw_text": raw_text[:500]},
                    "fallback": True,
                    "schema_error": str(parse_err),
                },
            }

    def _generate_mock_evaluation(self, context: RefundEvaluationContext) -> dict[str, Any]:
        """Generate deterministic evaluation for mock mode and test runs."""
        item = context.refund_item
        price = float(item.get("price", 0.0))
        quantity = int(item.get("quantity", 1))
        total_amount = price * quantity

        if item.get("is_final_sale"):
            decision = "Denied"
            confidence = 1.0
            explanation = "Item marked as final sale and cannot be refunded per store policy."
            matched_rules = ["RULE_FINAL_SALE"]
            citations = ["Refund Policy § 1.3 (Final Sale Exclusions)"]
        elif total_amount > 500.0:
            decision = "Escalated"
            confidence = 0.5
            explanation = f"Refund total (${total_amount:.2f}) exceeds human supervisor escalation threshold ($500.00)."
            matched_rules = ["RULE_HIGH_VALUE_ESCALATION"]
            citations = ["Refund Policy § 2.1 (Manager Escalation Thresholds)"]
        else:
            decision = "Approved"
            confidence = 0.95
            explanation = f"Return request for {item.get('product_name', 'item')} is approved within policy guidelines."
            matched_rules = ["RULE_STANDARD_RETURN_WINDOW"]
            citations = ["Refund Policy § 1.1 (Standard Return Window)"]

        return {
            "decision": decision,
            "confidence_score": confidence,
            "explanation": explanation,
            "policy_citations": citations,
            "matched_rules": matched_rules,
            "audit_notes": "Mock deterministic evaluation mode.",
            "suggested_action": "process_refund" if decision == "Approved" else "supervisor_review",
            "provider": "mock",
            "telemetry": {
                "provider": "mock",
                "latency_ms": 15,
                "tokens": {"prompt": 120, "completion": 45, "total": 165},
                "raw_response": {"mock": True},
                "fallback": False,
            },
        }
