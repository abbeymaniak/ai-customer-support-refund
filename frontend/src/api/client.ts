import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Avoid infinite loop if refresh fails or if login/refresh itself 401s
    const isAuthPath =
      originalRequest?.url?.includes('/auth/login') ||
      originalRequest?.url?.includes('/auth/refresh');

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthPath) {
      originalRequest._retry = true;
      try {
        await apiClient.post('/auth/refresh');
        return apiClient(originalRequest);
      } catch (refreshErr) {
        if (typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')) {
          if (!window.location.pathname.includes('/admin/login')) {
            window.location.href = `/admin/login?returnUrl=${encodeURIComponent(
              window.location.pathname
            )}`;
          }
        }
        return Promise.reject(refreshErr);
      }
    }

    const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);
