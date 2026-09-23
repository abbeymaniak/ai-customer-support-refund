import { apiClient } from './client';
import type { Customer, Order, RefundRequest, RefundSubmissionPayload, AuditLog } from '../types';

export const refundApi = {
  // Customer & Order Lookups
  async getCustomerByEmail(email: string): Promise<Customer> {
    const { data } = await apiClient.get<Customer>(
      `/customers/lookup?email=${encodeURIComponent(email)}`
    );
    return data;
  },

  async getCustomerOrders(customerId: string): Promise<Order[]> {
    const { data } = await apiClient.get<Order[]>(`/customers/${customerId}/orders`);
    return data;
  },

  // Refund Processing
  async submitRefundRequest(payload: RefundSubmissionPayload): Promise<RefundRequest> {
    const { data } = await apiClient.post<RefundRequest>('/refunds/process', payload);
    return data;
  },

  // Admin & Audit
  async listRefundRequests(params?: {
    decision?: string;
    limit?: number;
    offset?: number;
  }): Promise<RefundRequest[]> {
    const { data } = await apiClient.get<RefundRequest[]>('/admin/refunds', { params });
    return data;
  },

  async getRefundRequestDetail(id: string): Promise<RefundRequest> {
    const { data } = await apiClient.get<RefundRequest>(`/admin/refunds/${id}`);
    return data;
  },

  async overrideDecision(
    id: string,
    payload: { decision: string; reason: string; actor: string }
  ): Promise<RefundRequest> {
    const { data } = await apiClient.post<RefundRequest>(`/admin/refunds/${id}/override`, payload);
    return data;
  },

  async getAuditLogs(refundRequestId?: string): Promise<AuditLog[]> {
    const { data } = await apiClient.get<AuditLog[]>('/admin/audit-logs', {
      params: refundRequestId ? { refund_id: refundRequestId } : {},
    });
    return data;
  },
};
