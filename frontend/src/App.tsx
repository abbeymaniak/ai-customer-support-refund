import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { RefundRequestPage } from './pages/RefundRequest';
import { AdminDashboardPage } from './pages/AdminDashboard';
import { RequestDetailPage } from './pages/RequestDetail';
import { AdminSettingsPage } from './pages/AdminSettings';

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
        <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
          <Navbar />
          <main className="flex-1 pb-16">
            <Routes>
              <Route path="/" element={<RefundRequestPage />} />
              <Route path="/admin" element={<AdminDashboardPage />} />
              <Route path="/admin/refunds/:id" element={<RequestDetailPage />} />
              <Route path="/admin/settings" element={<AdminSettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
            AI Customer Support Refund System &bull; Production Architecture Challenge &bull; 2026
          </footer>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
