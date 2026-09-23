"""Unit and integration tests for admin LLM provider settings API and service."""

import pytest

from app.services.llm_settings_service import mask_api_key


def test_mask_api_key_helper():
    """Test API key masking logic."""
    assert mask_api_key(None) is None
    assert mask_api_key("") is None
    assert mask_api_key("1234") == "••••"
    assert mask_api_key("sk-test-secret-key-1234567890") == "••••••••7890"


@pytest.mark.asyncio
async def test_list_and_get_active_llm_providers(async_client):
    """Test AC-1, AC-2: List all providers and retrieve the active provider."""
    # 1. List all providers
    res = await async_client.get("/api/admin/settings/llm")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 3
    names = [p["llm"] for p in providers]
    assert "ollama" in names
    assert "openai" in names
    assert "gemini" in names

    # 2. Get active provider
    active_res = await async_client.get("/api/admin/settings/llm/active")
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data["is_active"] is True
    assert "llm_model" in active_data


@pytest.mark.asyncio
async def test_update_and_activate_provider(async_client):
    """Test AC-2: Update provider credentials and activate provider."""
    # 1. Update OpenAI settings with a test key
    update_res = await async_client.put(
        "/api/admin/settings/llm/openai",
        json={
            "llm_model": "gpt-4o",
            "api_key": "sk-proj-supersecret9988",
            "temperature": 0.2,
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["llm"] == "openai"
    assert updated["llm_model"] == "gpt-4o"
    assert updated["has_api_key"] is True
    assert updated["api_key_masked"] == "••••••••9988"
    assert updated["temperature"] == 0.2

    # 2. Activate OpenAI
    act_res = await async_client.post("/api/admin/settings/llm/openai/activate")
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["llm"] == "openai"
    assert act_data["is_active"] is True

    # 3. Confirm Ollama is now deactivated
    list_res = await async_client.get("/api/admin/settings/llm")
    providers = list_res.json()
    ollama = next(p for p in providers if p["llm"] == "ollama")
    assert ollama["is_active"] is False

    # Switch back to ollama for clean environment state
    await async_client.post("/api/admin/settings/llm/ollama/activate")


@pytest.mark.asyncio
async def test_test_probe_endpoint(async_client):
    """Test AC-3: Connection test probe returns structured status and latency."""
    probe_res = await async_client.post(
        "/api/admin/settings/llm/test",
        json={
            "llm": "ollama",
            "llm_model": "llama3",
            "api_base": "http://127.0.0.1:59999",  # unreachable port
        },
    )
    assert probe_res.status_code == 200
    probe_data = probe_res.json()
    assert probe_data["status"] == "offline"
    assert probe_data["error"] is not None
    assert "Failed to communicate" in probe_data["message"]
