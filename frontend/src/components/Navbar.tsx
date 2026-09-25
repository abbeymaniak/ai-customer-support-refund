import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, RefreshCw, Settings, LogOut, LogIn, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCustomerAuth } from '../context/CustomerAuthContext';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated: isAdminAuthed, logout: adminLogout } = useAuth();
  const { customer, isAuthenticated: isCustomerAuthed, logout: customerLogout } = useCustomerAuth();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleAdminLogout = async () => {
    await adminLogout();
    navigate('/admin/login');
  };

  const handleCustomerLogout = async () => {
    await customerLogout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-100 group-hover:scale-105 transition-transform duration-200">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">AutoRefund</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                AI Engine
              </span>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <Link
              to={isCustomerAuthed ? '/portal' : '/login'}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/portal') || isActive('/login')
                  ? 'bg-emerald-50 text-emerald-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <RefreshCw className="w-4 h-4" />
              <span>Customer Portal</span>
            </Link>

            <Link
              to="/admin"
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/admin' || location.pathname.startsWith('/admin/refunds')
                  ? 'bg-emerald-50 text-emerald-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Admin Dashboard</span>
            </Link>

            {(!user || user.role === 'admin') && (
              <Link
                to="/admin/settings"
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/admin/settings')
                    ? 'bg-emerald-50 text-emerald-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>AI Settings</span>
              </Link>
            )}

            {/* Auth Profile / Actions */}
            <div className="pl-2 ml-1 border-l border-slate-200 flex items-center space-x-2">
              {/* Customer Session Display */}
              {isCustomerAuthed && customer && (
                <div className="flex items-center space-x-2">
                  <div className="hidden md:flex flex-col items-end">
                    <span className="text-xs font-medium text-slate-800 leading-tight">
                      {customer.name}
                    </span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Customer
                    </span>
                  </div>
                  <button
                    onClick={handleCustomerLogout}
                    title="Log Out of Customer Account"
                    aria-label="Log Out of Customer Account"
                    className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Admin Session Display */}
              {isAdminAuthed && user && (
                <div className="flex items-center space-x-2">
                  <div className="hidden md:flex flex-col items-end">
                    <span className="text-xs font-medium text-slate-800 leading-tight">
                      {user.name}
                    </span>
                    <span
                      className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        user.role === 'admin'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      {user.role}
                    </span>
                  </div>
                  <button
                    onClick={handleAdminLogout}
                    title="Log Out of Admin Account"
                    aria-label="Log Out of Admin Account"
                    className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Unauthenticated CTAs */}
              {!isCustomerAuthed && !isAdminAuthed && (
                <div className="flex items-center space-x-1.5">
                  <Link
                    to="/login"
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-semibold shadow-sm transition-colors"
                  >
                    <UserCheck className="w-3.5 h-3.5" />
                    <span>Customer Login</span>
                  </Link>
                  <Link
                    to="/admin/login"
                    className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 text-xs font-medium transition-colors"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Staff Login</span>
                  </Link>
                </div>
              )}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};
