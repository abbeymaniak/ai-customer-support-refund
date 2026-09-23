import { apiClient } from './client';
import type {
  LLMProvider,
  LLMProviderUpdatePayload,
  LLMTestProbePayload,
  LLMTestProbeResponse,
} from '../types';

export const fetchLLMProviders = async (): Promise<LLMProvider[]> => {
  const response = await apiClient.get<LLMProvider[]>('/admin/settings/llm');
  return response.data;
};

export const fetchActiveLLMProvider = async (): Promise<LLMProvider> => {
  const response = await apiClient.get<LLMProvider>('/admin/settings/llm/active');
  return response.data;
};

export const updateLLMProvider = async (
  provider: string,
  payload: LLMProviderUpdatePayload
): Promise<LLMProvider> => {
  const response = await apiClient.put<LLMProvider>(`/admin/settings/llm/${provider}`, payload);
  return response.data;
};

export const activateLLMProvider = async (provider: string): Promise<LLMProvider> => {
  const response = await apiClient.post<LLMProvider>(`/admin/settings/llm/${provider}/activate`);
  return response.data;
};

export const testLLMConnection = async (
  payload: LLMTestProbePayload
): Promise<LLMTestProbeResponse> => {
  const response = await apiClient.post<LLMTestProbeResponse>('/admin/settings/llm/test', payload);
  return response.data;
};
