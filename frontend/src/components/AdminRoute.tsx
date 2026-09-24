import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2, ShieldAlert } from 'lucide-react';

interface AdminRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'agent';
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children, requiredRole }) => {
  const { user, isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <p className="text-sm font-medium text-slate-500">Verifying administrative session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    const returnUrl = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/admin/login?returnUrl=${returnUrl}`} replace />;
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-8 bg-white border border-rose-200 rounded-2xl shadow-sm text-center">
        <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Access Restricted</h2>
        <p className="text-sm text-slate-600 mb-6">
          This area requires the <strong>{requiredRole}</strong> role. Your current account (
          {user?.email}) is assigned the <strong>{user?.role}</strong> role.
        </p>
        <a
          href="/admin"
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition"
        >
          Return to Dashboard
        </a>
      </div>
    );
  }

  return <>{children}</>;
};
