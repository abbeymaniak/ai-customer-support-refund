import { describe, it, expect } from 'vitest';
import { apiClient } from './client';

describe('apiClient', () => {
  it('is configured with default JSON headers and timeout', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
    expect(apiClient.defaults.timeout).toBe(30000);
  });

  it('rejects with detail message from response error when present', async () => {
    const errorResponse = {
      response: {
        data: { detail: 'Customer account not found' },
        status: 404,
      },
    };

    // Find response error interceptor handler
    const handlers = (
      apiClient.interceptors.response as unknown as {
        handlers: Array<{ rejected: (err: unknown) => Promise<never> }>;
      }
    ).handlers;
    const responseInterceptor = handlers[0];
    await expect(responseInterceptor.rejected(errorResponse)).rejects.toThrow(
      'Customer account not found'
    );
  });

  it('rejects with generic error message when response detail is absent', async () => {
    const genericError = {
      message: 'Network Timeout',
    };

    const handlers = (
      apiClient.interceptors.response as unknown as {
        handlers: Array<{ rejected: (err: unknown) => Promise<never> }>;
      }
    ).handlers;
    const responseInterceptor = handlers[0];
    await expect(responseInterceptor.rejected(genericError)).rejects.toThrow('Network Timeout');
  });
});
