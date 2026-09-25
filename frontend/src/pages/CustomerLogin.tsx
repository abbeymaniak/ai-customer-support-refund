import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useCustomerAuth } from '../context/CustomerAuthContext';
import { Lock, Mail, AlertCircle, ArrowRight, UserCheck, ShieldCheck } from 'lucide-react';

const SAMPLE_CUSTOMERS = [
  { name: 'Sarah Jenkins', email: 'sarah.jenkins@example.com', badge: '18 Orders · VIP' },
  { name: 'David Miller', email: 'david.miller@example.com', badge: '4 Orders · Standard' },
  { name: 'Elena Rostova', email: 'elena.rostova@example.com', badge: '6 Orders · Frequent Returns' },
];

export const CustomerLoginPage: React.FC = () => {
  const { login, isAuthenticated, isLoading: authLoading } = useCustomerAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const returnUrl = searchParams.get('returnUrl') || '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate(returnUrl, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, returnUrl]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      navigate(returnUrl, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please try again.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectSample = (sampleEmail: string) => {
    setEmail(sampleEmail);
    setPassword('customer123');
    setErrorMessage(null);
  };

  return (
    <div className="min-h-[85vh] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 mb-4">
          <UserCheck className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Customer Portal Login</h1>
        <p className="text-sm text-slate-500 mt-1">
          Access your personal orders, view claim status, and file returns
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200/80 rounded-2xl sm:px-10">
          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200/80 flex items-start gap-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label htmlFor="customer-email" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="customer-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
                />
              </div>
            </div>

            <div>
              <label htmlFor="customer-password" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="customer-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition"
            >
              {isSubmitting ? (
                'Authenticating...'
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </>
              )}
            </button>
          </form>

          {/* Test Accounts Callout Card */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-4">
              <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-700">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Sample Test Profiles (Password: customer123)</span>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                Click any profile below to populate login fields instantly:
              </p>
              <div className="space-y-2">
                {SAMPLE_CUSTOMERS.map((sample) => (
                  <button
                    key={sample.email}
                    type="button"
                    onClick={() => handleSelectSample(sample.email)}
                    className="w-full flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/40 text-left transition group"
                  >
                    <div>
                      <div className="text-xs font-medium text-slate-900 group-hover:text-emerald-700">
                        {sample.name}
                      </div>
                      <div className="text-[11px] text-slate-500">{sample.email}</div>
                    </div>
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 group-hover:bg-emerald-100 group-hover:text-emerald-800">
                      {sample.badge}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-slate-500">
            Looking for administrative management?{' '}
            <Link to="/admin/login" className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline">
              Support Staff Login &rarr;
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
