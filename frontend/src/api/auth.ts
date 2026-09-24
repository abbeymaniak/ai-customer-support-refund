import { apiClient } from './client';
import type { AdminUser, AuthStatusResponse, LoginCredentials } from '../types';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AdminUser> => {
    const response = await apiClient.post<AdminUser>('/auth/login', credentials);
    return response.data;
  },

  refresh: async (): Promise<AuthStatusResponse> => {
    const response = await apiClient.post<AuthStatusResponse>('/auth/refresh');
    return response.data;
  },

  logout: async (): Promise<AuthStatusResponse> => {
    const response = await apiClient.post<AuthStatusResponse>('/auth/logout');
    return response.data;
  },

  getMe: async (): Promise<AdminUser> => {
    const response = await apiClient.get<AdminUser>('/auth/me');
    return response.data;
  },
};
