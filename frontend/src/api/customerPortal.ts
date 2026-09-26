import { apiClient } from './client';
import type { CustomerRefundClaimPayload, Order, RefundRequest } from '../types';

export const customerPortalApi = {
  getMyOrders: async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>('/customer/orders');
    return response.data;
  },

  submitRefund: async (payload: CustomerRefundClaimPayload): Promise<RefundRequest> => {
    const response = await apiClient.post<RefundRequest>('/customer/refunds', payload);
    return response.data;
  },
};
