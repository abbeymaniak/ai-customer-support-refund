"""Service layer for managing LLM provider configurations and connectivity probes."""

import time
from typing import Any

import litellm
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_provider import LLMProvider
from app.schemas.llm_setting import (
    LLMProviderResponse,
    LLMProviderUpdatePayload,
    LLMTestProbePayload,
    LLTestProbeResponse,
)

logger = structlog.get_logger()


def mask_api_key(api_key: str | None) -> str | None:
    """Return a masked representation of an API key showing only the last four characters."""
    if not api_key:
        return None
    cleaned = api_key.strip()
    if len(cleaned) <= 4:
        return "••••"
    return f"••••••••{cleaned[-4:]}"


def provider_to_response(provider: LLMProvider) -> LLMProviderResponse:
    """Convert an LLMProvider ORM instance to public LLMProviderResponse."""
    has_key = bool(provider.api_key and provider.api_key.strip())
    masked_key = mask_api_key(provider.api_key)

    return LLMProviderResponse(
        id=provider.id,
        llm=provider.llm,
        is_active=provider.is_active,
        llm_model=provider.llm_model,
        has_api_key=has_key,
        api_key_masked=masked_key,
        api_base=provider.api_base,
        temperature=provider.temperature,
        timeout_seconds=provider.timeout_seconds,
        updated_by=provider.updated_by,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


class LLMSettingsService:
    """Encapsulates database operations and connection probes for LLM provider settings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_providers(self) -> list[LLMProviderResponse]:
        """Return all configured LLM providers sorted by name."""
        stmt = select(LLMProvider).order_by(LLMProvider.llm.asc())
        result = await self.db.execute(stmt)
        providers = result.scalars().all()
        return [provider_to_response(p) for p in providers]

    async def get_active_provider(self) -> LLMProvider | None:
        """Return the currently active LLM provider."""
        stmt = select(LLMProvider).where(LLMProvider.is_active.is_(True))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_provider_by_name(self, llm: str) -> LLMProvider | None:
        """Find a provider record by provider name."""
        stmt = select(LLMProvider).where(LLMProvider.llm == llm.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_provider(
        self,
        llm: str,
        payload: LLMProviderUpdatePayload,
        updated_by: str = "admin",
    ) -> LLMProviderResponse:
        """Update provider settings and optionally set active status."""
        provider = await self.get_provider_by_name(llm)
        if not provider:
            raise ValueError(f"LLM provider '{llm}' not found.")

        # If activating this provider, deactivate all other providers first
        if payload.is_active is True:
            await self.db.execute(update(LLMProvider).values(is_active=False))
            provider.is_active = True
        elif payload.is_active is False:
            provider.is_active = False

        if payload.llm_model is not None:
            provider.llm_model = payload.llm_model.strip()

        if payload.api_key is not None:
            cleaned_key = payload.api_key.strip()
            provider.api_key = cleaned_key if cleaned_key else None

        if payload.api_base is not None:
            cleaned_base = payload.api_base.strip()
            provider.api_base = cleaned_base if cleaned_base else None

        if payload.temperature is not None:
            provider.temperature = payload.temperature

        if payload.timeout_seconds is not None:
            provider.timeout_seconds = payload.timeout_seconds

        provider.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(provider)

        logger.info(
            "llm_provider_settings_updated",
            llm=provider.llm,
            model=provider.llm_model,
            is_active=provider.is_active,
            updated_by=updated_by,
        )

        return provider_to_response(provider)

    async def activate_provider(
        self,
        llm: str,
        updated_by: str = "admin",
    ) -> LLMProviderResponse:
        """Activate the specified provider and deactivate all others."""
        provider = await self.get_provider_by_name(llm)
        if not provider:
            raise ValueError(f"LLM provider '{llm}' not found.")

        await self.db.execute(update(LLMProvider).values(is_active=False))
        provider.is_active = True
        provider.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(provider)

        logger.info("llm_provider_activated", llm=provider.llm, updated_by=updated_by)
        return provider_to_response(provider)

    async def probe_provider_connection(
        self,
        payload: LLMTestProbePayload,
    ) -> LLTestProbeResponse:
        """Send a lightweight prompt to test communication with a provider."""
        provider_name = payload.llm.lower().strip()
        db_provider = await self.get_provider_by_name(provider_name)

        model_name = payload.llm_model or (db_provider.llm_model if db_provider else None)
        api_key = payload.api_key or (db_provider.api_key if db_provider else None)
        api_base = payload.api_base or (db_provider.api_base if db_provider else None)

        if not model_name:
            if provider_name == "openai":
                model_name = "gpt-4o-mini"
            elif provider_name == "ollama":
                model_name = "llama3"
            elif provider_name == "gemini":
                model_name = "gemini-1.5-flash"
            else:
                model_name = "default"

        # Format full LiteLLM model identifier
        if "/" not in model_name:
            full_model = f"{provider_name}/{model_name}"
        else:
            full_model = model_name

        if provider_name == "ollama" and not api_base:
            api_base = "http://host.docker.internal:11434"

        start_time = time.perf_counter()
        try:
            kwargs: dict[str, Any] = {
                "model": full_model,
                "messages": [
                    {"role": "user", "content": "Return valid JSON with key status set to healthy."}
                ],
                "timeout": 10.0,
                "temperature": 0.0,
            }
            if api_key:
                kwargs["api_key"] = api_key
            if api_base:
                kwargs["api_base"] = api_base

            await litellm.acompletion(**kwargs)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            return LLTestProbeResponse(
                llm=provider_name,
                llm_model=model_name,
                status="online",
                latency_ms=latency_ms,
                message=f"Successfully connected to {provider_name} ({model_name}) in {latency_ms}ms.",
                error=None,
            )
        except Exception as probe_err:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(
                "llm_probe_failed",
                provider=provider_name,
                model=model_name,
                error=str(probe_err),
            )
            return LLTestProbeResponse(
                llm=provider_name,
                llm_model=model_name,
                status="offline",
                latency_ms=latency_ms,
                message=f"Failed to communicate with {provider_name} ({model_name}).",
                error=str(probe_err),
            )
