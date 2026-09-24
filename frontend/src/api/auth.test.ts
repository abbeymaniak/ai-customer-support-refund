import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authApi } from './auth';
import { apiClient } from './client';

describe('authApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('login sends credentials and returns admin user', async () => {
    const mockUser = {
      id: 'admin-uuid',
      email: 'admin@store.com',
      name: 'Store Administrator',
      role: 'admin',
      is_active: true,
      created_at: '2026-09-24T12:00:00Z',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockUser });

    const result = await authApi.login({
      email: 'admin@store.com',
      password: 'admin123',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
      email: 'admin@store.com',
      password: 'admin123',
    });
    expect(result).toEqual(mockUser);
  });

  it('refresh calls /auth/refresh and returns status', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      data: { status: 'refreshed', message: 'Session renewed' },
    });

    const result = await authApi.refresh();
    expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh');
    expect(result.status).toBe('refreshed');
  });

  it('logout calls /auth/logout and returns status', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      data: { status: 'logged_out', message: 'Logged out' },
    });

    const result = await authApi.logout();
    expect(apiClient.post).toHaveBeenCalledWith('/auth/logout');
    expect(result.status).toBe('logged_out');
  });

  it('getMe calls /auth/me and returns active user profile', async () => {
    const mockUser = {
      id: 'lead-uuid',
      email: 'lead@store.com',
      name: 'Support Lead',
      role: 'agent',
      is_active: true,
      created_at: '2026-09-24T12:00:00Z',
    };

    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockUser });

    const result = await authApi.getMe();
    expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
    expect(result.role).toBe('agent');
  });

  it('login throws error on rejected credentials', async () => {
    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('Invalid email or password')
    );

    await expect(
      authApi.login({ email: 'bad@store.com', password: 'wrong' })
    ).rejects.toThrow('Invalid email or password');
  });

  it('refresh throws error when session cannot be renewed', async () => {
    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('Session expired')
    );

    await expect(authApi.refresh()).rejects.toThrow('Session expired');
  });
});
