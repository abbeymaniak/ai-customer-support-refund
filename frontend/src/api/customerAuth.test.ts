import { describe, it, expect, vi, beforeEach } from 'vitest';
import { customerAuthApi } from './customerAuth';
import { apiClient } from './client';
import type { CustomerUser, AuthStatusResponse } from '../types';

describe('customerAuthApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('login sends credentials and returns authenticated customer profile (covers: AC-3)', async () => {
    const mockCustomer: CustomerUser = {
      id: 'cust-sarah-123',
      email: 'sarah.jenkins@example.com',
      name: 'Sarah Jenkins',
      role: 'customer',
      is_active: true,
      orders_count: 18,
      refunds_count: 1,
      total_spent: 3250.5,
      return_rate: 0.05,
      risk_score: 0.12,
      created_at: '2026-01-01T00:00:00Z',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockCustomer });

    const result = await customerAuthApi.login({
      email: 'sarah.jenkins@example.com',
      password: 'customer123',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/customer/auth/login', {
      email: 'sarah.jenkins@example.com',
      password: 'customer123',
    });
    expect(result).toEqual(mockCustomer);
  });

  it('login throws error when credentials are rejected (covers: AC-3)', async () => {
    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('Invalid email or password')
    );

    await expect(
      customerAuthApi.login({ email: 'sarah.jenkins@example.com', password: 'wrong' })
    ).rejects.toThrow('Invalid email or password');
  });

  it('refresh requests session token rotation and returns status (covers: AC-3)', async () => {
    const mockStatus: AuthStatusResponse = {
      status: 'refreshed',
      message: 'Customer session refreshed successfully',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockStatus });

    const result = await customerAuthApi.refresh();

    expect(apiClient.post).toHaveBeenCalledWith('/customer/auth/refresh');
    expect(result.status).toBe('refreshed');
  });

  it('refresh throws error when refresh token is invalid or expired (covers: AC-3)', async () => {
    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('Invalid or expired refresh token')
    );

    await expect(customerAuthApi.refresh()).rejects.toThrow(
      'Invalid or expired refresh token'
    );
  });

  it('logout terminates active customer session (covers: AC-3, AC-7)', async () => {
    const mockStatus: AuthStatusResponse = {
      status: 'logged_out',
      message: 'Successfully logged out',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockStatus });

    const result = await customerAuthApi.logout();

    expect(apiClient.post).toHaveBeenCalledWith('/customer/auth/logout');
    expect(result.status).toBe('logged_out');
  });

  it('getMe retrieves current authenticated customer profile (covers: AC-4)', async () => {
    const mockCustomer: CustomerUser = {
      id: 'cust-sarah-123',
      email: 'sarah.jenkins@example.com',
      name: 'Sarah Jenkins',
      role: 'customer',
      is_active: true,
      orders_count: 18,
      refunds_count: 1,
      total_spent: 3250.5,
      return_rate: 0.05,
      risk_score: 0.12,
      created_at: '2026-01-01T00:00:00Z',
    };

    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockCustomer });

    const result = await customerAuthApi.getMe();

    expect(apiClient.get).toHaveBeenCalledWith('/customer/auth/me');
    expect(result).toEqual(mockCustomer);
  });

  it('getMe throws error when unauthenticated (covers: AC-4, AC-6)', async () => {
    vi.spyOn(apiClient, 'get').mockRejectedValueOnce(new Error('Customer authentication required'));

    await expect(customerAuthApi.getMe()).rejects.toThrow('Customer authentication required');
  });
});
