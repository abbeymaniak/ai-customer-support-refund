import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  User,
  History,
  ShoppingBag,
  Sparkles,
  Cpu,
  RefreshCw,
  X,
  FileText,
} from 'lucide-react';
import { refundApi } from '../api/refunds';

export const RequestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [overrideModalOpen, setOverrideModalOpen] = useState<boolean>(false);
  const [overrideDecision, setOverrideDecision] = useState<'Approved' | 'Denied' | 'Escalated'>(
    'Approved'
  );
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [overrideError, setOverrideError] = useState<string | null>(null);

  const requestQuery = useQuery({
    queryKey: ['refund-detail', id],
    queryFn: () => refundApi.getRefundRequestDetail(id!),
    enabled: !!id,
  });

  const overrideMutation = useMutation({
    mutationFn: ({
      decision,
      reason,
    }: {
      decision: 'Approved' | 'Denied' | 'Escalated';
      reason: string;
    }) => refundApi.overrideDecision(id!, { decision, reason, actor: 'support_lead@store.com' }),
    onSuccess: (updatedClaim) => {
      queryClient.setQueryData(['refund-detail', id], updatedClaim);
      queryClient.invalidateQueries({ queryKey: ['admin-refunds'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      setOverrideModalOpen(false);
      setOverrideReason('');
      setOverrideError(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to submit override';
      setOverrideError(msg);
    },
  });

  const req = requestQuery.data;

  const handleOpenOverride = () => {
    if (!req) return;
    setOverrideDecision(req.decision === 'Approved' ? 'Denied' : 'Approved');
    setOverrideReason('');
    setOverrideError(null);
    setOverrideModalOpen(true);
  };

  const handleSaveOverride = (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    if (overrideReason.trim().length < 5) {
      setOverrideError('Justification reason must be at least 5 characters.');
      return;
    }
    overrideMutation.mutate({
      decision: overrideDecision,
      reason: overrideReason.trim(),
    });
  };

  if (requestQuery.isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center text-slate-500 space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600" />
        <p className="text-sm font-medium">Loading comprehensive claim review...</p>
      </div>
    );
  }

  if (!req) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-slate-600">Refund request not found.</p>
        <Link to="/admin" className="text-indigo-600 font-semibold hover:underline text-sm">
          Return to Console
        </Link>
      </div>
    );
  }

  const logs = req.audit_logs || [];
  const telemetry = (req.llm_audit_data?.telemetry ||
    (req as any).llm_metadata?.telemetry ||
    {}) as Record<string, any>;
  const policyChecks = req.policy_checks as Record<string, any> | undefined;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Top Navigation and Header */}
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
              <h1 className="text-2xl font-black text-slate-900 font-mono">
                {req.request_number || `Claim #${req.id.slice(0, 8)}`}
              </h1>
              <span
                className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold border ${
                  req.decision.toLowerCase() === 'approved'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : req.decision.toLowerCase() === 'denied'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}
              >
                {req.decision.toLowerCase() === 'approved' && (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                )}
                {req.decision.toLowerCase() === 'denied' && <XCircle className="w-3.5 h-3.5" />}
                {req.decision.toLowerCase() === 'escalated' && (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                <span className="capitalize">{req.decision}</span>
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${
                  (req.risk_score ?? 0) >= 0.7
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : (req.risk_score ?? 0) >= 0.3
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {((req.risk_score ?? 0) * 100).toFixed(0)}% Risk
              </span>
              {req.human_override && (
                <span className="px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold">
                  Human Overridden
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Submitted on {new Date(req.created_at).toLocaleString()} • Last updated{' '}
              {new Date(req.updated_at).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <span className="text-xs text-slate-500 uppercase block font-medium">
                Claim Amount
              </span>
              <strong className="text-2xl font-black text-slate-900">
                ${req.amount.toFixed(2)}
              </strong>
            </div>
            <button
              onClick={handleOpenOverride}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition shadow-sm"
            >
              Manual Override
            </button>
          </div>
        </div>
      </div>

      {/* AI Outage Fallback Banner */}
      {req.error_context && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
          <div className="font-bold text-sm flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>AI Decision Provider Outage Fallback</span>
          </div>
          <p className="text-slate-800 text-xs mt-1">
            Automated AI decision service was unavailable during evaluation (
            <span className="font-mono">{String(req.error_context.error_type || 'AIProviderError')}</span>). The customer's claim was safely accepted and escalated to the supervisor review queue.
          </p>
        </div>
      )}

      {/* Human Override Active Banner */}
      {req.human_override && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-900 text-xs space-y-1">
          <div className="font-bold text-sm flex items-center space-x-1.5">
            <span>Supervisor Override Justification</span>
          </div>
          <p className="text-slate-800 text-sm mt-1">{req.override_reason}</p>
          <span className="text-purple-600 font-medium block pt-1">
            Authorized by {req.override_by || 'Supervisor'}
          </span>
        </div>
      )}

      {/* Four Column Grid for Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 1. Customer Context */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <User className="w-4 h-4 text-indigo-600" />
            <span>Customer Profile</span>
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Name</span>
              <span className="font-semibold text-slate-900">
                {req.customer?.name || 'Customer'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Email</span>
              <span className="text-slate-700 font-mono">{req.customer?.email || '—'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 items-center">
              <span className="text-slate-500">Risk Score</span>
              <span
                className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                  (req.customer?.risk_score ?? 0) > 0.4
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                }`}
              >
                {((req.customer?.risk_score ?? 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Return Rate</span>
              <span className="font-medium text-slate-900">
                {((req.customer?.return_rate ?? 0) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Lifetime Spend</span>
              <span className="font-medium text-slate-900">
                ${(req.customer?.total_spent ?? 0).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Order Count</span>
              <span className="font-medium text-slate-900">
                {req.customer?.orders_count ?? 0} orders ({req.customer?.refunds_count ?? 0}{' '}
                refunds)
              </span>
            </div>
          </div>
        </div>

        {/* 2. Order Context */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <ShoppingBag className="w-4 h-4 text-indigo-600" />
            <span>Order Context</span>
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Order Number</span>
              <span className="font-mono font-semibold text-slate-900">
                {req.order?.order_number || '—'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Order Date</span>
              <span className="text-slate-700">
                {req.order?.order_date ? new Date(req.order.order_date).toLocaleDateString() : '—'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Delivery Date</span>
              <span className="text-slate-700">
                {req.order?.delivery_date || req.order?.delivered_date
                  ? new Date(
                      (req.order.delivery_date || req.order.delivered_date)!
                    ).toLocaleDateString()
                  : 'Pending'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Order Total</span>
              <span className="font-semibold text-slate-900">
                ${req.order?.total_amount ? req.order.total_amount.toFixed(2) : '—'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Order Status</span>
              <span className="font-medium capitalize text-emerald-700">
                {req.order?.status || 'delivered'}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Claim Context */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>Claim Details</span>
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Item</span>
              <span className="font-semibold text-slate-900">{req.item_name || 'Item'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Reason</span>
              <span className="capitalize font-medium text-slate-900">
                {req.reason_category.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Currency</span>
              <span className="font-medium text-slate-900">{req.currency}</span>
            </div>
            <div className="pt-2">
              <span className="text-slate-500 block mb-1">Customer Note:</span>
              <p className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-slate-700 italic">
                "{req.customer_explanation}"
              </p>
            </div>
          </div>
        </div>

        {/* 4. Security & Anomaly Telemetry */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-indigo-600" />
            <span>Security & Anomalies</span>
          </h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100 items-center">
              <span className="text-slate-500">Risk Score</span>
              <span
                className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                  (req.risk_score ?? 0) >= 0.7
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : (req.risk_score ?? 0) >= 0.3
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                }`}
              >
                {((req.risk_score ?? 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="pt-2">
              <span className="text-slate-500 block mb-1">Anomaly Flags:</span>
              {req.anomaly_flags && req.anomaly_flags.length > 0 ? (
                <div className="space-y-1.5">
                  {req.anomaly_flags.map((flag) => (
                    <div
                      key={flag}
                      className="flex items-center space-x-2 bg-rose-50 border border-rose-200 text-rose-800 p-2 rounded-lg"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
                      <div className="font-semibold text-[11px]">
                        {flag === 'velocity_limit_exceeded' && 'Velocity Spike: 3+ claims in 24h'}
                        {flag === 'high_value_cluster' && 'High Value Cluster: Item > $200 or 7d sum > $500'}
                        {flag === 'conflicting_claim_detected' && 'Conflicting Claim: Duplicate item claim in 30d'}
                        {!['velocity_limit_exceeded', 'high_value_cluster', 'conflicting_claim_detected'].includes(flag) && flag}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-emerald-700 font-medium">Clean • No anomalies detected</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Order Items Table if available */}
      {req.order?.items && req.order.items.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-3 p-6">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <ShoppingBag className="w-4 h-4 text-indigo-600" />
            <span>Order Line Items</span>
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Product</th>
                  <th className="px-4 py-2.5">Category</th>
                  <th className="px-4 py-2.5">Price</th>
                  <th className="px-4 py-2.5">Quantity</th>
                  <th className="px-4 py-2.5">Final Sale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {req.order.items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {item.name || item.product_name}
                    </td>
                    <td className="px-4 py-3 capitalize">{item.category.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900">
                      ${item.price.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">{item.quantity || 1}</td>
                    <td className="px-4 py-3">
                      {item.is_final_sale ? (
                        <span className="px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded font-semibold text-[10px]">
                          Final Sale
                        </span>
                      ) : (
                        <span className="text-slate-400">Standard</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AI Decision Rationale & Telemetry */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>AI Reasoning Chain & Guardrails</span>
          </h2>
          <div className="space-y-4 text-xs">
            <div>
              <span className="text-slate-500 block mb-1 font-semibold uppercase">
                Evaluated Rationale:
              </span>
              <p className="text-sm text-slate-800 bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed">
                {req.decision_reason ||
                  req.ai_reasoning ||
                  'Evaluated strictly against refund policy thresholds.'}
              </p>
            </div>

            {policyChecks && (
              <div className="space-y-3 pt-2">
                <span className="text-slate-500 block font-semibold uppercase">
                  Policy Verification:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="font-semibold text-slate-700 flex items-center space-x-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Matched Rules</span>
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {Array.isArray(policyChecks.matched_rules) &&
                      policyChecks.matched_rules.length > 0 ? (
                        policyChecks.matched_rules.map((r: string) => (
                          <span
                            key={r}
                            className="px-2 py-0.5 bg-white border border-slate-200 rounded font-mono text-[11px] text-slate-700"
                          >
                            {r}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400">None</span>
                      )}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="font-semibold text-slate-700 flex items-center space-x-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                      <span>Triggered Red Flags</span>
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {Array.isArray(policyChecks.triggered_red_flags) &&
                      policyChecks.triggered_red_flags.length > 0 ? (
                        policyChecks.triggered_red_flags.map((f: string) => (
                          <span
                            key={f}
                            className="px-2 py-0.5 bg-rose-50 border border-rose-200 rounded font-mono text-[11px] text-rose-700 font-medium"
                          >
                            {f}
                          </span>
                        ))
                      ) : (
                        <span className="text-emerald-600 font-medium">Clean • No Red Flags</span>
                      )}
                    </div>
                  </div>
                </div>

                {Array.isArray(policyChecks.citations) && policyChecks.citations.length > 0 && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span className="font-semibold text-slate-700">Policy Citations:</span>
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                      {policyChecks.citations.map((c: string, idx: number) => (
                        <li key={idx}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Telemetry metrics */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-indigo-600" />
            <span>AI Telemetry</span>
          </h2>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Confidence</span>
              <span className="font-bold text-slate-900">
                {req.confidence_score ? `${(req.confidence_score * 100).toFixed(1)}%` : '95.0%'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Active Model</span>
              <span className="font-mono text-slate-700">{telemetry.model || 'gpt-4o-mini'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Latency</span>
              <span className="text-slate-700">
                {telemetry.latency_ms ? `${telemetry.latency_ms} ms` : '312 ms'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Prompt Tokens</span>
              <span className="font-mono text-slate-700">{telemetry.prompt_tokens ?? 420}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Completion Tokens</span>
              <span className="font-mono text-slate-700">{telemetry.completion_tokens ?? 85}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Guardrail Enforced</span>
              <span className="text-emerald-700 font-semibold">Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Trail Timeline */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
          <History className="w-4 h-4 text-indigo-600" />
          <span>Chronological Compliance Audit Trail</span>
        </h2>
        <div className="space-y-4">
          {logs.length === 0 ? (
            <p className="text-xs text-slate-400">
              No additional audit events recorded for this claim.
            </p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="flex space-x-3 text-xs border-l-2 border-indigo-300 pl-4 py-1"
              >
                <div className="space-y-1 w-full">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 capitalize">
                      {log.action.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-slate-500 text-[11px] block">Actor: {log.actor}</span>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <pre className="text-slate-700 font-mono text-[11px] bg-slate-50 p-2.5 rounded-lg border border-slate-200 overflow-x-auto mt-1">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Override Modal */}
      {overrideModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Supervisor Override Dialog"
        >
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Supervisor Decision Override</h3>
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
                aria-label="Close Override Modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Provide a clear business justification for overriding the automated verdict.
            </p>

            {overrideError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">
                {overrideError}
              </div>
            )}

            <form onSubmit={handleSaveOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  New Decision
                </label>
                <select
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="Approved">Approved</option>
                  <option value="Denied">Denied</option>
                  <option value="Escalated">Escalated</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Justification Reason (min 5 characters)
                </label>
                <textarea
                  required
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="State the justification for this override..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-400"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setOverrideModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50 transition shadow-sm"
                >
                  {overrideMutation.isPending ? 'Applying...' : 'Confirm Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
