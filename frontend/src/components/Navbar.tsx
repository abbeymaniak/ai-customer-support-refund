import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  LayoutDashboard,
  Settings,
  LogOut,
  LogIn,
  UserCheck,
  FileText,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCustomerAuth } from '../context/CustomerAuthContext';

export const Navbar: React.FC = () => {
  const location = (() => {
    try {
      return useLocation();
    } catch {
      return null;
    }
  })();
  const navigate = (() => {
    try {
      return useNavigate();
    } catch {
      return null;
    }
  })();
  const {
    user,
    isAuthenticated: isAdminAuthed,
    logout: adminLogout,
    isLoading: isAdminLoading,
  } = useAuth();
  const {
    customer,
    isAuthenticated: isCustomerAuthed,
    logout: customerLogout,
    isLoading: isCustomerLoading,
  } = useCustomerAuth();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileNavOpen(false);
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);

  const isLoading = isAdminLoading || isCustomerLoading;
  const isActive = (path: string) => location?.pathname === path;
  const isStaffActive = (path: string) => location?.pathname === path || location?.pathname.startsWith(`${path}/`);

  const handleAdminLogout = async () => {
    if (!navigate) {
      return;
    }
    await adminLogout();
    navigate('/admin/login');
  };

  const handleCustomerLogout = async () => {
    if (!navigate) {
      return;
    }
    await customerLogout();
    navigate('/');
  };

  const desktopNav = (
    <nav className="hidden md:flex items-center space-x-1 sm:space-x-2">
      {isCustomerAuthed && customer && (
        <>
          <Link
            to="/portal"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive('/portal')
                ? 'bg-emerald-50 text-emerald-700 font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Customer Portal</span>
          </Link>
          <Link
            to="/portal?tab=claims"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              location?.pathname === '/portal' && location.search.includes('tab=claims')
                ? 'bg-emerald-50 text-emerald-700 font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>My Claims</span>
          </Link>
        </>
      )}

      {isAdminAuthed && user && (
        <>
          <Link
            to="/admin"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              isStaffActive('/admin')
                ? 'bg-emerald-50 text-emerald-700 font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Admin Dashboard</span>
          </Link>

          {user.role === 'admin' && (
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
        </>
      )}

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
    </nav>
  );

  const mobileNav = (
    <nav className={`${mobileNavOpen ? 'block' : 'hidden'} md:hidden border-t border-slate-200 bg-white px-4 py-3`}>
      {isCustomerAuthed && customer && (
        <div className="space-y-2">
          <Link to="/portal" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Customer Portal
          </Link>
          <Link to="/portal?tab=claims" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            My Claims
          </Link>
        </div>
      )}

      {isAdminAuthed && user && (
        <div className="space-y-2 mt-2 pt-2 border-t border-slate-200">
          <Link to="/admin" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Admin Dashboard
          </Link>
          {user.role === 'admin' && (
            <Link to="/admin/settings" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
              AI Settings
            </Link>
          )}
        </div>
      )}

      {!isCustomerAuthed && !isAdminAuthed && (
        <div className="space-y-2">
          <Link to="/login" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Customer Login
          </Link>
          <Link to="/admin/login" onClick={() => setMobileNavOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Staff Login
          </Link>
        </div>
      )}
    </nav>
  );

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
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

          {isLoading ? null : (
            <>
              {desktopNav}
              <div className="flex items-center space-x-2 md:pl-2 md:ml-1 md:border-l md:border-slate-200">
                {isCustomerAuthed && customer && (
                  <div className="hidden md:flex items-center space-x-2">
                    <div className="flex flex-col items-end">
                      <span className="text-xs font-medium text-slate-800 leading-tight">{customer.name}</span>
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

                {isAdminAuthed && user && (
                  <div className="hidden md:flex items-center space-x-2">
                    <div className="flex flex-col items-end">
                      <span className="text-xs font-medium text-slate-800 leading-tight">{user.name}</span>
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

                {!isCustomerAuthed && !isAdminAuthed && (
                  <div className="hidden md:flex items-center space-x-1.5">
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

                <button
                  type="button"
                  aria-label={mobileNavOpen ? 'Close navigation' : 'Open navigation'}
                  aria-expanded={mobileNavOpen}
                  className="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-slate-700 hover:bg-slate-100 transition-colors"
                  onClick={() => setMobileNavOpen((open) => !open)}
                >
                  {mobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </button>
              </div>
            </>
          )}
        </div>
        {isLoading ? null : mobileNav}
      </div>
    </header>
  );
};
