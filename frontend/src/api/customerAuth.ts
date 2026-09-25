import { apiClient } from './client';
import type { AuthStatusResponse, CustomerLoginCredentials, CustomerUser } from '../types';

export const customerAuthApi = {
  login: async (credentials: CustomerLoginCredentials): Promise<CustomerUser> => {
    const response = await apiClient.post<CustomerUser>('/customer/auth/login', credentials);
    return response.data;
  },

  refresh: async (): Promise<AuthStatusResponse> => {
    const response = await apiClient.post<AuthStatusResponse>('/customer/auth/refresh');
    return response.data;
  },

  logout: async (): Promise<AuthStatusResponse> => {
    const response = await apiClient.post<AuthStatusResponse>('/customer/auth/logout');
    return response.data;
  },

  getMe: async (): Promise<CustomerUser> => {
    const response = await apiClient.get<CustomerUser>('/customer/auth/me');
    return response.data;
  },
};
