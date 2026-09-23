"""AI decision engine using LiteLLM for multi-provider support."""

import json
from typing import Any

import litellm
import structlog

from app.ai.prompts import REFUND_EVALUATION_SYSTEM_PROMPT
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

    async def evaluate_refund_request(
        self,
        customer_info: dict[str, Any],
        order_info: dict[str, Any],
        request_info: dict[str, Any],
        policy_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate a refund request against policy using LLM."""
        if not settings.openai_api_key and "mock" not in self.primary_model.lower():
            logger.warning("llm_api_key_missing", primary_model=self.primary_model)
            raise AIProviderError("OpenAI API key is not configured; AI evaluation unavailable.")

        user_content = json.dumps(
            {
                "customer": customer_info,
                "order": order_info,
                "refund_request": request_info,
                "policy_context": policy_info,
            },
            indent=2,
        )

        messages = [
            {"role": "system", "content": REFUND_EVALUATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Please evaluate this customer refund claim against store policy:\n{user_content}",
            },
        ]

        # 1. Attempt Primary Provider
        try:
            response = await litellm.acompletion(
                model=self.primary_model,
                messages=messages,
                response_format={"type": "json_object"},
                timeout=12.0,
                api_key=settings.openai_api_key,
            )
            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text)
            return self._normalize_ai_response(parsed, provider=self.primary_model)
        except Exception as primary_err:
            logger.warning(
                "primary_llm_evaluation_failed",
                model=self.primary_model,
                error=str(primary_err),
            )

        # 2. Attempt Fallback Provider if configured
        if self.fallback_model:
            try:
                response = await litellm.acompletion(
                    model=self.fallback_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    timeout=15.0,
                    api_base=settings.ollama_api_base if "ollama" in self.fallback_model else None,
                )
                raw_text = response.choices[0].message.content
                parsed = json.loads(raw_text)
                return self._normalize_ai_response(parsed, provider=self.fallback_model)
            except Exception as fallback_err:
                logger.warning(
                    "fallback_llm_evaluation_failed",
                    model=self.fallback_model,
                    error=str(fallback_err),
                )

        raise AIProviderError("All configured AI evaluation providers failed or timed out.")

    def _normalize_ai_response(self, raw: dict[str, Any], provider: str) -> dict[str, Any]:
        """Normalize and validate LLM output into expected format."""
        raw_decision = str(raw.get("decision", "Escalated")).capitalize()
        if raw_decision not in ["Approved", "Denied", "Escalated"]:
            raw_decision = "Escalated"

        confidence = raw.get("confidence_score", 0.8)
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (ValueError, TypeError):
            confidence = 0.5

        explanation = raw.get("explanation") or raw.get("reasoning") or "Evaluated against policy."
        citations = raw.get("policy_citations") or raw.get("matched_rules") or []
        if isinstance(citations, str):
            citations = [citations]

        return {
            "decision": raw_decision,
            "confidence_score": confidence,
            "explanation": str(explanation),
            "policy_citations": citations,
            "provider": provider,
        }
