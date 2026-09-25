import React from 'react';
import { Link } from 'react-router-dom';
import { useCustomerAuth } from '../context/CustomerAuthContext';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  ArrowRight,
  UserCheck,
  LayoutDashboard,
  Sparkles,
  Lock,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { customer, isAuthenticated: isCustomerAuthed } = useCustomerAuth();
  const { user: adminUser, isAuthenticated: isAdminAuthed } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs font-semibold mb-6 shadow-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Intelligent Automated Refund Governance</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight sm:leading-none">
          AI-Powered Support & <br className="hidden sm:block" />
          <span className="text-emerald-600">Instant Refund Decisions</span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-600 leading-relaxed">
          A full-stack refund orchestration platform featuring two-phase deterministic policy
          enforcement, multi-provider LLM decision support, and role-isolated security controls.
        </p>

        {/* CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          {isCustomerAuthed ? (
            <Link
              to="/portal"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm shadow-md shadow-emerald-600/20 hover:bg-emerald-700 transition"
            >
              <span>Welcome, {customer?.name.split(' ')[0]} — Enter Portal</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          ) : (
            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm shadow-md shadow-emerald-600/20 hover:bg-emerald-700 transition"
            >
              <UserCheck className="w-4 h-4 mr-2" />
              <span>Customer Portal Login</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          )}

          <Link
            to={isAdminAuthed ? '/admin' : '/admin/login'}
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-white border border-slate-200 text-slate-700 font-semibold text-sm hover:bg-slate-50 hover:border-slate-300 transition shadow-sm"
          >
            <LayoutDashboard className="w-4 h-4 mr-2 text-slate-500" />
            <span>{isAdminAuthed ? 'Admin Dashboard' : 'Support Staff Login'}</span>
          </Link>
        </div>

        {/* Active Session Info if any */}
        {(isCustomerAuthed || isAdminAuthed) && (
          <div className="mt-6 inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-100 text-xs text-slate-600 border border-slate-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              Active session: {isCustomerAuthed ? `Customer (${customer?.email})` : `Staff (${adminUser?.email})`}
            </span>
          </div>
        )}
      </div>

      {/* Feature Pillar Cards */}
      <div className="mt-16 sm:mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
        <div className="p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm hover:border-emerald-200 transition">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h2 className="text-base font-bold text-slate-900 mb-2">Deterministic Guardrails</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Non-negotiable post-AI policy evaluation blocks final-sale refunds, enforces the 90-day return window,
            and routes claims over $500 directly to supervisor review.
          </p>
        </div>

        <div className="p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm hover:border-emerald-200 transition">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center mb-4">
            <Sparkles className="w-5 h-5" />
          </div>
          <h2 className="text-base font-bold text-slate-900 mb-2">Multi-Provider AI Engine</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Runtime gateway supporting OpenAI, local Ollama, and Google Gemini with prompt injection
            sanitization, XML delimiter tagging, and graceful outage fallback.
          </p>
        </div>

        <div className="p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm hover:border-emerald-200 transition">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-4">
            <Lock className="w-5 h-5" />
          </div>
          <h2 className="text-base font-bold text-slate-900 mb-2">Role-Isolated Security</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Dual HTTP-only cookie transport separates customer sessions from administrative workspaces,
            allowing concurrent reviewer testing without credential collisions.
          </p>
        </div>
      </div>

      {/* Evaluator Quick Start Banner */}
      <div className="mt-12 p-6 sm:p-8 bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-transparent border border-emerald-200/80 rounded-2xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-1">
              Evaluator Quick Reference
            </div>
            <h2 className="text-lg font-bold text-slate-900">Pre-seeded Test Accounts Ready</h2>
            <p className="text-sm text-slate-600 mt-1">
              Customer credentials: <code className="px-1.5 py-0.5 bg-white rounded border border-slate-200 text-emerald-700 font-mono text-xs">sarah.jenkins@example.com</code> / <code className="px-1.5 py-0.5 bg-white rounded border border-slate-200 text-emerald-700 font-mono text-xs">customer123</code>.
              Staff credentials: <code className="px-1.5 py-0.5 bg-white rounded border border-slate-200 text-slate-700 font-mono text-xs">admin@store.com</code> / <code className="px-1.5 py-0.5 bg-white rounded border border-slate-200 text-slate-700 font-mono text-xs">admin123</code>.
            </p>
          </div>
          <Link
            to="/login"
            className="flex-shrink-0 inline-flex items-center px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition"
          >
            Go to Customer Login &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
