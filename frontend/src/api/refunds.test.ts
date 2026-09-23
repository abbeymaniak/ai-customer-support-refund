import { describe, it, expect, vi, beforeEach } from 'vitest';
import { refundApi } from './refunds';
import { apiClient } from './client';

describe('refundApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getCustomerByEmail queries customer lookup endpoint with encoded email', async () => {
    const mockCustomer = {
      id: 'cust-123',
      email: 'test@example.com',
      name: 'Test Customer',
      total_spent: 100,
      orders_count: 2,
      refunds_count: 0,
      return_rate: 0,
      risk_score: 0.1,
      account_created_at: '2026-01-01',
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockCustomer });

    const result = await refundApi.getCustomerByEmail('test+user@example.com');
    expect(getSpy).toHaveBeenCalledWith('/customers/lookup?email=test%2Buser%40example.com');
    expect(result).toEqual(mockCustomer);
  });

  it('getCustomerOrders queries customer orders endpoint', async () => {
    const mockOrders = [
      {
        id: 'ord-1',
        customer_id: 'cust-123',
        order_number: 'ORD-101',
        order_date: '2026-02-01',
        total_amount: 50,
        currency: 'USD',
        status: 'delivered',
        items: [],
      },
    ];

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockOrders });

    const result = await refundApi.getCustomerOrders('cust-123');
    expect(getSpy).toHaveBeenCalledWith('/customers/cust-123/orders');
    expect(result).toEqual(mockOrders);
  });

  it('submitRefundRequest posts payload to /refunds/process', async () => {
    const payload = {
      customer_email: 'test@example.com',
      order_number: 'ORD-101',
      item_id: 'item-1',
      amount: 45.0,
      reason_category: 'defective',
      customer_explanation: 'Broken on arrival',
    };

    const mockResponse = {
      id: 'ref-1',
      customer_id: 'cust-123',
      order_id: 'ord-1',
      amount: 45.0,
      currency: 'USD',
      reason_category: 'defective',
      customer_explanation: 'Broken on arrival',
      decision: 'Approved',
      confidence_score: 0.95,
      human_override: false,
      created_at: '2026-02-02',
      updated_at: '2026-02-02',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockResponse });

    const result = await refundApi.submitRefundRequest(payload);
    expect(postSpy).toHaveBeenCalledWith('/refunds/process', payload);
    expect(result).toEqual(mockResponse);
  });

  it('overrideDecision posts decision override to admin endpoint', async () => {
    const mockUpdated = {
      id: 'ref-1',
      decision: 'Approved',
      human_override: true,
      override_reason: 'Manager goodwill',
      override_by: 'lead@store.com',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockUpdated });

    const result = await refundApi.overrideDecision('ref-1', {
      decision: 'Approved',
      reason: 'Manager goodwill',
      actor: 'lead@store.com',
    });

    expect(postSpy).toHaveBeenCalledWith('/admin/refunds/ref-1/override', {
      decision: 'Approved',
      reason: 'Manager goodwill',
      actor: 'lead@store.com',
    });
    expect(result).toEqual(mockUpdated);
  });

  it('getAuditLogs passes refund_id parameter when provided', async () => {
    const mockLogs = [
      {
        id: 'log-1',
        refund_request_id: 'ref-1',
        action: 'evaluated',
        actor: 'ai_engine',
        details: {},
        timestamp: '2026-02-02',
      },
    ];

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockLogs });

    const result = await refundApi.getAuditLogs('ref-1');
    expect(getSpy).toHaveBeenCalledWith('/admin/audit-logs', {
      params: { refund_id: 'ref-1' },
    });
    expect(result).toEqual(mockLogs);
  });

  it('submitRefundRequest sends quantity and item_condition payload (covers: AC-2)', async () => {
    const payload = {
      customer_email: 'sarah.jenkins@example.com',
      order_number: 'ORD-2026-9001',
      item_id: 'item-uuid-1',
      amount: 90.0,
      reason_category: 'defective',
      customer_explanation: 'Broken hinges',
      quantity: 2,
      item_condition: 'opened_used',
    };

    const mockResponse = {
      id: 'ref-100',
      request_number: 'REF-1234567890',
      customer_id: 'cust-1',
      order_id: 'ord-1',
      amount: 90.0,
      currency: 'USD',
      reason_category: 'defective',
      customer_explanation: 'Broken hinges',
      decision: 'Approved' as const,
      confidence_score: 0.95,
      policy_checks: {
        matched_rules: ['RULE_RETURN_WINDOW'],
        citations: ['Refund Policy § 1.1'],
      },
      human_override: false,
      created_at: '2026-09-23',
      updated_at: '2026-09-23',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockResponse });

    const result = await refundApi.submitRefundRequest(payload);
    expect(postSpy).toHaveBeenCalledWith('/refunds/process', payload);
    expect(result).toEqual(mockResponse);
  });

  it('getRefundRequestDetail queries detail endpoint by ID (covers: AC-5, AC-6)', async () => {
    const mockDetail = {
      id: 'ref-detail-1',
      request_number: 'REF-ABC1234567',
      customer_id: 'cust-1',
      order_id: 'ord-1',
      amount: 45.0,
      currency: 'USD',
      reason_category: 'defective',
      customer_explanation: 'Faulty scroll wheel',
      decision: 'Approved' as const,
      status: 'approved',
      confidence_score: 0.95,
      human_override: false,
      created_at: '2026-09-23',
      updated_at: '2026-09-23',
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockDetail });

    const result = await refundApi.getRefundRequestDetail('ref-detail-1');
    expect(getSpy).toHaveBeenCalledWith('/admin/refunds/ref-detail-1');
    expect(result).toEqual(mockDetail);
  });
});
