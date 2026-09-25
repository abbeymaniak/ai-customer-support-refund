import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { CustomerAuthProvider } from './context/CustomerAuthContext';
import { AdminRoute } from './components/AdminRoute';
import { CustomerRoute } from './components/CustomerRoute';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { RefundRequestPage } from './pages/RefundRequest';
import { AdminDashboardPage } from './pages/AdminDashboard';
import { RequestDetailPage } from './pages/RequestDetail';
import { AdminSettingsPage } from './pages/AdminSettings';
import { LoginPage } from './pages/Login';
import { CustomerLoginPage } from './pages/CustomerLogin';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30, // 30 seconds
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <CustomerAuthProvider>
            <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
              <Navbar />
              <main className="flex-1 pb-16">
                <Routes>
                  {/* Public Landing Page */}
                  <Route path="/" element={<LandingPage />} />

                  {/* Customer Authentication */}
                  <Route path="/login" element={<CustomerLoginPage />} />

                  {/* Customer Portal (Protected Route) */}
                  <Route
                    path="/portal"
                    element={
                      <CustomerRoute>
                        <RefundRequestPage />
                      </CustomerRoute>
                    }
                  />

                  {/* Admin Authentication */}
                  <Route path="/admin/login" element={<LoginPage />} />

                  {/* Protected Administrative Routes */}
                  <Route
                    path="/admin"
                    element={
                      <AdminRoute>
                        <AdminDashboardPage />
                      </AdminRoute>
                    }
                  />
                  <Route
                    path="/admin/refunds/:id"
                    element={
                      <AdminRoute>
                        <RequestDetailPage />
                      </AdminRoute>
                    }
                  />
                  <Route
                    path="/admin/settings"
                    element={
                      <AdminRoute requiredRole="admin">
                        <AdminSettingsPage />
                      </AdminRoute>
                    }
                  />

                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>
              <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
                AI Customer Support Refund System &bull; Production Architecture Challenge &bull; 2026
              </footer>
            </div>
          </CustomerAuthProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
