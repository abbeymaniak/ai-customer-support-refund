import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  User,
  History,
} from 'lucide-react';
import { refundApi } from '../api/refunds';

export const RequestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const requestQuery = useQuery({
    queryKey: ['refund-detail', id],
    queryFn: () => refundApi.getRefundRequestDetail(id!),
    enabled: !!id,
  });

  const auditLogsQuery = useQuery({
    queryKey: ['audit-logs', id],
    queryFn: () => refundApi.getAuditLogs(id!),
    enabled: !!id,
  });

  const req = requestQuery.data;
  const logs = auditLogsQuery.data || [];

  if (requestQuery.isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center text-slate-500">
        Loading audit details...
      </div>
    );
  }

  if (!req) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-slate-600">Refund request not found.</p>
        <Link to="/admin" className="text-indigo-600 font-semibold hover:underline">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Back button and Header */}
      <div className="space-y-4">
        <Link
          to="/admin"
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Console</span>
        </Link>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-6">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-black text-slate-900">Claim #{req.id.slice(0, 8)}</h1>
              <span
                className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold border ${
                  req.decision === 'Approved'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : req.decision === 'Denied'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}
              >
                {req.decision === 'Approved' && <CheckCircle2 className="w-3.5 h-3.5" />}
                {req.decision === 'Denied' && <XCircle className="w-3.5 h-3.5" />}
                {req.decision === 'Escalated' && <AlertTriangle className="w-3.5 h-3.5" />}
                <span>{req.decision}</span>
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Submitted on {new Date(req.created_at).toLocaleString()}
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-500 uppercase block">Claim Amount</span>
            <strong className="text-2xl font-black text-slate-900">${req.amount.toFixed(2)}</strong>
          </div>
        </div>
      </div>

      {/* Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Customer & Claim */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <User className="w-4 h-4 text-indigo-600" />
            <span>Customer & Item Context</span>
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Customer</span>
              <span className="font-semibold text-slate-900">
                {req.customer?.name || 'Customer'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Email</span>
              <span className="text-slate-700">{req.customer?.email}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Customer Risk Score</span>
              <span className="font-bold text-slate-900">
                {((req.customer?.risk_score || 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Item</span>
              <span className="font-semibold text-slate-900">
                {req.item_name || 'Standard Item'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Claim Reason</span>
              <span className="capitalize text-slate-900 font-medium">
                {req.reason_category.replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* AI Decision Rationale */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-indigo-600" />
            <span>AI Reasoning & Rules</span>
          </h2>
          <div className="space-y-3">
            <div>
              <span className="text-xs font-semibold text-slate-500 block mb-1">
                Generated Explanation:
              </span>
              <p className="text-sm text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-200">
                {req.decision_reason ||
                  'Evaluated strictly against refund policy thresholds and order history.'}
              </p>
            </div>
            {req.confidence_score && (
              <div className="flex justify-between items-center text-xs pt-1">
                <span className="text-slate-500">Confidence Metric:</span>
                <span className="font-bold text-slate-900">
                  {(req.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {req.human_override && (
              <div className="p-3 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs space-y-1">
                <strong className="block font-bold">Manual Manager Override Applied</strong>
                <p>{req.override_reason}</p>
                <span className="text-purple-600 block">By: {req.override_by}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Audit Trail Timeline */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
          <History className="w-4 h-4 text-indigo-600" />
          <span>Audit Log Trail</span>
        </h2>
        <div className="space-y-4">
          {logs.length === 0 ? (
            <p className="text-xs text-slate-400">No additional audit events recorded.</p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="flex space-x-3 text-xs border-l-2 border-indigo-200 pl-4 py-1"
              >
                <div>
                  <span className="font-bold text-slate-900 capitalize">
                    {log.action.replace(/_/g, ' ')}
                  </span>
                  <span className="text-slate-500 ml-2">by {log.actor}</span>
                  <div className="text-slate-600 mt-1 font-mono text-[11px] bg-slate-50 p-2 rounded border">
                    {JSON.stringify(log.details)}
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-1">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
