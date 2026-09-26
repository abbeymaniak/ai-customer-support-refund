import { describe, it, expect, vi, beforeEach } from 'vitest';
import { customerPortalApi } from './customerPortal';
import { apiClient } from './client';
import type { CustomerRefundClaimPayload, Order, RefundRequest } from '../types';

describe('customerPortalApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getMyOrders fetches customer scoped orders from /customer/orders (covers: AC-1)', async () => {
    const mockOrders: Order[] = [
      {
        id: 'ord-101',
        customer_id: 'cust-sarah-123',
        order_number: 'ORD-98721',
        order_date: '2026-09-10T12:00:00Z',
        total_amount: 149.99,
        currency: 'USD',
        status: 'delivered',
        items: [
          {
            id: 'item-201',
            name: 'Noise Cancelling Headphones',
            price: 99.99,
            category: 'Electronics',
            quantity: 1,
            is_final_sale: false,
            has_active_claim: false,
            claim_status: null,
          },
        ],
      },
    ];

    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockOrders });

    const result = await customerPortalApi.getMyOrders();

    expect(apiClient.get).toHaveBeenCalledWith('/customer/orders');
    expect(result).toEqual(mockOrders);
  });

  it('getMyOrders propagates rejection when unauthenticated (covers: AC-1, AC-6)', async () => {
    vi.spyOn(apiClient, 'get').mockRejectedValueOnce(new Error('Unauthorized'));

    await expect(customerPortalApi.getMyOrders()).rejects.toThrow('Unauthorized');
  });

  it('submitRefund sends claim payload without client customer id to /customer/refunds (covers: AC-2)', async () => {
    const payload: CustomerRefundClaimPayload = {
      order_id: 'ord-101',
      item_id: 'item-201',
      reason_category: 'defective',
      customer_explanation: 'The headphones no longer charge or turn on.',
      quantity: 1,
      item_condition: 'opened_used',
    };

    const mockResponse: RefundRequest = {
      id: 'claim-301',
      request_number: 'REF-PORTAL-001',
      customer_id: 'cust-sarah-123',
      order_id: 'ord-101',
      amount: 99.99,
      status: 'pending',
      decision: 'Approved',
      confidence_score: 0.95,
      reason_category: 'defective',
      customer_explanation: 'The headphones no longer charge or turn on.',
      created_at: '2026-09-25T14:00:00Z',
      updated_at: '2026-09-25T14:00:00Z',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockResponse });

    const result = await customerPortalApi.submitRefund(payload);

    expect(apiClient.post).toHaveBeenCalledWith('/customer/refunds', payload);
    expect(result).toEqual(mockResponse);
    expect(result.customer_id).toBe('cust-sarah-123');
  });

  it('submitRefund handles error rejection when order does not belong to customer (covers: AC-2)', async () => {
    const payload: CustomerRefundClaimPayload = {
      order_id: 'ord-david-999',
      item_id: 'item-david-888',
      reason_category: 'defective',
      customer_explanation: 'Attempting to claim refund for unauthorized order.',
      quantity: 1,
      item_condition: 'unopened',
    };

    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('Access denied: Order does not belong to the authenticated customer.')
    );

    await expect(customerPortalApi.submitRefund(payload)).rejects.toThrow(
      'Access denied: Order does not belong to the authenticated customer.'
    );
  });

  it('submitRefund handles duplicate claim rejection error (covers: AC-4)', async () => {
    const payload: CustomerRefundClaimPayload = {
      order_id: 'ord-101',
      item_id: 'item-202',
      reason_category: 'defective',
      customer_explanation: 'Attempting to claim already filed item.',
      quantity: 1,
      item_condition: 'opened_used',
    };

    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(
      new Error('A refund claim has already been filed for this item.')
    );

    await expect(customerPortalApi.submitRefund(payload)).rejects.toThrow(
      'A refund claim has already been filed for this item.'
    );
  });
});
