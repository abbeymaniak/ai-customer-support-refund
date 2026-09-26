import { apiClient } from './client';
import type { CustomerRefundClaimPayload, CustomerRefundHistoryItem, Order, RefundRequest } from '../types';

export const customerPortalApi = {
  getMyOrders: async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>('/customer/orders');
    return response.data;
  },

  getMyRefunds: async (): Promise<CustomerRefundHistoryItem[]> => {
    const response = await apiClient.get<CustomerRefundHistoryItem[]>('/customer/refunds');
    return response.data;
  },

  submitRefund: async (payload: CustomerRefundClaimPayload): Promise<RefundRequest> => {
    const response = await apiClient.post<RefundRequest>('/customer/refunds', payload);
    return response.data;
  },
};
