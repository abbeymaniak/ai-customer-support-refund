"""Administrative API endpoints for managing LLM provider settings."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.llm_setting import (
    LLMProviderResponse,
    LLMProviderUpdatePayload,
    LLMTestProbePayload,
    LLTestProbeResponse,
)
from app.services.llm_settings_service import LLMSettingsService, provider_to_response

router = APIRouter()


@router.get(
    "/llm",
    response_model=list[LLMProviderResponse],
    summary="List all LLM provider settings",
    description="Retrieve all configured language model providers with masked API keys and active status.",
)
async def list_llm_providers(
    db: AsyncSession = Depends(get_db),
) -> list[LLMProviderResponse]:
    service = LLMSettingsService(db)
    return await service.list_providers()


@router.get(
    "/llm/active",
    response_model=LLMProviderResponse,
    summary="Get currently active LLM provider",
    description="Retrieve the provider currently engaged for automated refund evaluations.",
)
async def get_active_llm_provider(
    db: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    service = LLMSettingsService(db)
    active = await service.get_active_provider()
    if not active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active LLM provider configured.",
        )
    return provider_to_response(active)


@router.put(
    "/llm/{provider}",
    response_model=LLMProviderResponse,
    summary="Update LLM provider settings",
    description="Update model selection, credentials, parameters, or active status for a specific provider.",
)
async def update_llm_provider(
    provider: str,
    payload: LLMProviderUpdatePayload,
    db: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    service = LLMSettingsService(db)
    try:
        return await service.update_provider(provider, payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        ) from val_err


@router.post(
    "/llm/{provider}/activate",
    response_model=LLMProviderResponse,
    summary="Activate LLM provider",
    description="Set the specified provider as active and deactivate all other providers.",
)
async def activate_llm_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    service = LLMSettingsService(db)
    try:
        return await service.activate_provider(provider)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        ) from val_err


@router.post(
    "/llm/test",
    response_model=LLTestProbeResponse,
    summary="Test LLM provider connection",
    description="Send a lightweight probe prompt to verify connectivity and latency for a target provider.",
)
async def test_llm_connection(
    payload: LLMTestProbePayload,
    db: AsyncSession = Depends(get_db),
) -> LLTestProbeResponse:
    service = LLMSettingsService(db)
    return await service.probe_provider_connection(payload)
