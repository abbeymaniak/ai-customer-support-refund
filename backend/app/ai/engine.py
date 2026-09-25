"""AI decision engine using LiteLLM with dynamic database-backed provider resolution."""

import json
import time
from typing import Any

import litellm
import structlog
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import build_evaluation_prompt
from app.ai.schemas import AIOutputSchema, RefundEvaluationContext
from app.config import settings

logger = structlog.get_logger()


class AIProviderError(Exception):
    """Exception raised when an AI provider fails, times out, or has invalid credentials."""

    pass


class AIDecisionEngine:
    """Wrapper around LiteLLM providing dynamic database-driven provider selection."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db
        self.primary_model = settings.llm_provider
        self.fallback_model = settings.llm_fallback_provider
        self.timeout_seconds = getattr(settings, "llm_timeout_seconds", 3.0)
        self.temperature = getattr(settings, "llm_temperature", 0.0)

    async def _resolve_active_provider(self) -> dict[str, Any]:
        """Dynamically load the currently active provider from the database."""
        try:
            from app.database import async_session
            from app.models.llm_provider import LLMProvider

            if self.db:
                stmt = select(LLMProvider).where(LLMProvider.is_active.is_(True))
                result = await self.db.execute(stmt)
                active = result.scalars().first()
                if active:
                    return {
                        "llm": active.llm,
                        "llm_model": active.llm_model,
                        "api_key": active.api_key,
                        "api_base": active.api_base,
                        "temperature": active.temperature,
                        "timeout_seconds": active.timeout_seconds,
                    }
            else:
                async with async_session() as session:
                    stmt = select(LLMProvider).where(LLMProvider.is_active.is_(True))
                    result = await session.execute(stmt)
                    active = result.scalars().first()
                    if active:
                        return {
                            "llm": active.llm,
                            "llm_model": active.llm_model,
                            "api_key": active.api_key,
                            "api_base": active.api_base,
                            "temperature": active.temperature,
                            "timeout_seconds": active.timeout_seconds,
                        }
        except Exception as db_err:
            logger.warning(
                "active_llm_provider_lookup_failed_using_settings_default",
                error=str(db_err),
            )

        # Fallback to static settings if database is not reachable
        return {
            "llm": "ollama" if "ollama" in self.primary_model else "openai",
            "llm_model": self.primary_model.split("/")[-1]
            if "/" in self.primary_model
            else self.primary_model,
            "api_key": settings.openai_api_key,
            "api_base": settings.ollama_api_base if "ollama" in self.primary_model else None,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
        }

    async def evaluate_refund_request(
        self,
        customer_info: dict[str, Any],
        order_info: dict[str, Any],
        request_info: dict[str, Any],
        policy_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate a refund request against policy using the active LLM provider."""
        context = RefundEvaluationContext(
            customer=customer_info,
            order=order_info,
            refund_item=request_info,
            reason_category=request_info.get("reason_category", "other"),
            customer_explanation=request_info.get("customer_explanation", ""),
            policy_rules=policy_info.get("rules", []),
        )

        # Handle mock mode for deterministic test suites
        if "mock" in self.primary_model.lower():
            return self._generate_mock_evaluation(context)

        active = await self._resolve_active_provider()
        provider_name = active["llm"].lower().strip()
        model_name = active["llm_model"].strip()
        api_key = active.get("api_key")
        api_base = active.get("api_base")
        temperature = active.get("temperature", 0.0)
        timeout_seconds = active.get("timeout_seconds", 3.0)

        # Build full model identifier for LiteLLM
        if "/" not in model_name:
            full_model = f"{provider_name}/{model_name}"
        else:
            full_model = model_name

        if provider_name == "ollama" and not api_base:
            api_base = "http://host.docker.internal:11434"

        # Check API key requirement for cloud providers
        if provider_name in ("openai", "gemini") and not api_key:
            if provider_name == "openai" and settings.openai_api_key:
                api_key = settings.openai_api_key
            else:
                logger.warning(
                    "active_provider_missing_credentials_escalating",
                    provider=provider_name,
                    model=model_name,
                )
                raise AIProviderError(
                    f"{provider_name.capitalize()} API key is not configured; claim escalated to human review."
                )

        messages = build_evaluation_prompt(context)
        start_time = time.perf_counter()

        try:
            kwargs: dict[str, Any] = {
                "model": full_model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "timeout": timeout_seconds,
                "temperature": temperature,
            }
            if api_key:
                kwargs["api_key"] = api_key
            if api_base:
                kwargs["api_base"] = api_base

            response = await litellm.acompletion(**kwargs)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raw_text = response.choices[0].message.content
            tokens = {
                "prompt": getattr(response.usage, "prompt_tokens", 0)
                if hasattr(response, "usage")
                else 0,
                "completion": getattr(response.usage, "completion_tokens", 0)
                if hasattr(response, "usage")
                else 0,
                "total": getattr(response.usage, "total_tokens", 0)
                if hasattr(response, "usage")
                else 0,
            }

            return self._parse_and_validate_response(
                raw_text=raw_text,
                provider=full_model,
                latency_ms=latency_ms,
                tokens=tokens,
            )

        except Exception as eval_err:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(
                "active_llm_evaluation_failed_escalating_to_human",
                provider=full_model,
                error=str(eval_err),
            )
            # Direct escalation to human review if active model fails (AC-5)
            raise AIProviderError(
                f"Active model ({full_model}) evaluation failed: {str(eval_err)}"
            ) from eval_err

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
            logger.error(
                "llm_response_schema_validation_failed", error=str(parse_err), raw=raw_text
            )
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
