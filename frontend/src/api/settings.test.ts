import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchLLMProviders,
  fetchActiveLLMProvider,
  updateLLMProvider,
  activateLLMProvider,
  testLLMConnection,
} from './settings';
import { apiClient } from './client';

describe('settings api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetchLLMProviders sends get request to admin settings llm endpoint', async () => {
    const mockProviders = [
      {
        id: 'prov-1',
        llm: 'ollama',
        llm_model: 'llama3',
        is_active: true,
        api_base: 'http://host.docker.internal:11434',
        has_api_key: false,
        api_key_masked: null,
        temperature: 0.1,
        timeout_seconds: 30,
        created_at: '2026-09-23T00:00:00',
        updated_at: '2026-09-23T00:00:00',
      },
    ];

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockProviders });

    const result = await fetchLLMProviders();
    expect(getSpy).toHaveBeenCalledWith('/admin/settings/llm');
    expect(result).toEqual(mockProviders);
  });

  it('fetchActiveLLMProvider sends get request to active endpoint', async () => {
    const mockActive = {
      id: 'prov-1',
      llm: 'ollama',
      llm_model: 'llama3',
      is_active: true,
      api_base: 'http://host.docker.internal:11434',
      has_api_key: false,
      api_key_masked: null,
      temperature: 0.1,
      timeout_seconds: 30,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockActive });

    const result = await fetchActiveLLMProvider();
    expect(getSpy).toHaveBeenCalledWith('/admin/settings/llm/active');
    expect(result).toEqual(mockActive);
  });

  it('updateLLMProvider sends put request with update payload', async () => {
    const payload = {
      llm_model: 'qwen2.5',
      temperature: 0.2,
      timeout_seconds: 45,
    };

    const mockResponse = {
      id: 'prov-1',
      llm: 'ollama',
      llm_model: 'qwen2.5',
      is_active: true,
      api_base: 'http://host.docker.internal:11434',
      has_api_key: false,
      api_key_masked: null,
      temperature: 0.2,
      timeout_seconds: 45,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    };

    const putSpy = vi.spyOn(apiClient, 'put').mockResolvedValueOnce({ data: mockResponse });

    const result = await updateLLMProvider('ollama', payload);
    expect(putSpy).toHaveBeenCalledWith('/admin/settings/llm/ollama', payload);
    expect(result).toEqual(mockResponse);
  });

  it('activateLLMProvider sends post request to provider activate endpoint', async () => {
    const mockResponse = {
      id: 'prov-2',
      llm: 'openai',
      llm_model: 'gpt-4o-mini',
      is_active: true,
      api_base: null,
      has_api_key: true,
      api_key_masked: 'sk-...4321',
      temperature: 0.1,
      timeout_seconds: 30,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockResponse });

    const result = await activateLLMProvider('openai');
    expect(postSpy).toHaveBeenCalledWith('/admin/settings/llm/openai/activate');
    expect(result).toEqual(mockResponse);
  });

  it('testLLMConnection sends probe test payload to probe endpoint', async () => {
    const probePayload = {
      llm: 'ollama',
      llm_model: 'llama3',
      api_base: 'http://host.docker.internal:11434',
    };

    const mockProbeResult = {
      llm: 'ollama',
      llm_model: 'llama3',
      status: 'online',
      latency_ms: 245,
      message: 'Provider probe succeeded',
      error: null,
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockProbeResult });

    const result = await testLLMConnection(probePayload);
    expect(postSpy).toHaveBeenCalledWith('/admin/settings/llm/test', probePayload);
    expect(result).toEqual(mockProbeResult);
  });
});
