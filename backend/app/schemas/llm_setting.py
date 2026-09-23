"""Pydantic schemas for LLM provider settings and connection test probes."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LLMProviderResponse(BaseModel):
    """Public representation of an LLM provider configuration with masked credential."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    llm: str = Field(..., description="Provider identifier: openai, ollama, gemini")
    is_active: bool = Field(..., description="Whether this provider is currently active")
    llm_model: str = Field(..., description="Selected model name")
    has_api_key: bool = Field(..., description="Whether an API key is currently stored")
    api_key_masked: str | None = Field(
        None, description="Masked API key showing only the last four characters"
    )
    api_base: str | None = Field(None, description="Custom API endpoint base URL")
    temperature: float = Field(default=0.0, description="Model sampling temperature")
    timeout_seconds: float = Field(default=3.0, description="Model request timeout")
    updated_by: str | None = Field(None, description="Identifier of last editor")
    created_at: datetime
    updated_at: datetime


class LLMProviderUpdatePayload(BaseModel):
    """Payload for updating an LLM provider configuration."""

    llm_model: str | None = Field(None, description="Model identifier to use")
    api_key: str | None = Field(
        None, description="New API key (omit or null to leave unchanged)"
    )
    api_base: str | None = Field(
        None, description="Custom API endpoint base URL"
    )
    is_active: bool | None = Field(
        None, description="Set this provider as active"
    )
    temperature: float | None = Field(
        None, ge=0.0, le=2.0, description="Sampling temperature"
    )
    timeout_seconds: float | None = Field(
        None, ge=1.0, le=60.0, description="Request timeout in seconds"
    )


class LLMTestProbePayload(BaseModel):
    """Payload to test communication with an LLM provider before saving or activating."""

    llm: str = Field(..., description="Provider identifier: openai, ollama, gemini")
    llm_model: str | None = Field(None, description="Model to test")
    api_key: str | None = Field(None, description="API key to test (uses saved key if omitted)")
    api_base: str | None = Field(None, description="API base URL to test (uses saved base if omitted)")


class LLTestProbeResponse(BaseModel):
    """Result of an LLM provider connectivity probe."""

    llm: str
    llm_model: str
    status: str = Field(..., description="Connectivity status: online or offline")
    latency_ms: int = Field(..., description="Round trip probe latency in milliseconds")
    message: str = Field(..., description="Human readable probe outcome description")
    error: str | None = Field(None, description="Error detail if probe failed")
