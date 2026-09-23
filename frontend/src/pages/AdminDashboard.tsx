import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  Filter,
  RefreshCw,
  User,
} from 'lucide-react';
import { refundApi } from '../api/refunds';
import type { RefundRequest } from '../types';

export const AdminDashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedRequest, setSelectedRequest] = useState<RefundRequest | null>(null);
  const [overrideModalOpen, setOverrideModalOpen] = useState<boolean>(false);
  const [overrideDecision, setOverrideDecision] = useState<string>('Approved');
  const [overrideReason, setOverrideReason] = useState<string>('');

  const refundsQuery = useQuery({
    queryKey: ['admin-refunds', filterStatus],
    queryFn: () =>
      refundApi.listRefundRequests(filterStatus !== 'all' ? { decision: filterStatus } : {}),
  });

  const overrideMutation = useMutation({
    mutationFn: ({ id, decision, reason }: { id: string; decision: string; reason: string }) =>
      refundApi.overrideDecision(id, { decision, reason, actor: 'support_lead@store.com' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-refunds'] });
      setOverrideModalOpen(false);
      setSelectedRequest(null);
    },
  });

  const requests = refundsQuery.data || [];

  const counts = {
    total: requests.length,
    approved: requests.filter((r) => r.decision === 'Approved').length,
    denied: requests.filter((r) => r.decision === 'Denied').length,
    escalated: requests.filter((r) => r.decision === 'Escalated').length,
  };

  const handleOpenOverride = (req: RefundRequest) => {
    setSelectedRequest(req);
    setOverrideDecision(req.decision === 'Approved' ? 'Denied' : 'Approved');
    setOverrideReason('');
    setOverrideModalOpen(true);
  };

  const handleSaveOverride = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;
    overrideMutation.mutate({
      id: selectedRequest.id,
      decision: overrideDecision,
      reason: overrideReason || 'Manual manager discretion override.',
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Support Agent Refund Console
          </h1>
          <p className="text-slate-600 text-sm">
            Review AI refund evaluations, inspect audit logs, and provide human manager overrides.
          </p>
        </div>
        <button
          onClick={() => refundsQuery.refetch()}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-medium hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-4 h-4 ${refundsQuery.isFetching ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Claims
          </span>
          <div className="text-2xl font-black text-slate-900">{counts.total}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">
            Approved
          </span>
          <div className="text-2xl font-black text-emerald-700">{counts.approved}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">
            Denied
          </span>
          <div className="text-2xl font-black text-rose-700">{counts.denied}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">
            Escalations
          </span>
          <div className="text-2xl font-black text-amber-700">{counts.escalated}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-3">
        <span className="text-xs font-bold text-slate-500 uppercase flex items-center space-x-1 mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Status:</span>
        </span>
        {['all', 'Escalated', 'Approved', 'Denied'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterStatus(tab)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterStatus === tab
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Table of Claims */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500 tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Customer & Item</th>
                <th className="px-6 py-3.5">Amount</th>
                <th className="px-6 py-3.5">AI Verdict</th>
                <th className="px-6 py-3.5">Confidence</th>
                <th className="px-6 py-3.5">Override</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {requests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                    No refund requests found for this filter.
                  </td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50/70 transition">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">
                        {req.item_name || 'Item Refund'}
                      </div>
                      <div className="text-xs text-slate-500 flex items-center space-x-1">
                        <User className="w-3 h-3" />
                        <span>{req.customer?.name || req.customer_id}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      ${req.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${
                          req.decision === 'Approved'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : req.decision === 'Denied'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {req.decision === 'Approved' && <CheckCircle2 className="w-3 h-3" />}
                        {req.decision === 'Denied' && <XCircle className="w-3 h-3" />}
                        {req.decision === 'Escalated' && <AlertTriangle className="w-3 h-3" />}
                        <span>{req.decision}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {req.confidence_score ? `${(req.confidence_score * 100).toFixed(0)}%` : '95%'}
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {req.human_override ? (
                        <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                          Overridden
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenOverride(req)}
                        className="px-3 py-1 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
                      >
                        Override
                      </button>
                      <Link
                        to={`/admin/refunds/${req.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition"
                      >
                        <span>Audit</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Human Override Modal */}
      {overrideModalOpen && selectedRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Human Manager Override</h3>
            <p className="text-xs text-slate-500">
              Manually change the verdict for Claim #{selectedRequest.id.slice(0, 8)}:
            </p>

            <form onSubmit={handleSaveOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  New Decision
                </label>
                <select
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                >
                  <option value="Approved">Approved</option>
                  <option value="Denied">Denied</option>
                  <option value="Escalated">Escalated</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Override Reason
                </label>
                <textarea
                  required
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="State the justification for overriding the AI decision..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setOverrideModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-sm font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
                >
                  {overrideMutation.isPending ? 'Saving...' : 'Confirm Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
